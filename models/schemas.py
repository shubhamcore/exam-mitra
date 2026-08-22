"""Pydantic models for the agent pipeline state and outputs.

All inter-agent data flows through a strongly-typed `StudyPlanState` object.
This is what makes our architecture "disciplined" rather than a brittle script:
each sub-agent has a clear input contract and output contract.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import List, Optional
from typing import Any, Dict
from pydantic import BaseModel, Field, field_validator


# ---------- Outputs from individual agents ----------


class Chapter(BaseModel):
    """A single chapter/unit parsed from the syllabus."""
    number: int = Field(..., description="1-indexed chapter number")
    title: str = Field(..., description="Concise chapter title")
    description: str = Field(..., description="2-3 sentence summary of what the chapter covers")
    estimated_hours: float = Field(..., ge=0.5, le=40, description="Realistic hours to master the chapter")
    importance: str = Field(..., description="high / medium / low — based on exam weight")


class DailyTask(BaseModel):
    """One day's study assignment."""
    day: int = Field(..., ge=1, description="Day number in the plan")
    date: Optional[str] = Field(None, description="ISO date (YYYY-MM-DD) if a start date is given")
    chapter: str = Field(..., description="Chapter/topic to cover that day")
    hours: float = Field(..., ge=0.5, le=12, description="Recommended hours of focus")
    activities: List[str] = Field(..., description="Specific activities: watch lecture, read notes, solve MCQs, revise")


class Resource(BaseModel):
    """A recommended learning resource (video/article)."""
    chapter: str = ""
    title: str = ""
    url: str = ""
    platform: str = "other"
    teacher_or_channel: str = ""
    why: str = ""
    duration_minutes: int = 0


class ChapterNote(BaseModel):
    """Concise revision notes for one chapter."""
    chapter: str = ""
    key_concepts: List[str] = Field(default_factory=list)
    formulas_or_definitions: List[str] = Field(default_factory=list)
    common_mistakes: List[str] = Field(default_factory=list)
    summary: str = ""


class Flashcard(BaseModel):
    """A spaced-repetition flashcard."""
    chapter: str = ""
    front: str = ""
    back: str = ""
    difficulty: str = "medium"


class MCQOption(BaseModel):
    label: str = Field(..., description="A / B / C / D")
    text: str


class MCQQuestion(BaseModel):
    """A single multiple-choice practice question."""
    chapter: str = ""
    question: str = ""
    options: List[MCQOption] = Field(default_factory=list, min_length=0, max_length=4)
    correct_answer: str = ""
    explanation: str = ""
    difficulty: str = "medium"

    @field_validator("options", mode="before")
    @classmethod
    def _coerce_options(cls, v: Any) -> List[MCQOption]:
        """Accept both list format and dict format ({'A': 'text', ...}) from the LLM."""
        if isinstance(v, dict):
            return [MCQOption(label=k, text=str(val)) for k, val in v.items()]
        if isinstance(v, list):
            out = []
            for i, item in enumerate(v):
                if isinstance(item, dict):
                    # Dict item like {"label": "A", "text": "..."} or {"A": "..."}
                    if "label" in item and "text" in item:
                        out.append(MCQOption(**item))
                    elif len(item) == 1:
                        k, val = next(iter(item.items()))
                        out.append(MCQOption(label=str(k), text=str(val)))
                    else:
                        # Fallback: assign labels A/B/C/D
                        for j, (k, val) in enumerate(item.items()):
                            out.append(MCQOption(label=str(k), text=str(val)))
                elif isinstance(item, str):
                    # Strings — auto-label
                    letter = chr(ord('A') + i)
                    out.append(MCQOption(label=letter, text=item))
                else:
                    out.append(MCQOption(label=getattr(item, 'label', chr(ord('A')+i)),
                                         text=str(getattr(item, 'text', item))))
            return out[:4]
        return v


class WeakArea(BaseModel):
    chapter: str
    topic: str
    feedback: str = Field(..., description="Specific feedback on what went wrong and how to improve")


# ---------- Top-level state (flows through the pipeline) ----------


class StudyPlanState(BaseModel):
    """Mutable state passed through every agent in the pipeline.

    Each agent reads what it needs from earlier fields and appends its own output.
    Persisted to Firestore so jobs can be resumed across Cloud Run invocations.
    """
    # ---- input ----
    job_id: str = Field(..., description="Unique job ID")
    exam: str = Field(..., description="e.g., 'JEE Mains Physics'")
    syllabus_text: str = Field(..., description="Raw syllabus text/topic list from user")
    start_date: Optional[date] = None
    daily_hours_budget: float = Field(4.0, ge=1, le=16)
    language: str = Field("en", description="en / hi / hinglish")

    # ---- output (filled in by agents as they run) ----
    chapters: List[Chapter] = Field(default_factory=list)
    daily_plan: List[DailyTask] = Field(default_factory=list)
    resources: List[Resource] = Field(default_factory=list)
    notes: List[ChapterNote] = Field(default_factory=list)
    flashcards: List[Flashcard] = Field(default_factory=list)
    mcqs: List[MCQQuestion] = Field(default_factory=list)

    # ---- status ----
    current_step: int = Field(0, description="1 = parsed, 2 = planned, 3 = resources, 4 = notes, 5 = flashcards, 6 = mcqs, 7 = done")
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class StudyPackage(BaseModel):
    """The final output returned to the user (subset of state, formatted)."""
    exam: str
    total_chapters: int
    total_days: int
    total_hours: float
    daily_plan: List[DailyTask]
    resources: List[Resource]
    notes: List[ChapterNote]
    flashcards: List[Flashcard]
    mcqs: List[MCQQuestion]
