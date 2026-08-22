"""Agent 4: Notes Generator — writes concise revision notes per chapter."""
from __future__ import annotations

import logging
from typing import List

from pydantic import BaseModel, Field

from models.schemas import ChapterNote, StudyPlanState
from ._adk import make_agent, run_agent_json

logger = logging.getLogger(__name__)


class NotesWrapper(BaseModel):
    notes: List[ChapterNote]


INSTRUCTIONS = """You are ExamMitra's NOTES GENERATOR agent — step 4 of the pipeline.

Given an exam name and a list of chapters, write CONCISE REVISION NOTES for each chapter.
These are meant for quick revision BEFORE an exam, not for first-time learning.

For each chapter produce:
- chapter: exact chapter title (must match input)
- key_concepts: 5-8 bullet points of the most exam-relevant concepts (short, specific)
- formulas_or_definitions: list of key formulas, laws, or definitions students MUST memorize (relevant for STEM/law/medicine; empty list if not applicable)
- common_mistakes: 2-5 mistakes students typically make on this topic in the actual exam
- summary: 2-3 sentence executive summary

Rules:
- Be specific. Not "learn about motion" but "v = u + at is the first equation of motion; applies only under constant acceleration".
- For Indian exams, prioritize NCERT content and standard PYQ patterns.
- Keep each bullet under 160 characters.
- Return ONLY JSON {"notes": [...]}."""


def generate_notes(state: StudyPlanState) -> StudyPlanState:
    logger.info("[4/7] Generating revision notes for %d chapters", len(state.chapters))
    agent = make_agent("notes_generator", INSTRUCTIONS)
    chapters_text = "\n".join(
        f"{ch.number}. {ch.title}: {ch.description}" for ch in state.chapters
    )
    # If many chapters, batch in groups to avoid token limits
    batch_size = 6  # fewer LLM calls = faster + fewer rate limits
    all_notes: List[ChapterNote] = []
    for i in range(0, len(state.chapters), batch_size):
        batch = state.chapters[i:i + batch_size]
        batch_text = "\n".join(
            f"{ch.number}. {ch.title}: {ch.description}" for ch in batch
        )
        prompt = (
            f"Exam: {state.exam}\nLanguage: {state.language}\n\n"
            f"Chapters:\n{batch_text}\n\n"
            f"Return JSON {{'notes': [...]}} with ChapterNote objects for EACH chapter listed above."
        )
        wrapper = run_agent_json(agent, prompt, NotesWrapper)
        all_notes.extend(wrapper.notes)
        logger.info("  Notes batch %d/%d done", (i // batch_size) + 1,
                    (len(state.chapters) + batch_size - 1) // batch_size)
    state.notes = all_notes
    state.current_step = 4
    logger.info("[4/7] Done — notes for %d chapters", len(state.notes))
    return state
