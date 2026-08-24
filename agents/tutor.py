"""Agent 9: Tutor Chat — answers a student's follow-up question using their plan/notes as context.

This is the interactive "AI Tutor" panel next to notes/MCQs. The student asks a free-text question,
we bundle up the relevant chapter's notes + formulas + flashcards, and Gemini answers clearly with LaTeX.
"""
from __future__ import annotations

import logging
from typing import List

from pydantic import BaseModel, Field

from ._adk import make_agent, run_agent_text

logger = logging.getLogger(__name__)


TUTOR_INSTRUCTIONS = r"""You are ExamMitra's PERSONAL AI TUTOR — a patient, sharp, Indian-exam-savvy teacher.

The student is preparing for a specific Indian exam (JEE / NEET / UPSC / SSC / Banking / BPSC / MBBS / BTech etc.).
They have just read some revision notes and practiced MCQs, and now they are asking you a follow-up question.

HOW YOU ANSWER:
1. Be WARM and ENCOURAGING but never ramble. Be the teacher a student from a small town wishes they had.
2. Explain in SHORT, CLEAR steps. Use analogies when it helps (cricket, trains, everyday Indian life).
3. EVERY math symbol, variable, formula, subscript/superscript, Greek letter MUST be wrapped in $...$ LaTeX.
   Example: "The displacement is $\Delta x = x_f - x_i$ where $x_f$ is final position."
4. If the question is a "why" question, start from intuition, THEN give the formal rule/formula.
5. If the student made a common mistake, NAME IT EXPLICITLY. ("This is the classic sign-convention trap.")
6. For derivation questions: show every step. Don't skip algebra.
7. If the question is NOT related to the chapter, gently say "That's outside this chapter, but here's a quick answer:"
   and answer briefly, then nudge them back on track.
8. You MAY draw one small ASCII diagram in a triple-backtick code block if it genuinely clarifies things
   (projectile parabola, pulley setup, circuit, polity flow, etc.). Keep diagrams ≤8 lines.
9. End with ONE tiny check-question to confirm they understood (like "Tell me: what is the acceleration at the peak of a projectile?")
   UNLESS the student specifically asked for a fact/definition.
10. Keep the whole answer CONCISE — usually 150-350 words. Quality > length.

LANGUAGE:
- If language is 'hi': answer entirely in Devanagari हिन्दी script.
- If 'hinglish': answer in conversational Roman-script Hinglish ("Bhai, projectile ke peak par velocity zero hota hai lekin acceleration $g$ nahi, woh hamesha $9.8 \,\text{m/s}^2$ neeche ki taraf hota hai.")
- If 'en': answer in English.

DO NOT prefix with "Dear student" or other formal fluff. Just answer.
"""


class TutorResponse(BaseModel):
    answer: str = Field(..., description="The tutor's answer (can contain $...$ LaTeX and a single ``` code-block diagram)")


def _relevant_context(
    state,
    chapter_hint: str = "",
) -> str:
    """Pick out notes/flashcards/MCQs most relevant to the student's question."""
    ctx_parts = []
    # Always include exam + language at top
    ctx_parts.append(f"Exam: {state.exam}")

    # Find matching notes by keyword overlap
    hint_words = set(chapter_hint.lower().split()) if chapter_hint else set()
    def score(note_chapter: str, text_blob: str) -> int:
        if not chapter_hint:
            return 1
        blob = (note_chapter + " " + text_blob).lower()
        return sum(1 for w in hint_words if w in blob)

    # Grab top 2 most relevant notes
    scored = []
    for n in state.notes:
        blob = " ".join(n.key_concepts) + " " + " ".join(n.formulas_or_definitions)
        scored.append((score(n.chapter, blob), n))
    scored.sort(key=lambda x: -x[0])
    for _, n in scored[:3]:
        ctx_parts.append(
            f"\n[CHAPTER: {n.chapter}]\n"
            f"Key concepts:\n- " + "\n- ".join(n.key_concepts)
            + (("\nFormulas / definitions:\n- " + "\n- ".join(n.formulas_or_definitions[:8])) if n.formulas_or_definitions else "")
            + (("\nCommon mistakes:\n- " + "\n- ".join(n.common_mistakes[:4])) if n.common_mistakes else "")
        )
    # Relevant flashcards (just a few for Q&A context)
    relevant_fc = [f for f in state.flashcards if not chapter_hint or score(f.chapter, f.front + " " + f.back) > 0][:5]
    if relevant_fc:
        ctx_parts.append(
            "\n[SAMPLE FLASHCARDS]\n"
            + "\n".join(f"- Q: {f.front}  →  A: {f.back}" for f in relevant_fc)
        )
    return "\n".join(ctx_parts)


def ask_tutor(
    state,
    question: str,
    chapter_hint: str = "",
    conversation_history: list[str] | None = None,
) -> str:
    """Answer a single student question; returns answer text (may contain LaTeX)."""
    logger.info("[9/9] Tutor question: %s", question[:120])
    agent = make_agent("tutor_chat", TUTOR_INSTRUCTIONS)
    context = _relevant_context(state, chapter_hint)
    history_blob = ""
    if conversation_history:
        # Keep last 4 turns
        history_blob = "\n\n[RECENT CONVERSATION (for continuity)]:\n" + "\n".join(conversation_history[-8:])
    prompt = (
        f"Student's language: {state.language}\n\n"
        f"{context}\n"
        f"{history_blob}\n\n"
        f"[STUDENT ASKS]: {question}\n\n"
        f"[YOUR ANSWER]:"
    )
    answer = run_agent_text(agent, prompt).strip()
    # Strip any leading "Answer:" labels the model sometimes adds
    for prefix in ("Answer:", "Tutor:", "A:", "AI Tutor:"):
        if answer.startswith(prefix):
            answer = answer[len(prefix):].strip()
    logger.info("[9/9] Tutor answer: %s", answer[:120].replace("\n", " "))
    return answer
