"""Agent 3: Resource Finder — uses search to find best free lectures per chapter."""
from __future__ import annotations

import logging

from models.schemas import StudyPlanState
from services.search import find_all_resources

logger = logging.getLogger(__name__)


def gather_resources(state: StudyPlanState) -> StudyPlanState:
    """Find real free resources (YouTube lectures, NPTEL, Khan Academy, etc.) per chapter.

    This agent demonstrates tool-use: it calls our search service, which on Cloud
    Run uses Gemini with Google Search Grounding, and locally uses DuckDuckGo.
    """
    logger.info("[3/7] Finding free learning resources for %d chapters", len(state.chapters))
    state.resources = find_all_resources(state.chapters, state.exam)
    state.current_step = 3
    logger.info("[3/7] Done — %d resources curated", len(state.resources))
    return state
