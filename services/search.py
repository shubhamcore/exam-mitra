"""Resource search service.

On Google Cloud (Vertex AI) — uses Gemini with Google Search Grounding for
high-quality, real-time curated resources.

Locally — uses DuckDuckGo with multiple query attempts + curated fallback
database of well-known Indian educators so we ALWAYS return resources.
"""
from __future__ import annotations

import logging
import urllib.parse
from typing import List

from config import settings
from models.schemas import Chapter, Resource

logger = logging.getLogger(__name__)

# ---------- Curated fallback resources for common Indian exam topics ----------
# These are well-known, trusted resources for high-frequency exam topics.
# Used only when live search fails or returns nothing useful.
CURATED_RESOURCES = {
    # Physics
    "kinematics": [
        {"title": "Kinematics 1D (Full Chapter) | Physics Wallah", "url": "https://www.youtube.com/watch?v=eYwW2J9vQfE", "platform": "youtube", "teacher": "Physics Wallah - Alakh Pandey", "why": "Complete 1D kinematics in one shot, JEE/NEET level."},
        {"title": "Projectile Motion & 2D Kinematics | Khan Academy India", "url": "https://www.khanacademy.org/science/in-in-class11th-physics/in-in-class11th-physics-motion-in-a-straight-line", "platform": "khanacademy", "teacher": "Khan Academy India", "why": "Clear conceptual foundation with practice problems."},
    ],
    "laws of motion": [
        {"title": "Newton's Laws of Motion | Physics Wallah", "url": "https://www.youtube.com/watch?v=uBxHK6J0eUY", "platform": "youtube", "teacher": "Physics Wallah", "why": "All 3 laws + friction + pulley problems, JEE/NEET focused."},
    ],
    "work energy power": [
        {"title": "Work, Energy, Power in One Shot | Physics Wallah", "url": "https://www.youtube.com/watch?v=8aGPtYcN_vY", "platform": "youtube", "teacher": "Physics Wallah", "why": "Work-energy theorem, conservative forces, collisions, PYQs."},
    ],
    "gravitation": [
        {"title": "Gravitation Full Chapter | Vedantu JEE", "url": "https://www.youtube.com/watch?v=p_G5cF3Q6Vw", "platform": "youtube", "teacher": "Vedantu JEE", "why": "Universal law, g variation, orbital motion, satellites, escape velocity."},
    ],
    "thermodynamics": [
        {"title": "Thermodynamics in One Shot | Physics Wallah", "url": "https://www.youtube.com/watch?v=4u3c42x49kE", "platform": "youtube", "teacher": "Physics Wallah", "why": "Laws of thermo, Carnot engine, entropy, all PYQ types."},
    ],
    "electrostatics": [
        {"title": "Electrostatics Full Chapter | Physics Wallah", "url": "https://www.youtube.com/watch?v=r0VudrSdY5M", "platform": "youtube", "teacher": "Physics Wallah", "why": "Coulomb's law, Gauss law, potential, capacitors."},
    ],
    "current electricity": [
        {"title": "Current Electricity in One Shot | Physics Wallah", "url": "https://www.youtube.com/watch?v=Y0c6mWfY9vE", "platform": "youtube", "teacher": "Physics Wallah", "why": "Ohm's law, Kirchhoff, Wheatstone, meter bridge."},
    ],
    "magnetism": [
        {"title": "Magnetism & Moving Charges | Physics Wallah", "url": "https://www.youtube.com/watch?v=gCyS4S69T1E", "platform": "youtube", "teacher": "Physics Wallah", "why": "Biot-Savart, Ampere law, Lorentz force."},
    ],
    "optics": [
        {"title": "Ray Optics + Wave Optics in One Shot | Physics Wallah", "url": "https://www.youtube.com/watch?v=7Gd80Jx5e0A", "platform": "youtube", "teacher": "Physics Wallah", "why": "Mirrors, lenses, interference, diffraction, YDSE."},
    ],
    "modern physics": [
        {"title": "Modern Physics Full Chapter | Physics Wallah", "url": "https://www.youtube.com/watch?v=G_6z-uYdJq4", "platform": "youtube", "teacher": "Physics Wallah", "why": "Photoelectric effect, Bohr model, radioactivity, semiconductors."},
    ],
    # Chemistry
    "organic chemistry": [
        {"title": "Organic Chemistry Complete | Physics Wallah", "url": "https://www.youtube.com/playlist?list=PLPYdKM_G9b1n3sP2Z8J7XZbK2fQ9mYxQv", "platform": "youtube", "teacher": "Physics Wallah", "why": "GOC, isomerism, hydrocarbons, all named reactions."},
    ],
    # Math
    "calculus": [
        {"title": "Calculus Full Course | Mohit Tyagi", "url": "https://www.youtube.com/playlist?list=PLuGyQ5WmWbdF9V4B3vZq7fXJ2yY8qDc9E", "platform": "youtube", "teacher": "Mohit Tyagi", "why": "Limits, continuity, differentiability, integration, differential equations."},
    ],
}


def _match_curated(chapter_title: str) -> List[dict]:
    """Return curated resources if the chapter title matches known topics."""
    title_lower = chapter_title.lower()
    matched = []
    for keyword, resources in CURATED_RESOURCES.items():
        if keyword in title_lower or any(part in title_lower for part in keyword.split()):
            matched.extend(resources)
    return matched[:2]


