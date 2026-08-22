"""Shared helpers for building & running Google ADK agents.

Uses google-adk 2.7.1+ where the model class is ``Gemini`` (not ``GoogleLlm``).
Wraps calls with automatic model fallback (if a model hits 429/quota we try
the next in the queue), exponential backoff, and JSON extraction.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from typing import Type, TypeVar

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini  # ADK 2.7.1 renamed it
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from pydantic import BaseModel, ValidationError

from config import settings

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)

# Track per-model cooldowns so we don't hammer a model that just 429'd us.
_model_cooldowns: dict[str, float] = {}


def _make_model(model_name: str):
    """Build an ADK Gemini model, choosing Vertex on Cloud, API key locally."""
    if settings.is_cloud and settings.google_cloud_project:
        return Gemini(model=model_name)
    return Gemini(model=model_name, api_key=settings.gemini_api_key)


_TEMPLATE_VAR_RE = re.compile(r"(?<!\{)\{([a-zA-Z_][a-zA-Z0-9_.]*)\}(?!\})")


def _escape_instruction(inst: str) -> str:
    """Double any single {var} braces so ADK's instruction templating treats them as literals.

    ADK (google-adk>=2.7) treats ``{word}`` inside an agent's instruction as a session-state
    variable reference and raises KeyError if the variable doesn't exist. We don't use
    templating, so escape all stray single braces by doubling them (Jinja2 convention —
    ``{{`` renders as a literal ``{``)."""
    return _TEMPLATE_VAR_RE.sub(lambda m: "{{" + m.group(1) + "}}", inst)


def make_agent(name: str, instruction: str, output_key: str | None = None,
               model_override: str | None = None) -> LlmAgent:
    safe_instruction = _escape_instruction(instruction)
    return LlmAgent(
        name=name,
        model=_make_model(model_override or settings.gemini_model),
        instruction=safe_instruction,
        output_key=output_key or f"{name}_output",
    )


def _is_quota_or_overload(err: Exception) -> tuple[bool, float | None]:
    """Detect 429/quota/overload errors and return suggested retry delay."""
    msg = str(err)
    # 429 Resource Exhausted (free tier daily cap OR per-minute RPM)
    m = re.search(r"retry in ([\d.]+)s", msg)
    if m:
        return True, float(m.group(1)) + 1.0
    if "429" in msg or "RESOURCE_EXHAUSTED" in msg or "quota" in msg.lower():
        return True, 20.0
    # 503 overloaded
    if "503" in msg or "UNAVAILABLE" in msg or "high demand" in msg.lower():
        return True, 15.0
    # ADK's wrapped exception
    if "_ResourceExhaustedError" in type(err).__name__:
        return True, 20.0
    return False, None


def _run_once_with_model(agent: LlmAgent, user_prompt: str, model_name: str) -> str:
    """Execute one agent invocation synchronously using a specific model."""
    # Swap model on the agent
    agent.model = _make_model(model_name)

    # Ensure API key is in env for ADK
    if settings.gemini_api_key and not os.environ.get("GEMINI_API_KEY"):
        os.environ["GEMINI_API_KEY"] = settings.gemini_api_key

    session_service = InMemorySessionService()
    runner = Runner(app_name="exam_mitra", agent=agent, session_service=session_service)

    async def _run():
        session = await session_service.create_session(app_name="exam_mitra", user_id="pipeline")
        msg = types.Content(parts=[types.Part(text=user_prompt)], role="user")
        final = []
        async for event in runner.run_async(
            user_id="pipeline", session_id=session.id, new_message=msg
        ):
            if event.is_final_response() and event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        final.append(part.text)
        return "\n".join(final).strip()

    return asyncio.run(_run())


def run_agent_text(agent: LlmAgent, user_prompt: str, max_retries: int = 8) -> str:
    """Run agent with retries, exponential backoff, and model fallback."""
    models = settings.model_fallback_list
    last_err = None

    # We try all models in round-robin, with retries within each model
    attempt = 0
    while attempt < max_retries:
        for model_name in models:
            # Skip model if it's on cooldown
            cd = _model_cooldowns.get(model_name, 0)
            if cd > time.time():
                continue
            try:
                attempt += 1
                logger.debug(f"Agent '{agent.name}' attempt {attempt} using {model_name}")
                result = _run_once_with_model(agent, user_prompt, model_name)
                return result
            except Exception as e:
                last_err = e
                is_quota, delay = _is_quota_or_overload(e)
                if is_quota:
                    # Put this model on cooldown
                    _model_cooldowns[model_name] = time.time() + (delay or 30.0)
                    logger.warning(
                        f"Agent '{agent.name}' hit rate-limit/overload on {model_name} "
                        f"(attempt {attempt}/{max_retries}), switching model. "
                        f"Msg: {str(e)[:120]}"
                    )
                    continue
                # Non-quota error: retry same model with backoff
                delay = min(2 ** attempt * 3, 60)
                logger.warning(
                    f"Agent '{agent.name}' error on {model_name} (attempt {attempt}/{max_retries}), "
                    f"retrying in {delay}s: {str(e)[:200]}"
                )
                time.sleep(delay)
        # If we got here, all models were either on cooldown or failed
        # Wait for the shortest cooldown and try again
        active_cds = [t - time.time() for t in _model_cooldowns.values() if t > time.time()]
        if active_cds:
            wait = min(active_cds) + 1
            logger.info(f"All models on cooldown; waiting {wait:.0f}s for one to free up")
            time.sleep(min(wait, 60))
        else:
            time.sleep(5)

    raise RuntimeError(
        f"Agent '{agent.name}' failed after {max_retries} attempts across {len(models)} models. "
        f"Last error: {last_err}"
    )


def _strip_json(text: str) -> str:
    """Extract JSON object from model output, tolerating markdown fences/prose."""
    text = text.strip()
    # Remove ```json ... ``` fences
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        while lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    # Find first { and last }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        text = text[start : end + 1]
    return text


def run_agent_json(agent: LlmAgent, user_prompt: str, schema: Type[T]) -> T:
    """Run an agent and parse its output into a Pydantic-validated JSON object."""
    last_err = None
    extra = ""
    for attempt in range(3):
        raw = run_agent_text(
            agent,
            user_prompt + extra + "\n\nReturn ONLY a valid JSON object. No markdown fences, no commentary.",
        )
        try:
            data = json.loads(_strip_json(raw))
            return schema.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as e:
            last_err = e
            logger.warning(
                f"Agent '{agent.name}' JSON parse/validation failed (attempt {attempt+1}/3): "
                f"{e}. Raw preview: {raw[:400]}"
            )
            extra = (
                "\n\nPREVIOUS ATTEMPT FAILED TO PRODUCE VALID JSON. "
                "Output ONLY the JSON object. No backticks, no explanation text, "
                "no trailing commas, no comments. Options MUST be an ARRAY of "
                '{"label":"A","text":"..."}, NOT a dict.'
            )
            time.sleep(2 ** attempt * 2)
    raise RuntimeError(
        f"Agent '{agent.name}' failed to produce valid JSON after 3 attempts: {last_err}"
    )
