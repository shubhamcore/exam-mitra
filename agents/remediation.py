"""Agent 8: Adaptive Remediation — generates a focused revision mini-plan + extra MCQs when the student struggles on specific topics.

This is what makes Exam Mitra an AUTONOMOUS TUTOR (not just a planner):
  perceive → plan → teach → test → grade → detect weakness → RE-teach → RE-test
The closed feedback loop is THE "Taskmaster" wow moment.
"""
from __future__ import annotations

import logging
from typing import List

from pydantic import BaseModel, Field, field_validator

from models.schemas import (
    ChapterNote, Flashcard, MCQOption, MCQQuestion, DailyTask,
    WeakArea, StudyPlanState,
)
from ._adk import make_agent, run_agent_json

logger = logging.getLogger(__name__)


class _RelaxedDailyTask(BaseModel):
    """Loose DailyTask variant that coerces common LLM formatting mistakes like 'Day 1' or '2.0 hours'."""
    day: int = Field(..., description="Day number (integer)")
    date: str | None = None
    chapter: str = ""
    hours: float = Field(2.0, ge=0.25, le=12)
    activities: List[str] = Field(default_factory=list)

    @field_validator("day", mode="before")
    @classmethod
    def _coerce_day(cls, v):
        if isinstance(v, int): return v
        s = str(v).strip().lower().replace("day", "").strip()
        m = __import__("re").search(r"\d+", s)
        if m: return int(m.group())
        return 1

    @field_validator("hours", mode="before")
    @classmethod
    def _coerce_hours(cls, v):
        if isinstance(v, (int, float)): return float(v)
        s = str(v).strip().lower().replace("hours", "").replace("hrs", "").replace("hr", "").replace("h", "").strip()
        try: return float(s)
        except Exception: return 2.0

    @field_validator("activities", mode="before")
    @classmethod
    def _split_string_activities(cls, v):
        if isinstance(v, str):
            # Split on common bullets / numbers
            import re as _re
            parts = _re.split(r"(?:^|\n)\s*(?:[-*•]|\d+[.)])\s*", v)
            return [p.strip() for p in parts if p.strip()]
        return v


class RemediationPackage(BaseModel):
    """Targeted revision package for one or more weak chapters/topics."""
    # Short summary of what went wrong
    diagnosis: str = Field(..., description="1-2 sentence diagnosis of why the student struggled, e.g. 'Confusion between velocity & acceleration vectors; sign convention mistakes in kinematic equations.'")
    # 2-day focused revision plan
    revision_days: List[_RelaxedDailyTask] = Field(..., min_length=2, max_length=3, description="2-3 day focused mini-plan for the weak topics only")
    # Booster notes for the weak topics (deeper, with common pitfalls called out)
    booster_notes: List[ChapterNote] = Field(default_factory=list)
    # 5-8 harder MCQs targeting the weak sub-topics
    extra_mcqs: List[MCQQuestion] = Field(default_factory=list)
    # 4-6 targeted flashcards
    extra_flashcards: List[Flashcard] = Field(default_factory=list)
    # Encouraging closing
    motivation: str = Field(..., description="Short motivational push tailored to the student's effort")

    @field_validator("extra_mcqs", mode="before")
    @classmethod
    def _coerce_mcq_options(cls, v):
        out = []
        for q in v or []:
            if not isinstance(q, dict):
                continue
            opts = q.get("options", [])
            fixed = []
            if isinstance(opts, dict):
                for k, val in opts.items():
                    fixed.append({"label": str(k), "text": str(val)})
            elif isinstance(opts, list):
                for i, item in enumerate(opts):
                    if isinstance(item, dict) and "label" in item and "text" in item:
                        fixed.append({"label": str(item["label"]), "text": str(item["text"])})
                    elif isinstance(item, dict) and len(item) == 1:
                        k, val = next(iter(item.items()))
                        fixed.append({"label": str(k), "text": str(val)})
                    elif isinstance(item, str):
                        fixed.append({"label": chr(ord('A') + i), "text": item})
                    elif isinstance(item, list) and len(item) == 2:
                        fixed.append({"label": str(item[0]), "text": str(item[1])})
            while len(fixed) < 4:
                fixed.append({"label": chr(ord('A') + len(fixed)), "text": "(option not generated)"})
            q["options"] = fixed[:4]
            ca = str(q.get("correct_answer", "A")).strip().upper()
            if len(ca) > 1:
                ca = ca[0]
            if ca not in "ABCD":
                ca = "A"
            q["correct_answer"] = ca
            q.setdefault("chapter", "")
            q.setdefault("explanation", "")
            q.setdefault("difficulty", "hard")
            q.setdefault("question", "")
            out.append(q)
        return out

    @field_validator("extra_flashcards", mode="before")
    @classmethod
    def _fix_flashcards(cls, v):
        out = []
        for item in v or []:
            if isinstance(item, dict):
                out.append({
                    "chapter": item.get("chapter", ""),
                    "front": item.get("front", item.get("question", "")),
                    "back": item.get("back", item.get("answer", "")),
                    "difficulty": item.get("difficulty", "medium"),
                })
            else:
                out.append(item)
        return out

    @field_validator("booster_notes", mode="before")
    @classmethod
    def _fix_notes(cls, v):
        out = []
        for item in v or []:
            if isinstance(item, dict):
                out.append({
                    "chapter": item.get("chapter", ""),
                    "key_concepts": item.get("key_concepts", []),
                    "formulas_or_definitions": item.get("formulas_or_definitions", item.get("formulas", [])),
                    "common_mistakes": item.get("common_mistakes", []),
                    "summary": item.get("summary", ""),
                })
            else:
                out.append(item)
        return out


