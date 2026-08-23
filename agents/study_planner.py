"""Agent 2: Study Planner — turns chapters into a day-by-day plan."""
from __future__ import annotations

import logging
from typing import List

from pydantic import BaseModel, Field

from models.schemas import DailyTask, StudyPlanState
from ._adk import make_agent, run_agent_json

logger = logging.getLogger(__name__)


class PlanWrapper(BaseModel):
    daily_plan: List[DailyTask]


PLANNER_INSTRUCTIONS = """You are ExamMitra's STUDY PLANNER agent — step 2 of a 7-step study pipeline for Indian exam aspirants.

Given an exam name, list of chapters (each with estimated study hours and importance), and daily study budget, produce a DAY-BY-DAY study schedule.

RULES:
1. Calculate total days: sum(chapter hours) / daily_hours_budget. Round UP.
2. Allocate MORE days to HIGH importance chapters, FEWER days to LOW importance.
3. Every 5-6 study days, schedule a REVISION & PRACTICE day (chapter name should be "Revision & Practice" and activities should be "Revise previous chapters, Solve PYQs, Make mistake notebook").
4. For each study day:
   - "chapter": name of the main chapter/sub-topic to cover that day (break big chapters into specific sub-topics across days, e.g. "Kinematics: 1D Motion & Graphs" then "Kinematics: Projectile Motion" then "Kinematics: Relative Velocity")
   - "hours": hours for that day (match the daily budget; 2-8 hours depending on budget)
   - "activities": 4-6 SPECIFIC, DETAILED activities for that day. Be EXTREMELY specific:
     * Include WHICH educator lecture to watch (e.g., "Watch Alakh Pandey (PW) one-shot on 1D Kinematics")
     * Include WHICH problems to solve (e.g., "Solve NCERT exercise Q1-20 + last 10 years JEE Main PYQs on motion graphs", "Solve 30 MCQs from NEET previous year on cell organelles")
     * Include WHAT to make notes on (e.g., "Make formula sheet: write all 5 kinematics equations with units", "Make mind map of Fundamental Rights articles")
     * Include SELF-TEST activity (e.g., "Attempt 10-min quiz on v-t, s-t graphs", "Take 20 MCQ self-test and mark mistakes")
     Example good activities: ["Watch Physics Wallah (Alakh Sir) lecture on Newton's Laws (2 hrs)", "Read NCERT Chapter 5 + solve example problems (1 hr)", "Solve 25 JEE Main PYQs on friction & pulleys (1.5 hrs)", "Write all friction formulas + make mistake notes (30 min)", "Take 20-MCQ self-test on Laws of Motion (30 min)"].
     NEVER generic like "study the topic" or "complete the chapter" — be specific to the sub-topic with book/lecture/MCQ count.
5. Start Day 1 on start_date if provided; otherwise leave date as null (we'll fill it client-side).
6. Early days = easier/introductory content. Later days = harder topics + revision.
7. If there are only 1-2 chapters, still spread them properly across days with practice sessions.

OUTPUT FORMAT: Return ONLY valid JSON. Top-level key "daily_plan" whose value is an array of day objects. Each day object has keys: day (integer starting at 1), date (null), chapter (string), hours (float 2-6), activities (array of 3-4 specific activity strings). No prose, no markdown, no fences."""


def plan_study(state: StudyPlanState) -> StudyPlanState:
    """Create a day-by-day study schedule from chapters."""
    logger.info(f"[2/7] Planning study schedule across {len(state.chapters)} chapters ({state.daily_hours_budget} hrs/day)")
    agent = make_agent("study_planner", PLANNER_INSTRUCTIONS)

    chapters_summary = "\n".join(
        f"  Ch{ch.number}: {ch.title} — {ch.estimated_hours}h, importance={ch.importance}\n"
        f"    Description: {ch.description}"
        for ch in state.chapters
    )
    total_hours = sum(ch.estimated_hours for ch in state.chapters)
    estimated_days = round(total_hours / state.daily_hours_budget) + 2  # +2 for revision

    prompt = (
        f"Exam: {state.exam}\n"
        f"Daily study budget: {state.daily_hours_budget} hours/day\n"
        f"Start date: {state.start_date.isoformat() if state.start_date else 'not specified (date=null)'}\n"
        f"Total chapters: {len(state.chapters)}\n"
        f"Total estimated content hours: {total_hours:.1f}\n"
        f"Estimated total days needed (including revision): ~{estimated_days}\n\n"
        f"Chapters:\n{chapters_summary}\n\n"
        f"Produce a complete day-by-day plan covering ALL chapters with revision days every 5-6 days. Return JSON."
    )

    wrapper = run_agent_json(agent, prompt, PlanWrapper)
    # Re-number days in case the LLM skipped any
    for i, task in enumerate(wrapper.daily_plan, start=1):
        task.day = i
    state.daily_plan = wrapper.daily_plan
    state.current_step = 2
    logger.info(f"[2/7] Done — {len(state.daily_plan)} study days planned")
    return state
