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
   - "chapter": name of the main chapter to cover that day (sub-topic if chapter spans multiple days, e.g. "Kinematics: 1D Motion" then "Kinematics: Projectile Motion")
   - "hours": hours for that day (typically 2-6 depending on daily budget)
   - "activities": 3-4 SPECIFIC activities for that day (e.g., "Watch PW lecture on Newton's 2nd Law", "Solve 20 MCQs from HCV/NCERT", "Make short notes on friction", "Revise formulas of kinematics"). NOT generic like "study the topic" — be specific to the sub-topic.
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
