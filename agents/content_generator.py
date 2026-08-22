"""Combined Notes + Flashcards + MCQ generator (Steps 4, 5, 6).

Generates HIGH-QUALITY revision notes, active-recall flashcards, and exam-style
MCQs with detailed explanations. Uses strict schema enforcement and exam-aware
prompting.
"""
from __future__ import annotations

import logging
from typing import List

from pydantic import BaseModel, Field, field_validator

from models.schemas import ChapterNote, Flashcard, MCQOption, MCQQuestion, StudyPlanState
from ._adk import make_agent, run_agent_json

logger = logging.getLogger(__name__)


class BatchContent(BaseModel):
    notes: List[ChapterNote]
    flashcards: List[Flashcard]
    mcqs: List[MCQQuestion]

    @field_validator("notes", mode="before")
    @classmethod
    def _ensure_notes_fields(cls, v):
        out = []
        for item in v:
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

    @field_validator("flashcards", mode="before")
    @classmethod
    def _ensure_flashcards_fields(cls, v):
        out = []
        for item in v:
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

    @field_validator("mcqs", mode="before")
    @classmethod
    def _coerce_mcq_options(cls, v):
        out = []
        for q in v:
            if not isinstance(q, dict):
                continue
            opts = q.get("options", [])
            fixed_opts = []
            if isinstance(opts, dict):
                for k, val in opts.items():
                    fixed_opts.append({"label": str(k), "text": str(val)})
            elif isinstance(opts, list):
                for i, item in enumerate(opts):
                    if isinstance(item, dict) and "label" in item and "text" in item:
                        fixed_opts.append({"label": str(item["label"]), "text": str(item["text"])})
                    elif isinstance(item, dict) and len(item) == 1:
                        k, val = next(iter(item.items()))
                        fixed_opts.append({"label": str(k), "text": str(val)})
                    elif isinstance(item, str):
                        fixed_opts.append({"label": chr(ord('A') + i), "text": item})
                    elif isinstance(item, list) and len(item) == 2:
                        fixed_opts.append({"label": str(item[0]), "text": str(item[1])})
            # Pad to 4 if needed (shouldn't happen but safety)
            while len(fixed_opts) < 4:
                fixed_opts.append({"label": chr(ord('A') + len(fixed_opts)), "text": "(option not generated)"})
            q["options"] = fixed_opts[:4]
            # Normalize correct answer
            ca = str(q.get("correct_answer", "A")).strip().upper()
            if len(ca) > 1:
                ca = ca[0]
            if ca not in "ABCD":
                ca = "A"
            q["correct_answer"] = ca
            q.setdefault("chapter", "")
            q.setdefault("explanation", "")
            q.setdefault("difficulty", "medium")
            q.setdefault("question", "")
            out.append(q)
        return out


CONTENT_INSTRUCTIONS = """You are ExamMitra's STUDY CONTENT GENERATOR — steps 4, 5, 6 of an autonomous study pipeline for Indian exam aspirants (JEE, NEET, UPSC, SSC, GATE, CBSE, Banking, etc.).

Given a batch of chapters for a specific exam, produce THREE things for EVERY chapter listed.

═══════════════════════════════════════════
1. REVISION NOTES (1 note PER chapter)
═══════════════════════════════════════════
For EACH chapter produce an object with these keys:
- "chapter": EXACT chapter title as given (string, required)
- "key_concepts": 8-12 bullet points of the MOST important concepts, definitions, derivations, PYQ-relevant facts. Be SPECIFIC. Example: "Average velocity = total displacement / total time (NOT average speed = total distance / time)".
- "formulas_or_definitions": 6-15 items. For STEM (Physics/Chem/Math): include ALL essential formulas with variable meanings and units. Example entry: "F = ma (Newton's 2nd Law, force in N, mass in kg, acceleration in m/s²)". For non-STEM: key definitions, article numbers, dates, classifications.
- "common_mistakes": 3-5 specific mistakes students ACTUALLY make in exams. Example: "Using v = u + at for non-uniform acceleration (it only applies to constant a)".
- "summary": 3-4 sentence exam-focused summary covering what the chapter is about, its weightage, and the 2-3 most-tested concepts.

CRITICAL FOR STEM: Formulas MUST include every major formula. For Kinematics that means: v=u+at, s=ut+1/2 at², v²=u²+2as, s_nth = u + a(n-1/2), average velocity = (v+u)/2 (const a only), projectile range R = u²sin(2θ)/g, max height H = u²sin²θ/(2g), time of flight T = 2u sinθ/g, relative velocity, centripetal acceleration a_c = v²/r, etc.

═══════════════════════════════════════════
2. FLASHCARDS (5 cards PER chapter minimum)
═══════════════════════════════════════════
For EACH chapter produce 5-8 flashcards for active recall. Each card:
- "chapter": EXACT chapter title
- "front": Question testing ONE specific fact/concept/formula. GOOD: "What is the range of a projectile launched with velocity u at angle θ from horizontal?" BAD: "Explain projectile motion."
- "back": Precise, complete answer including formula if applicable.
- "difficulty": one of "easy", "medium", "hard" (mix them — formula recall easy, concept medium, trick questions hard).

═══════════════════════════════════════════
3. MCQs (4 questions PER chapter minimum)
═══════════════════════════════════════════
For EACH chapter produce 4 MCQs in exam style (JEE/NEET/UPSC as appropriate).

RULES FOR MCQs:
- Mix difficulty: 1 easy, 2 medium, 1 hard per chapter.
- Distractors (wrong options) MUST be plausible — the answers students get when they mix up formulas/signs/powers. For numericals, CALCULATE the wrong answers that come from common errors.
- "question": The actual question (include realistic numbers for numericals).
- "options": ALWAYS an ARRAY of exactly 4 objects. Each object is of the form LABEL:TEXT where label is A/B/C/D and text is the option text. IMPORTANT: represent this as an ARRAY not a dict.
- "correct_answer": Single uppercase letter "A", "B", "C", or "D" matching the correct option.
- "explanation": 3-5 sentences explaining WHY the answer is correct (show calculation for numericals) AND why each wrong option is wrong (which student mistake produces it). This is the LEARNING value — make it excellent.
- "difficulty": "easy" | "medium" | "hard"
- "chapter": EXACT chapter title.

MCQ OPTIONS EXAMPLE (array format):
  "options": [
    ["A", "3 s"],
    ["B", "4 s"],
    ["C", "5 s"],
    ["D", "6 s"]
  ]
(The validator will convert these to proper objects.)

═══════════════════════════════════════════
OUTPUT FORMAT
═══════════════════════════════════════════
Return ONLY valid JSON (no markdown fences, no prose). Top-level keys:
  "notes"        — array of note objects (one per chapter)
  "flashcards"   — array of flashcard objects
  "mcqs"         — array of MCQ objects

Every chapter from the input MUST appear in the notes array with the EXACT title."""


