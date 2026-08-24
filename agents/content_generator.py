"""Combined Notes + Flashcards + MCQ generator (Steps 4, 5, 6).

Generates HIGH-QUALITY revision notes, active-recall flashcards, and exam-style
MCQs with detailed explanations. Uses strict schema enforcement and exam-aware
prompting — PYQ-style questions ordered easy→hard to build student confidence.
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
            # Pad to 4 if needed
            while len(fixed_opts) < 4:
                fixed_opts.append({"label": chr(ord('A') + len(fixed_opts)), "text": "(option not generated)"})
            q["options"] = fixed_opts[:4]
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


CONTENT_INSTRUCTIONS = r"""You are ExamMitra's STUDY CONTENT GENERATOR — steps 4, 5, 6 of an autonomous study pipeline for Indian exam aspirants (JEE, NEET, UPSC, SSC, GATE, CBSE, Banking, NDA, State PSCs, BTech, MBBS, etc.).

Given a batch of chapters for a specific exam, produce THREE things for EVERY chapter listed.

═══════════════════════════════════════════
MATH FORMATTING — ABSOLUTELY CRITICAL
═══════════════════════════════════════════
ALL formulas MUST be in LaTeX inside $...$ delimiters.
WRONG: "v = u + at"     RIGHT: "$v = u + at$"
WRONG: "s = ut + 1/2 at^2"   RIGHT: "$s = ut + \frac{1}{2} a t^2$"
WRONG: "F = G Mm/r^2"    RIGHT: "$F = G \frac{M m}{r^2}$"

Use proper LaTeX: \frac{n}{d}, v_0, x^2, \theta, \pi, \omega, \Delta, \sqrt{x}, \sin\theta, \vec{F}, \sum, \int, \, (thin space before units).
Units go OUTSIDE $...$ e.g. "$v = u + at$ (velocity in m/s)".
EVERY math symbol/variable/formula MUST be inside $...$. NO exceptions.

═══════════════════════════════════════════
1. REVISION NOTES (1 per chapter)
═══════════════════════════════════════════
For EACH chapter:
- "chapter": EXACT chapter title (string, required)
- "key_concepts": 8-12 bullet points of MOST important / PYQ-relevant concepts. Use $...$ LaTeX for any math. Be exam-oriented and specific.
- "formulas_or_definitions": 8-18 items. STEM: every major formula with LaTeX + variable meanings + units. Non-STEM: key definitions, article numbers, dates, constitutional provisions.
- "common_mistakes": 3-5 specific mistakes students actually make on exams.
- "summary": 3-4 sentence exam-focused summary (what it covers, approximate weightage, top 2-3 tested concepts).

CRITICAL FOR STEM: include EVERY major formula for the chapter. For Kinematics: v=u+at, s=ut+½at², v²=u²+2as, s_nth = u + a(n-½), <v>=(u+v)/2, R=u²sin2θ/g, H=u²sin²θ/(2g), T=2u sinθ/g, a_c = v²/r, etc.

═══════════════════════════════════════════
2. FLASHCARDS (6-9 per chapter)
═══════════════════════════════════════════
Each card:
- "chapter": EXACT chapter title
- "front": ONE specific fact/formula/concept question with $...$ LaTeX. GOOD: "Write the projectile range formula." BAD: "Explain projectiles."
- "back": Precise answer with formula in $...$. Include brief derivation/context when helpful.
- "difficulty": "easy" | "medium" | "hard" (mix them).

═══════════════════════════════════════════
3. MCQs (6 per chapter, ordered EASY → HARD, PYQ-style)
═══════════════════════════════════════════
For EACH chapter produce 6 MCQs. ORDER THEM STRICTLY: Q1-2 easy, Q3-4 medium, Q5-6 hard.
This builds student confidence and keeps them hooked — easy wins first, then ramp up.

EXAM-SPECIFIC PYQ STYLE — match the actual exam:
- "JEE Main" / "JEE Mains": Single-concept numericals like real JEE Main PYQs. Easy = NCERT formula recall. Medium = standard JEE Main application. Hard = multi-concept JEE Main PYQ level.
- "JEE Advanced": Tricky multi-concept problems. Hard Q5-6 should be Advanced PYQ tier (pulleys+energy+collisions combined; organic reaction mechanism traps; multi-concept calculus).
- "NEET" / "AIIMS": 95% NCERT-line-based. Easy = direct NCERT line/fact. Medium = NCERT application. Hard = PYQ-level assertion-reason or multi-concept clinical/biology.
- "CBSE" / "Class 10" / "Class 12" / "BSEB" / "UP Board" / "ICSE" / "ISC" / "board": Board PYQ style. Adapt NCERT intext/exercise questions to MCQ. Include 1-mark concept, 2-mark reasoning, 3/5-mark type.
- "UPSC" / "IAS" / "CSAT": UPSC Prelims PYQ style — statement-based ("Which statements are correct?"), polity/eco/history/geography conceptual; CSAT quant/reasoning.
- "SSC" / "CGL" / "CHSL" / "Bank" / "IBPS" / "SBI" / "RRB" / "Railway": SSC/Banking PYQ style — one-liner factual, arithmetic short-trick, current GK.
- "GATE": GATE-style numerical + conceptual, proper engineering distractors.
- "BPSC" / "UPPSC" / "MPSC" / "State PSC": State PSC Prelims style — factual + conceptual, state GK mixed in where relevant.
- "NDA" / "CDS": NDA/CDS PYQ style — math + GAT mix.
- "CTET": CTET Pedagogy + subject MCQs.
- "BTech" / "BSc" / "MBBS" / "BCom" / "LLB" / college: University semester-exam style, matching typical internal/end-sem question patterns.
- Generic/other: sensible easy→hard ramp with exam-appropriate difficulty.

