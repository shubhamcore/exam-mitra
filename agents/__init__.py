"""Agent pipeline for Exam Mitra.

Steps:
  1. parse_syllabus       — raw text → Chapter[]
  2. plan_study           — Chapter[] → DailyTask[]
  3. gather_resources     — chapters → Resource[] (via web search)
  4-6. generate_content   — chapters → notes + flashcards + MCQs (one LLM call)
  7. grade_answers        — user's MCQ answers → score + weak areas (called on demand)
  8. build_remediation    — weak areas → focused 2-day revision + extra MCQs + booster notes (on demand, ADAPTIVE LOOP)
  9. ask_tutor           — in-context tutor chat answer (on demand)
"""
from .syllabus_parser import parse_syllabus
from .study_planner import plan_study
from .resource_finder import gather_resources
from .content_generator import generate_content
from .answer_grader import grade_answers
from .remediation import build_remediation
from .tutor import ask_tutor

__all__ = [
    "parse_syllabus",
    "plan_study",
    "gather_resources",
    "generate_content",
    "grade_answers",
    "build_remediation",
    "ask_tutor",
]