REMEDIATION_INSTRUCTIONS = r"""You are ExamMitra's ADAPTIVE REMEDIATION TUTOR — step 8 in an autonomous Indian-exam tutoring loop.

The student just attempted MCQs after studying, and got some topics WRONG. You now act as their personal tutor.
Your job is to REMEDIATE: give them a sharp, focused 2-3 day revision plan + booster notes + harder MCQs
on ONLY the weak topics so they can master them before moving on.

HOW TO WRITE CONTENT THAT HELPS:
- Be direct, warm, and honest — like a good teacher who cares. Don't sugarcoat but always encourage.
- Diagnose the ROOT MISCONCEPTION, not just the topic. ("You are confusing velocity with acceleration" — not "Revise kinematics.")
- Write KEY CONCEPTS that directly address the mistakes. Every concept must target a specific error.
- Emphasize SIGN CONVENTIONS, common pitfalls, and trick questions examiners love.
- For STEM, write formulas with $...$ LaTeX delimiters as always.
- Make the extra MCQs HARDER than the first round — multi-step reasoning, trickier distractors that
  correspond to REAL misconceptions students have. Each distractor must be a plausible wrong path.
- Explain each MCQ answer DEEPLY — show step-by-step derivation.
- Make flashcards that expose the exact confusion (e.g., front: "When is $v = u + at$ valid?" back: "Only for CONSTANT acceleration. For variable acceleration use $a = dv/dt$ and integrate.").
- Keep the 2-3 day revision plan VERY specific: which 30-min sub-topic to cover, which video to re-watch,
  how many PYQs to solve, which mistake to focus on avoiding.

LANGUAGE RULES:
- If the user's language is 'hi' (Hindi), write EVERYTHING in pure Devanagari हिन्दी.
- If 'hinglish', write in Roman-script conversational Hinglish (e.g. "Yahan galti ye hui ki aapne acceleration aur velocity confuse kar liya...").
- If 'en', write in English.

MATH / LATEX: EVERY formula, variable, Greek letter, subscript, superscript MUST be in $...$ delimiters.
Example: "$v_{avg} = \frac{\Delta x}{\Delta t}$". Even single variables like "$a$" in a sentence.

Return ONLY a valid JSON object. Use EXACTLY this shape:
{
  "diagnosis": "short root-cause diagnosis",
  "revision_days": [
    { "day": 1, "chapter": "...", "hours": 2.0, "activities": ["specific activity 1", "specific activity 2", "..."] },
    { "day": 2, "chapter": "...", "hours": 2.0, "activities": ["...", "..."] }
  ],
  "booster_notes": [ { "chapter": "...", "summary": "...", "key_concepts": ["..."], "formulas_or_definitions": ["$...$"], "common_mistakes": ["..."] } ],
  "extra_mcqs":  [ { "chapter": "...", "question": "...", "options": [{"label":"A","text":"..."},{"label":"B","text":"..."},{"label":"C","text":"..."},{"label":"D","text":"..."}], "correct_answer": "A", "explanation": "...", "difficulty": "hard" } ],
  "extra_flashcards": [ { "chapter": "...", "front": "...", "back": "..." } ],
  "motivation": "short encouraging closing"
}

CRITICAL TYPE RULES (JSON will be REJECTED if you violate these):
- "day" MUST be an INTEGER (1 or 2 or 3), NOT a string like "Day 1".
- "hours" MUST be a NUMBER (e.g. 2.0 or 2), NOT a string like "2 hours".
- "correct_answer" MUST be a single uppercase letter string: "A" or "B" or "C" or "D" — never more than one character.
- All formulas MUST use $...$ LaTeX delimiters.
No markdown fences (```), no commentary outside the JSON, no trailing commas.
"""


