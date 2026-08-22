"""LLM client abstraction.

Uses google-genai SDK (required by the hackathon). On Cloud Run we route
through Vertex AI with the service account's credentials; locally we use
the developer's Gemini API key from aistudio.google.com.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Type, TypeVar

import google.genai as genai
from google.genai import types
from pydantic import BaseModel, ValidationError

from config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# Lazy-initialized client
_client: genai.Client | None = None


def get_client() -> genai.Client:
    global _client
    if _client is not None:
        return _client
    if settings.is_cloud and settings.google_cloud_project:
        _client = genai.Client(
            vertexai=True,
            project=settings.google_cloud_project,
            location=settings.google_cloud_region,
        )
    else:
        if not settings.gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Get one free from https://aistudio.google.com/apikey"
            )
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


# ---- System prompts ----

BASE_SYSTEM_INSTRUCTION = """You are Exam Mitra, an expert academic study planner built for Indian students preparing for competitive exams (JEE, NEET, UPSC, SSC, GATE, banking, etc.).
You are part of an autonomous agent pipeline. Always output structured, detailed, accurate content.
- Write in clear, simple language.
- Prioritize NCERT-aligned, exam-relevant content (avoid tangents).
- Be concrete: include actual chapter names, formulas, and PYQ context where relevant.
- If the user's request is in Hindi or Hinglish, respond in Hinglish (Hindi written in Roman script).
- Never hallucinate resources you don't know about; if a resource search is needed, leave it for the resource-finder step.
- All outputs must be valid JSON matching the schema provided.
"""


def structured_generate(
    *,
    prompt: str,
    schema: Type[T],
    model: str | None = None,
    temperature: float = 0.3,
    system_instruction: str = BASE_SYSTEM_INSTRUCTION,
) -> T:
    """Call Gemini and parse the response into a Pydantic model.

    Uses Gemini's structured-outputs / JSON-mode to guarantee shape.
    Falls back to manual JSON parsing if needed.
    """
    client = get_client()
    model_name = model or settings.gemini_model

    config = types.GenerateContentConfig(
        temperature=temperature,
        system_instruction=system_instruction,
        response_mime_type="application/json",
        response_schema=schema,
    )

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config,
        )
    except Exception as e:
        logger.exception("Gemini call failed: %s", e)
        raise

    text = response.text.strip()
    # Sometimes Gemini wraps in ```json ... ``` fences — strip them.
    if text.startswith("```"):
        lines = text.splitlines()
        lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse JSON from model: %s\nRaw: %s", e, text[:500])
        raise ValueError(f"Model output was not valid JSON: {e}")

    try:
        return schema.model_validate(data)
    except ValidationError as e:
        logger.error("Schema validation failed: %s\nData: %s", e, data)
        raise


def plain_generate(
    *,
    prompt: str,
    model: str | None = None,
    temperature: float = 0.4,
    system_instruction: str = BASE_SYSTEM_INSTRUCTION,
) -> str:
    """Plain text generation (used for notes/flashcards/MCQs where we want list outputs)."""
    client = get_client()
    model_name = model or settings.gemini_model

    config = types.GenerateContentConfig(
        temperature=temperature,
        system_instruction=system_instruction,
    )
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=config,
    )
    return response.text.strip()