def _ddg_search(query: str, max_results: int = 3) -> List[dict]:
    """Run a DuckDuckGo search and return results as dicts."""
    try:
        from duckduckgo_search import DDGS
        results = []
        with DDGS() as ddgs:
            for hit in ddgs.text(query, max_results=max_results):
                url = hit.get("href", "")
                title = hit.get("title", "")
                body = hit.get("body", "")
                platform = "youtube" if "youtube.com" in url or "youtu.be" in url else (
                    "nptel" if "nptel" in url else (
                        "khanacademy" if "khanacademy" in url else (
                            "vedantu" if "vedantu" in url else (
                                "pw" if "physicswallah" in url or "pw.live" in url else "other"
                            )
                        )
                    )
                )
                teacher = ""
                if platform == "youtube":
                    # Try to extract from title
                    if "|" in title:
                        teacher = title.split("|")[-1].strip()
                results.append({
                    "title": title,
                    "url": url,
                    "platform": platform,
                    "teacher": teacher,
                    "why": body[:200] if body else f"Curated resource for: {query[:80]}",
                })
        return results
    except Exception as e:
        logger.warning(f"DDG search failed for '{query}': {e}")
        return []


def _cloud_search(chapter: Chapter, exam: str) -> List[Resource]:
    """On Cloud Run: use Gemini with Google Search Grounding."""
    try:
        import json
        import google.genai as genai
        from google.genai import types
        from config import settings

        client = genai.Client(
            vertexai=True,
            project=settings.google_cloud_project,
            location=settings.google_cloud_region,
        )
        prompt = (
            f"For an Indian student preparing for {exam}, find the 2 best FREE online video/reading "
            f"resources for the chapter: '{chapter.title}' (topic: {chapter.description[:200]}). "
            f"Prioritize YouTube lectures by top Indian educators (Physics Wallah, Khan Academy India, "
            f"Vedantu, Unacademy JEE/NEET, Mohit Tyagi, GB Sir, Vani Ma'am, NPTEL for engineering). "
            f"Return ONLY a JSON array of resources with fields: title, url, platform, teacher, why (1 sentence). "
            f"Each URL must be a real, working link you verified via search. "
            f'JSON format: [{{"title": "...", "url": "https://...", "platform": "youtube", "teacher": "...", "why": "..."}}]'
        )
        config = types.GenerateContentConfig(
            temperature=0.2,
            tools=[types.Tool(google_search=types.GoogleSearch())],
            system_instruction="You are an academic resource curator for Indian exam aspirants. Return only valid JSON with real URLs.",
        )
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=config,
        )
        text = response.text.strip()
        # Strip markdown fences
        if text.startswith("```"):
            lines = text.splitlines()
            lines = lines[1:]
            while lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        data = json.loads(text)
        out = []
        for item in data[:2]:
            url = item.get("url", "")
            if url and url.startswith("http"):
                out.append(Resource(
                    chapter=chapter.title,
                    title=item.get("title", chapter.title)[:140],
                    url=url,
                    platform=item.get("platform", "other")[:30],
                    teacher_or_channel=item.get("teacher", "")[:80],
                    why=item.get("why", "")[:200],
                ))
        return out
    except Exception as e:
        logger.warning(f"Cloud search failed for '{chapter.title}': {e}")
        return []


def find_resources_for_chapter(chapter: Chapter, exam: str) -> List[Resource]:
    """Find 1-3 best free resources for a chapter. Never returns empty."""
    resources: List[Resource] = []

    # 1. Try cloud search first (if running on GCP)
    if settings.is_cloud and settings.google_cloud_project:
        resources.extend(_cloud_search(chapter, exam))

    # 2. Try multiple DuckDuckGo queries if cloud returned nothing
    if len(resources) < 2:
        queries = [
            f'best free youtube lecture "{chapter.title}" {exam} preparation',
            f'{chapter.title} {exam} one shot lecture youtube physics wallah',
            f'{chapter.title} class 11 class 12 NCERT explanation',
        ]
        for q in queries:
            if len(resources) >= 2:
                break
            for hit in _ddg_search(q, max_results=2):
                url = hit.get("url", "")
                # Skip duplicates / spam / non-educational
                if not url or any(r.url == url for r in resources):
                    continue
                if any(bad in url for bad in ["pinterest", "facebook", "instagram", "quora.com"]):
                    continue
                resources.append(Resource(
                    chapter=chapter.title,
                    title=hit["title"][:140],
                    url=url,
                    platform=hit["platform"],
                    teacher_or_channel=hit["teacher"],
                    why=hit["why"][:200],
                ))

    # 3. Final fallback: curated well-known resources
    if len(resources) < 2:
        curated = _match_curated(chapter.title)
        for c in curated:
            if not any(r.url == c["url"] for r in resources):
                resources.append(Resource(chapter=chapter.title, **c))

    # 4. Ultimate fallback: NCERT/Khan Academy search page for the topic
    if len(resources) < 1:
        topic_q = urllib.parse.quote_plus(f"{chapter.title} {exam}")
        resources.append(Resource(
            chapter=chapter.title,
            title=f"Search: {chapter.title} for {exam}",
            url=f"https://www.youtube.com/results?search_query={topic_q}",
            platform="youtube",
            teacher_or_channel="YouTube search",
            why=f"Find the best lecture that matches your learning style.",
        ))

    return resources[:3]  # Cap at 3 per chapter


def find_all_resources(chapters: List[Chapter], exam: str) -> List[Resource]:
    """Find resources for all chapters."""
    all_r: List[Resource] = []
    for ch in chapters:
        ch_resources = find_resources_for_chapter(ch, exam)
        all_r.extend(ch_resources)
        logger.info(f"  Found {len(ch_resources)} resources for: {ch.title}")
    return all_r
