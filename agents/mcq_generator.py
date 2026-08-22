"""Agent 6: MCQ Generator — creates practice multiple-choice questions per chapter."""
from __future__ import annotations

import logging
from typing import List

from pydantic import BaseModel, Field

from models.schemas import MCQQuestion, StudyPlanState
from ._adk import make_agent, run_agent_json

logger = logging.getLogger(__name__)


class MCQsWrapper(BaseModel):
    mcqs: List[MCQQuestion]


INSTRUCTIONS = """You are ExamMitra's MCQ GENERATOR agent — step 6 of the pipeline.

For each chapter provided, create 2 MULTIPLE CHOICE QUESTIONS in the style of Indian competitive exams (JEE/NEET/UPSC/SSC).

PER-QUESTION JSON SHAPE (copy this exactly — options MUST be an ARRAY):
{"chapter": "...", "question": "...", "options": [{"label": "A", "text": "..."}, {"label": "B", "text": "..."}, {"label": "C", "text": "..."}, {"label": "D", "text": "..."}], "correct_answer": "A", "explanation": "...", "difficulty": "medium"}

CRITICAL RULES:
- "options" MUST be a JSON ARRAY of objects, NOT a dict/object like {"A": "..."}.
- Exactly 4 options per question labeled A, B, C, D.
- Distractors must reflect common student mistakes.
- For STEM include at least one calculation-based question.
- "chapter" must EXACTLY match a chapter title from the input.
- Return ONLY {"mcqs": [...]} — no prose, no markdown fences."""


def generate_mcqs(state: StudyPlanState) -> StudyPlanState:
    logger.info("[6/7] Generating MCQs for %d chapters", len(state.chapters))
    agent = make_agent("mcq_generator", INSTRUCTIONS)
    batch_size = 5  # fewer LLM calls; ask for 2 MCQs/chapter
    all_mcqs: List[MCQQuestion] = []
    for i in range(0, len(state.chapters), batch_size):
        batch = state.chapters[i:i + batch_size]
        batch_text = "\n".join(
            f"{ch.number}. {ch.title}: {ch.description}" for ch in batch
        )
        prompt = (
            f"Exam: {state.exam}\nLanguage: {state.language}\n\n"
            f"Chapters:\n{batch_text}\n\n"
            f"Create exactly 2 MCQs per chapter listed. Remember options must be an ARRAY of objects, not a dict. "
            f"Return JSON {{\"mcqs\": [...]}}."
        )
        wrapper = run_agent_json(agent, prompt, MCQsWrapper)
        all_mcqs.extend(wrapper.mcqs)
        logger.info("  MCQs batch %d/%d done", (i // batch_size) + 1,
                    (len(state.chapters) + batch_size - 1) // batch_size)
    state.mcqs = all_mcqs
    state.current_step = 6
    logger.info("[6/7] Done — %d MCQs", len(state.mcqs))
    return state