def build_remediation(
    state: StudyPlanState,
    weak_areas: List[WeakArea],
    score: int,
    total: int,
) -> RemediationPackage:
    """Generate a remediation package given the student's weak areas and score."""
    logger.info(
        "[8/8] Building remediation plan for %d weak areas (score %d/%d)",
        len(weak_areas), score, total,
    )
    agent = make_agent("adaptive_tutor", REMEDIATION_INSTRUCTIONS)

    # Build context: original notes for the weak chapters
    weak_chapters_lookup = {w.chapter.lower().strip(): w for w in weak_areas}
    relevant_notes = [n for n in state.notes
                      if n.chapter.lower().strip() in weak_chapters_lookup
                      or any(w.topic.lower() in (n.chapter + " " + " ".join(n.key_concepts)).lower()
                             for w in weak_areas)]
    relevant_mcqs = [q for q in state.mcqs if q.chapter.lower().strip() in weak_chapters_lookup]

    # Build weak-area description
    wa_lines = []
    for w in weak_areas:
        wa_lines.append(f"  - Chapter: {w.chapter} | Topic: {w.topic} | Feedback: {w.feedback}")

    # Original notes snippets for weak chapters
    notes_snippets = []
    for n in relevant_notes[:4]:
        kc_preview = "; ".join(n.key_concepts[:3])[:400]
        formulas_preview = "; ".join(n.formulas_or_definitions[:3])[:300]
        notes_snippets.append(f"Chapter '{n.chapter}':\n  Key concepts: {kc_preview}\n  Formulas: {formulas_preview}")

    # Wrong MCQ preview
    wrong_preview = []
    for q in relevant_mcqs[:5]:
        opts = " | ".join(f"{o.label}) {o.text}" for o in q.options)
        wrong_preview.append(f"Q: {q.question}\n    Options: {opts}\n    Correct: {q.correct_answer} — {q.explanation[:250]}")

    prompt = (
        f"Exam: {state.exam}\n"
        f"Language: {state.language}\n"
        f"Student score: {score}/{total} ({(score/total*100):.0f}%)\n\n"
        f"WEAK AREAS identified by grader:\n" + "\n".join(wa_lines) + "\n\n"
        f"ORIGINAL NOTES FOR WEAK CHAPTERS (so you know what the student already read):\n"
        + ("\n\n".join(notes_snippets) if notes_snippets else "(no prior notes)") + "\n\n"
        f"MCQ CONTEXT (questions in this area):\n"
        + ("\n\n".join(wrong_preview) if wrong_preview else "(no MCQs)") + "\n\n"
        f"Now produce the RemediationPackage JSON. Make every activity specific, every MCQ target a misconception, "
        f"and every concept point directly at fixing the mistakes above."
    )
    result = run_agent_json(agent, prompt, RemediationPackage)
    logger.info(
        "[8/8] Remediation ready: %d revision days, %d booster notes, %d extra MCQs, %d flashcards",
        len(result.revision_days), len(result.booster_notes),
        len(result.extra_mcqs), len(result.extra_flashcards),
    )
    return result
