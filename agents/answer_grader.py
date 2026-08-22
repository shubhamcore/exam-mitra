"""Agent 7: Answer Grader — grades a student's MCQ answers and identifies weak areas.

Triggered AFTER the student practices MCQs (not during initial plan generation).
"""
from __future__ import annotations

import logging
from typing import Dict, List

from pydantic import BaseModel, Field

from models.schemas import MCQQuestion, WeakArea, StudyPlanState
from ._adk import make_agent, run_agent_json

logger = logging.getLogger(__name__)


class GradeResult(BaseModel):
    score: int = Field(..., ge=0, description="Number of correct answers")
    total: int = Field(..., ge=1)
    percentage: float = Field(..., ge=0, le=100)
    weak_areas: List[WeakArea] = Field(default_factory=list, description="Chapters/topics to revisit")
    encouragement: str = Field(..., description="A short, encouraging message for the student (can be in Hinglish if requested)")


INSTRUCTIONS = """You are ExamMitra's ANSWER GRADER agent — step 7 of the pipeline.

You are given a list of MCQ questions (with correct answers and explanations) and the student's submitted answers.
Your job:
1. Compute the score (correct / total) and percentage.
2. For every WRONG answer, identify the chapter and specific sub-topic the student got wrong,
   and write a 1-2 sentence feedback note explaining the misconception and what to re-study.
3. Deduplicate weak areas so each chapter/topic appears at most once.
4. Write a short encouraging message tailored to the score (celebrate wins; motivate after low scores).
   If the user's language is Hinglish or Hindi, write the message in Hinglish; otherwise English.

Return ONLY valid JSON with these top-level keys:
- "score": integer number of correct answers
- "total": integer total questions
- "percentage": float 0-100
- "weak_areas": array of objects with keys "chapter" (string), "topic" (string), "feedback" (string) for each wrong answer
- "encouragement": short encouraging message (Hinglish if requested, else English)"""


def grade_answers(
    state: StudyPlanState,
    answers: Dict[str, str],  # question_index (as str) -> "A"/"B"/"C"/"D"
) -> GradeResult:
    """Grade submitted MCQ answers against the state's MCQ list."""
    logger.info("[7/7] Grading %d answers against %d MCQs",
                len(answers), len(state.mcqs))
    agent = make_agent("answer_grader", INSTRUCTIONS)

    # Build MCQ context
    mcq_lines = []
    for idx, q in enumerate(state.mcqs):
        opts = " | ".join(f"{o.label}) {o.text}" for o in q.options)
        mcq_lines.append(
            f"Q{idx}. [{q.chapter}] {q.question}\n  Options: {opts}\n  Correct: {q.correct_answer}\n  Explanation: {q.explanation}"
        )
    answer_lines = [f"Q{idx}: {answers.get(str(idx), '(skipped)')}" for idx in range(len(state.mcqs))]

    prompt = (
        f"Exam: {state.exam}\nLanguage: {state.language}\n\n"
        f"Questions & correct answers:\n" + "\n\n".join(mcq_lines) + "\n\n"
        f"Student's answers:\n" + "\n".join(answer_lines) + "\n\n"
        f"Return the GradeResult JSON."
    )
    result = run_agent_json(agent, prompt, GradeResult)
    logger.info("[7/7] Done — score=%d/%d (%.1f%%), weak_areas=%d",
                result.score, result.total, result.percentage, len(result.weak_areas))
    return result
