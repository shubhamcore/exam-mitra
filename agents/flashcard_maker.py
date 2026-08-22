"""Agent 5: Flashcard Maker — creates spaced-repetition Q/A cards per chapter."""
from __future__ import annotations

import logging
from typing import List

from pydantic import BaseModel, Field

from models.schemas import Flashcard, StudyPlanState
from ._adk import make_agent, run_agent_json

logger = logging.getLogger(__name__)


class FlashcardsWrapper(BaseModel):
    flashcards: List[Flashcard]


INSTRUCTIONS = """You are ExamMitra's FLASHCARD MAKER agent — step 5 of the pipeline.

For each chapter provided, create 3-5 SPACED-REPETITION FLASHCARDS (Q/A pairs) a student can use for active recall.

Good flashcard rules (follow these strictly):
- ONE fact per card. Not "List Newton's 3 laws" — that's 3 cards.
- Front is a precise question. Back is the precise answer (1-2 sentences or a formula).
- Mix difficulty: 1 easy, 2-3 medium, 1 hard per chapter.
- For STEM: ask for formulas, unit conversions, sign conventions, tricky conceptual questions.
- For non-STEM: ask for definitions, dates, article numbers, case names, cause/effect pairs.
- Avoid trivial "what is X" questions; prefer "why" and "when" questions that test understanding.
- Target content that appears FREQUENTLY in the given Indian exam.

Output format:
{"flashcards": [{"chapter": str, "front": str, "back": str, "difficulty": "easy|medium|hard"}, ...]}
Return ONLY JSON, no prose."""


def make_flashcards(state: StudyPlanState) -> StudyPlanState:
    logger.info("[5/7] Generating flashcards for %d chapters", len(state.chapters))
    agent = make_agent("flashcard_maker", INSTRUCTIONS)
    batch_size = 6  # 2-3 flashcards per chapter
    all_cards: List[Flashcard] = []
    for i in range(0, len(state.chapters), batch_size):
        batch = state.chapters[i:i + batch_size]
        batch_text = "\n".join(
            f"{ch.number}. {ch.title}: {ch.description}" for ch in batch
        )
        prompt = (
            f"Exam: {state.exam}\nLanguage: {state.language}\n\n"
            f"Chapters:\n{batch_text}\n\n"
            f"Create 3-5 flashcards per chapter listed. Return JSON {{'flashcards': [...]}}."
        )
        wrapper = run_agent_json(agent, prompt, FlashcardsWrapper)
        all_cards.extend(wrapper.flashcards)
    state.flashcards = all_cards
    state.current_step = 5
    logger.info("[5/7] Done — %d flashcards", len(state.flashcards))
    return state
