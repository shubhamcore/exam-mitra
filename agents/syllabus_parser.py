"""Agent 1: Syllabus Parser — parses raw text into structured chapters."""
from __future__ import annotations

import logging
from typing import List

from pydantic import BaseModel, Field

from models.schemas import Chapter, StudyPlanState
from ._adk import make_agent, run_agent_json

logger = logging.getLogger(__name__)


class ChaptersWrapper(BaseModel):
    chapters: List[Chapter]


SYLLABUS_PARSER_INSTRUCTIONS = """You are ExamMitra's SYLLABUS PARSER — step 1 of a 7-step autonomous study planner for Indian competitive exams (JEE, NEET, UPSC, SSC, GATE, Banking, CBSE, etc.).

YOUR JOB: Take the student's raw exam name and syllabus text (could be a single topic like "Kinematics" or a full 50-topic syllabus) and break it into LOGICAL study chapters/units.

CRITICAL RULES:
1. If the user gives a SINGLE topic/word (e.g., "Kinematics", "Thermodynamics", "Mughal Empire"), return EXACTLY 1 chapter. DO NOT split a single topic into sub-chapters.
2. If the user gives 2-4 topics, return 1 chapter per topic.
3. If the user gives a full syllabus with many topics (5+), group them into 4-10 logical chapters of related sub-topics (each chapter should be a unit that takes 3-10 hours to study).
4. For each chapter, estimate hours REALISTICALLY based on Indian exam standards:
   - A single focused topic like "Projectile Motion" = 2-4 hours
   - A medium unit like "Kinematics (1D+2D)" = 6-10 hours
   - A large unit like "Electromagnetism" = 15-25 hours
   - A full exam topic list = 50-200 hours total
5. Rate importance (high/medium/low) based on actual weightage in the specified exam (research your knowledge of JEE/NEET/UPSC PYQ patterns). For example, in JEE Mains Physics, Mechanics and Modern Physics are high, Units & Dimensions is low.
6. Description should be 2 specific sentences: what the chapter covers, and why it matters for the exam.
7. Chapter title must be a clear, standard name used in Indian textbooks/coaching (e.g. "Motion in a Straight Line (Kinematics 1D)", NOT "Chapter 1: Motion").

OUTPUT FORMAT: Return ONLY valid JSON. Top-level key "chapters" whose value is an array of chapter objects. Each chapter object has keys: number (integer), title (string), description (string), estimated_hours (float), importance (one of "high", "medium", "low"). No prose, no markdown fences, no explanations outside JSON."""


def parse_syllabus(state: StudyPlanState) -> StudyPlanState:
    """Parse raw syllabus text into structured Chapter objects."""
    logger.info(f"[1/7] Parsing syllabus for exam='{state.exam}' (input={len(state.syllabus_text)} chars)")
    agent = make_agent("syllabus_parser", SYLLABUS_PARSER_INSTRUCTIONS)
    prompt = (
        f"Exam: {state.exam}\n"
        f"Daily study budget: {state.daily_hours_budget} hours/day\n"
        f"Language: {state.language}\n\n"
        f"Raw syllabus/topics from the student:\n---\n{state.syllabus_text}\n---\n\n"
        f"Parse into appropriate chapters following the rules. Return JSON."
    )
    wrapper = run_agent_json(agent, prompt, ChaptersWrapper)
    for i, ch in enumerate(wrapper.chapters, start=1):
        ch.number = i
    state.chapters = wrapper.chapters
    state.current_step = 1
    logger.info(f"[1/7] Parsed into {len(state.chapters)} chapters (total ~{sum(c.estimated_hours for c in state.chapters):.0f} hours)")
    for ch in state.chapters:
        logger.info(f"  Ch{ch.number}: {ch.title} ({ch.estimated_hours}h, {ch.importance})")
    return state