def generate_content(state: StudyPlanState) -> StudyPlanState:
    """Generate notes + flashcards + MCQs in batched calls."""
    logger.info(f"[4-6/7] Generating notes, flashcards, MCQs for {len(state.chapters)} chapters (batch mode)")
    agent = make_agent("content_generator", CONTENT_INSTRUCTIONS)

    # Smaller batch size = higher quality (less chance of LLM rushing)
    batch_size = 3
    all_notes: List[ChapterNote] = []
    all_cards: List[Flashcard] = []
    all_mcqs: List[MCQQuestion] = []
    total_batches = (len(state.chapters) + batch_size - 1) // batch_size

    for i in range(0, len(state.chapters), batch_size):
        batch = state.chapters[i:i + batch_size]
        batch_idx = (i // batch_size) + 1
        batch_text = "\n\n".join(
            f"Chapter {ch.number}: \"{ch.title}\"\n"
            f"  Description: {ch.description}\n"
            f"  Estimated hours: {ch.estimated_hours}\n"
            f"  Importance in {state.exam}: {ch.importance}"
            for ch in batch
        )
        chapter_titles = [ch.title for ch in batch]
        prompt = (
            f"Exam: {state.exam}\n"
            f"Language: {state.language} (use Hinglish if language is 'hi' or 'hinglish')\n\n"
            f"Generate notes, 5-8 flashcards, and 4 MCQs for EACH of these {len(batch)} chapters:\n"
            f"{batch_text}\n\n"
            f"REQUIREMENTS CHECKLIST:\n"
            f"✓ Produce {len(batch)} notes objects (one per chapter title)\n"
            f"✓ Each note has chapter = EXACT title: {chapter_titles}\n"
            f"✓ Each note has 8-12 key concepts, 6-15 formulas/definitions, 3-5 common mistakes, 3-4 sentence summary\n"
            f"✓ Produce {len(batch) * 5}-{len(batch) * 8} flashcards total (5-8 per chapter)\n"
            f"✓ Produce {len(batch) * 4} MCQs total (4 per chapter, mix easy/medium/hard)\n"
            f"✓ MCQ options MUST be an ARRAY of 4 entries, each being [label, text] (NOT a dict)\n"
            f"✓ MCQ distractors must be plausible (common student errors)\n"
            f"✓ MCQ explanations must be 3-5 sentences showing why correct and why each wrong option is wrong\n"
            f"✓ For STEM chapters, include ALL important formulas with variables defined\n\n"
            f"Return the JSON object now."
        )
        try:
            wrapper = run_agent_json(agent, prompt, BatchContent)
            all_notes.extend(wrapper.notes)
            all_cards.extend(wrapper.flashcards)
            all_mcqs.extend(wrapper.mcqs)
            logger.info(f"  Batch {batch_idx}/{total_batches} done: {len(wrapper.notes)} notes, {len(wrapper.flashcards)} cards, {len(wrapper.mcqs)} MCQs")
        except Exception as e:
            logger.error(f"  Batch {batch_idx}/{total_batches} failed: {e}")
            # Continue with next batch rather than failing entire pipeline
            continue

    state.notes = all_notes
    state.flashcards = all_cards
    state.mcqs = all_mcqs
    state.current_step = 6
    logger.info(f"[4-6/7] Done — notes:{len(all_notes)}, flashcards:{len(all_cards)}, mcqs:{len(all_mcqs)}")
    return state