MCQ RULES:
- Distractors MUST be plausible (common student errors). For numericals CALCULATE wrong answers from real mistakes (e.g., forgetting ½, using diameter not radius, sin vs cos, sign errors).
- "question": Use $...$ LaTeX for all formulas/variables/units. Example: "A body starts from rest and accelerates uniformly at $4\,\text{m/s}^2$ for $5\,\text{s}$. The distance covered is:"
- "options": ARRAY of exactly 4 two-element ARRAYS [label, text]. Label = "A"/"B"/"C"/"D". NOT a dict. Use $...$ LaTeX for math.
- "correct_answer": single letter "A"/"B"/"C"/"D".
- "explanation": 3-5 sentences (STEM) or 2-4 sentences (non-STEM). Show FULL CALCULATION using $...$ LaTeX. Then explicitly say what error leads to EACH wrong option. Example:
  "$s = ut + \frac{1}{2}at^2$ with $u=0, a=4, t=5$ gives $s = \frac{1}{2}(4)(25) = 50\,\text{m}$ (Option B correct). Option A (25 m) comes from forgetting the $\frac{1}{2}$ factor. Option C (100 m) comes from using $s = at^2$ directly. Option D (20 m) confuses $v = u + at = 20$ m/s with displacement."
- "difficulty": "easy" for Q1-2, "medium" for Q3-4, "hard" for Q5-6.
- "chapter": EXACT chapter title.

MCQ OPTIONS FORMAT:
  "options": [
    ["A", "$25\,\text{m}$"],
    ["B", "$50\,\text{m}$"],
    ["C", "$100\,\text{m}$"],
    ["D", "$20\,\text{m}$"]
  ]

═══════════════════════════════════════════
OUTPUT FORMAT
═══════════════════════════════════════════
Return ONLY valid JSON (no markdown fences, no prose). Top-level keys:
  "notes"        — array of note objects (one per chapter)
  "flashcards"   — array of flashcard objects
  "mcqs"         — array of MCQ objects
Every chapter in the input MUST appear in the notes array with the EXACT title."""


def generate_content(state: StudyPlanState) -> StudyPlanState:
    """Generate notes + flashcards + MCQs in batched calls."""
    logger.info(f"[4-6/7] Generating notes, flashcards, MCQs for {len(state.chapters)} chapters (batch mode)")
    agent = make_agent("content_generator", CONTENT_INSTRUCTIONS)

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
f"Language: {state.language}\n"
f"LANGUAGE INSTRUCTION: If language is 'hi' (Hindi), write EVERYTHING in pure Hindi using Devanagari script (हिन्दी) — headings, concepts, explanations, mistakes, summaries, flashcards, MCQ questions AND options AND explanations — ALL must be in Hindi script. If language is 'hinglish', write in conversational Roman-script Hinglish (Hindi words in English letters + English technical terms where natural, e.g. 'Projectile ka range formula R = u²sin2θ/g hota hai'). If language is 'en', write in English.\n\n"
f"Generate notes, 6-9 flashcards, and 6 MCQs for EACH of these {len(batch)} chapters:\n"
f"{batch_text}\n\n"
f"REQUIREMENTS CHECKLIST:\n"
f"✓ Produce {len(batch)} notes objects (one per chapter title) with EXACT titles: {chapter_titles}\n"
f"✓ Each note: 8-12 key concepts, 8-18 formulas/definitions, 3-5 common mistakes, 3-4 sentence summary\n"
f"✓ Produce {len(batch) * 6}-{len(batch) * 9} flashcards total (6-9 per chapter)\n"
f"✓ Produce {len(batch) * 6} MCQs total (6 per chapter)\n"
f"✓ MCQs MUST be ORDERED easy → hard: Q1-2 easy, Q3-4 medium, Q5-6 hard WITHIN EACH CHAPTER (builds confidence)\n"
f"✓ Match the MCQ style to this specific exam — '{state.exam}'. Use PYQ-style questions as described in the system instructions.\n"
f"✓ MCQ options MUST be an ARRAY of 4 entries, each being [label, text] (NOT a dict)\n"
f"✓ MCQ distractors must be plausible (common student errors)\n"
f"✓ MCQ explanations: 3-5 sentences showing full calculation AND why each wrong option is wrong\n"
f"✓ EVERY math symbol, variable, formula, subscript, superscript, Greek letter MUST be inside $...$ LaTeX delimiters. Example: 'The acceleration $a$ is given by $F = ma$ where $m$ is mass.'\n"
f"✓ For physics/geometry/mechanism/polity-economy topics you MAY include 1 ASCII diagram (≤8 lines inside triple backticks) when genuinely helpful (pulleys, projectiles, circuits, flowcharts).\n\n"
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
            continue

    state.notes = all_notes
    state.flashcards = all_cards
    state.mcqs = all_mcqs
    state.current_step = 6
    logger.info(f"[4-6/7] Done — notes:{len(all_notes)}, flashcards:{len(all_cards)}, mcqs:{len(all_mcqs)}")
    return state
