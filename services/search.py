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
        {"title": "Laws of Motion One Shot | Vedantu JEE", "url": "https://www.youtube.com/watch?v=vdDKPx3e3lU", "platform": "youtube", "teacher": "Vedantu JEE", "why": "Complete chapter one-shot with PYQs and numerical problems."},
    ],
    "work energy power": [
        {"title": "Work, Energy, Power in One Shot | Physics Wallah", "url": "https://www.youtube.com/watch?v=8aGPtYcN_vY", "platform": "youtube", "teacher": "Physics Wallah", "why": "Work-energy theorem, conservative forces, collisions, PYQs."},
    ],
    "work, energy": [
        {"title": "Work, Energy, Power in One Shot | Physics Wallah", "url": "https://www.youtube.com/watch?v=8aGPtYcN_vY", "platform": "youtube", "teacher": "Physics Wallah", "why": "Work-energy theorem, conservative forces, collisions, PYQs."},
    ],
    "gravitation": [
        {"title": "Gravitation Full Chapter | Vedantu JEE", "url": "https://www.youtube.com/watch?v=p_G5cF3Q6Vw", "platform": "youtube", "teacher": "Vedantu JEE", "why": "Universal law, g variation, orbital motion, satellites, escape velocity."},
        {"title": "Gravitation One Shot | Physics Wallah", "url": "https://www.youtube.com/watch?v=QIJhS4RjG5w", "platform": "youtube", "teacher": "Physics Wallah", "why": "Complete gravitation for JEE/NEET."},
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
    "emi": [
        {"title": "EMI & Alternating Current | Physics Wallah", "url": "https://www.youtube.com/watch?v=ZJoQDcX4xIc", "platform": "youtube", "teacher": "Physics Wallah", "why": "Faraday's law, Lenz law, AC circuits, transformers."},
    ],
    "optics": [
        {"title": "Ray Optics + Wave Optics in One Shot | Physics Wallah", "url": "https://www.youtube.com/watch?v=7Gd80Jx5e0A", "platform": "youtube", "teacher": "Physics Wallah", "why": "Mirrors, lenses, interference, diffraction, YDSE."},
    ],
    "modern physics": [
        {"title": "Modern Physics Full Chapter | Physics Wallah", "url": "https://www.youtube.com/watch?v=G_6z-uYdJq4", "platform": "youtube", "teacher": "Physics Wallah", "why": "Photoelectric effect, Bohr model, radioactivity, semiconductors."},
    ],
    "rotational motion": [
        {"title": "Rotational Motion One Shot | Physics Wallah", "url": "https://www.youtube.com/watch?v=eIcaAbfT7Ns", "platform": "youtube", "teacher": "Physics Wallah", "why": "Moment of inertia, torque, angular momentum, rolling motion."},
    ],
    "oscillations": [
        {"title": "SHM & Oscillations | Physics Wallah", "url": "https://www.youtube.com/watch?v=vPkEw4o4D-c", "platform": "youtube", "teacher": "Physics Wallah", "why": "Simple harmonic motion, pendulum, spring systems, damping."},
    ],
    "waves": [
        {"title": "Waves Full Chapter | Physics Wallah", "url": "https://www.youtube.com/watch?v=Rq67L6S2FJo", "platform": "youtube", "teacher": "Physics Wallah", "why": "Wave equation, superposition, beats, Doppler effect."},
    ],
    # Chemistry
    "organic chemistry": [
        {"title": "Organic Chemistry Complete | Physics Wallah", "url": "https://www.youtube.com/playlist?list=PLPYdKM_G9b1n3sP2Z8J7XZbK2fQ9mYxQv", "platform": "youtube", "teacher": "Physics Wallah", "why": "GOC, isomerism, hydrocarbons, all named reactions."},
    ],
    "chemical bonding": [
        {"title": "Chemical Bonding One Shot | Physics Wallah", "url": "https://www.youtube.com/watch?v=P3iAXKb6uTk", "platform": "youtube", "teacher": "Physics Wallah", "why": "Ionic, covalent, VBT, VSEPR, hybridization, MOT."},
    ],
    # Biology
    "cell biology": [
        {"title": "Cell Biology One Shot | Physics Wallah", "url": "https://www.youtube.com/watch?v=3c4yNq7vYxU", "platform": "youtube", "teacher": "Physics Wallah", "why": "Cell structure, organelles, cell division for NEET."},
    ],
    "human physiology": [
        {"title": "Human Physiology Complete | Physics Wallah", "url": "https://www.youtube.com/playlist?list=PLPYdKM_G9b1lz6hQk2C5i5zLg0i7rRfZ7", "platform": "youtube", "teacher": "Physics Wallah", "why": "All human systems for NEET."},
    ],
    "genetics": [
        {"title": "Genetics One Shot | Physics Wallah", "url": "https://www.youtube.com/watch?v=kPw5GQ7dRqk", "platform": "youtube", "teacher": "Physics Wallah", "why": "Mendel, inheritance, DNA replication for NEET."},
    ],
    "plant physiology": [
        {"title": "Plant Physiology | Physics Wallah", "url": "https://www.youtube.com/watch?v=2JmWz0a3jFE", "platform": "youtube", "teacher": "Physics Wallah", "why": "Photosynthesis, respiration, plant hormones, transport."},
    ],
    "ecology": [
        {"title": "Ecology One Shot | Physics Wallah", "url": "https://www.youtube.com/watch?v=TvMh3h_8JvM", "platform": "youtube", "teacher": "Physics Wallah", "why": "Ecosystems, biodiversity, conservation for NEET."},
    ],
    # Math
    "calculus": [
        {"title": "Calculus Full Course | Mohit Tyagi", "url": "https://www.youtube.com/playlist?list=PLuGyQ5WmWbdF9V4B3vZq7fXJ2yY8qDc9E", "platform": "youtube", "teacher": "Mohit Tyagi", "why": "Limits, continuity, differentiability, integration, differential equations."},
    ],
    "trigonometry": [
        {"title": "Trigonometry One Shot | Physics Wallah", "url": "https://www.youtube.com/watch?v=J0-sj_0l8L0", "platform": "youtube", "teacher": "Physics Wallah", "why": "Identities, equations, properties of triangles for JEE."},
    ],
    "vectors": [
        {"title": "Vectors & 3D Geometry | Physics Wallah", "url": "https://www.youtube.com/watch?v=uXwT3s3TQL8", "platform": "youtube", "teacher": "Physics Wallah", "why": "Vectors, 3D geometry, dot/cross product for JEE Mains."},
    ],
    "probability": [
        {"title": "Probability One Shot | Physics Wallah", "url": "https://www.youtube.com/watch?v=j3Q7B4mZ9T8", "platform": "youtube", "teacher": "Physics Wallah", "why": "Classical, conditional probability, Bayes theorem for JEE."},
    ],
    "matrices": [
        {"title": "Matrices & Determinants | Physics Wallah", "url": "https://www.youtube.com/watch?v=gH4xG8XQ2h0", "platform": "youtube", "teacher": "Physics Wallah", "why": "Matrix operations, determinants, properties for JEE."},
    ],
    # UPSC
    "indian polity": [
        {"title": "Indian Polity Complete | Khan GS Research Centre", "url": "https://www.youtube.com/results?search_query=indian+polity+one+shot+upsc+lecture", "platform": "youtube", "teacher": "Khan Sir / StudyIQ", "why": "Constitution, Parliament, Judiciary, Panchayati Raj for UPSC Prelims."},
    ],
    "indian economy": [
        {"title": "Indian Economy for UPSC | Study IQ", "url": "https://www.youtube.com/results?search_query=indian+economy+upsc+prelims+one+shot+lecture", "platform": "youtube", "teacher": "Study IQ / Mrunal Patel", "why": "Planning, Budget, RBI, key economic concepts for UPSC."},
    ],
    "modern indian history": [
        {"title": "Modern Indian History | Study IQ", "url": "https://www.youtube.com/results?search_query=modern+indian+history+1857+1947+upsc+one+shot", "platform": "youtube", "teacher": "Study IQ", "why": "1857-1947 freedom struggle for UPSC Prelims."},
    ],
    "indian geography": [
        {"title": "Indian Geography for UPSC | Amit Sengupta", "url": "https://www.youtube.com/results?search_query=indian+geography+upsc+prelims+one+shot+lecture", "platform": "youtube", "teacher": "Amit Sengupta / Study IQ", "why": "Physical, economic, social geography of India for UPSC."},
    ],
    "environment": [
        {"title": "Environment & Ecology for UPSC", "url": "https://www.youtube.com/results?search_query=environment+ecology+upsc+prelims+one+shot", "platform": "youtube", "teacher": "Study IQ", "why": "Environment, biodiversity, climate change for UPSC."},
    ],
}


def _match_curated(chapter_title: str) -> List[dict]:
    """Return curated resources if the chapter title matches known topics.

    Uses substring matching but requires MULTIPLE key terms to match to avoid
    false positives (e.g., "laws" alone shouldn't match; "laws of motion" should).
    """
    title_lower = chapter_title.lower()
    # Normalize punctuation
    import re
    title_clean = re.sub(r'[^a-z0-9 ]+', ' ', title_lower)
    title_words = set(title_clean.split())
    matched = []
    matched_urls = set()
    for keyword, resources in CURATED_RESOURCES.items():
        kw_words = [w for w in keyword.split() if len(w) > 2]
        if not kw_words:
            continue
        # Require: either the full keyword phrase appears, or at least half
        # of the significant words appear in the title
        phrase_match = keyword in title_lower or keyword in title_clean
        if not phrase_match:
            hits = sum(1 for w in kw_words if w in title_words)
            if hits < max(1, len(kw_words) - (1 if len(kw_words) > 2 else 0)):
                continue
        for r in resources:
            if r["url"] not in matched_urls:
                matched.append(r)
                matched_urls.add(r["url"])
        if len(matched) >= 2:
            break
    return matched[:3]


def _ddg_search(query: str, max_results: int = 3) -> List[dict]:
    """Run a DuckDuckGo search and return results as dicts. Tries video search first for video queries."""
    try:
        from duckduckgo_search import DDGS
        results = []
        with DDGS() as ddgs:
            # If query targets videos, use video search
            if 'youtube' in query.lower() or 'lecture' in query.lower() or 'video' in query.lower() or 'one shot' in query.lower():
                try:
                    for hit in ddgs.videos(query, max_results=max_results):
                        url = hit.get("href", "") or hit.get("content", "")
                        title = hit.get("title", "")
                        body = hit.get("description", "")
                        channel = hit.get("uploader", "") or hit.get("channel", "")
                        platform = "youtube" if "youtube" in url or "youtu.be" in url else "video"
                        results.append({
                            "title": title,
                            "url": url,
                            "platform": platform,
                            "teacher": channel,
                            "why": (body or f"Video lecture on {query[:80]}")[:200],
                        })
                except Exception as e:
                    logger.debug(f"DDG video search failed, falling back to text: {e}")
            if not results:
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
                        if "|" in title:
                            teacher = title.split("|")[-1].strip()
                    elif platform in ("khanacademy","vedantu","nptel","pw"):
                        teacher = platform.title()
                    results.append({
                        "title": title,
                        "url": url,
                        "platform": platform,
                        "teacher": teacher,
                        "why": body[:200] if body else f"Resource for: {query[:80]}",
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


def _is_relevant(chapter_title: str, url: str, hit_title: str) -> bool:
    """Check that a search result is actually about the chapter topic.

    DDG sometimes returns tangentially related videos (e.g. "electrostatics"
    when searching "work, energy, power"). We require at least one significant
    word from the chapter title to appear in the hit title.
    """
    import re
    stop_words = {"the","a","an","of","in","on","at","to","for","and","or",
                  "with","by","from","class","jee","neet","one","shot",
                  "full","chapter","physics","biology","chemistry","maths",
                  "lecture","crash","course"}
    def sig_words(s: str) -> set:
        s = re.sub(r'[^a-z0-9 ]+', ' ', s.lower())
        return {w for w in s.split() if len(w) > 3 and w not in stop_words}
    ch_words = sig_words(chapter_title)
    hit_words = sig_words(hit_title.lower() + " " + url.lower())
    if not ch_words:
        return True
    # Must share at least one significant word with chapter title
    overlap = ch_words & hit_words
    return len(overlap) >= 1


def _is_educator_resource(url: str, title: str) -> bool:
    """Heuristic: is this a video/lecture from a known educator platform?

    Prefers YouTube videos from Indian educators, Khan Academy, NPTEL, Vedantu.
    Rejects Wikipedia, dictionary/legal/spam pages.
    """
    url_l = url.lower()
    title_l = title.lower()
    bad_domains = ("wikipedia.org", "wikibooks.org", "pinterest", "facebook",
                   "instagram", "quora.com", "scribd.com", "coursehero",
                   "chegg.com", "merriam-webster", "dictionary.com",
                   "justia.com", "usajobs", "usa.gov", "linkedin.com",
                   "amazon.", "flipkart", "indeed.com")
    for b in bad_domains:
        if b in url_l:
            return False
    # Good domains
    video_platforms = ("youtube.com", "youtu.be", "khanacademy.org", "nptel",
                       "vedantu.com", "physicswallah", "pw.live", "unacademy",
                       "mohittyagi", "byjus.com")
    if any(v in url_l for v in video_platforms):
        return True
    # Educator name in title
    educator_names = ("physics wallah", "alakh pandey", "vedantu", "khan academy",
                      "mohit tyagi", "unacademy", "nptel", "gb sir", "vani ma'am",
                      "one shot", "lecture", "tutorial", "ncert", "pyq", "revision")
    if any(e in title_l for e in educator_names):
        return True
    return False


def find_resources_for_chapter(chapter: Chapter, exam: str) -> List[Resource]:
    """Find 1-3 best free resources for a chapter. Never returns empty."""
    resources: List[Resource] = []

    # 0. FIRST: check curated database for well-known topics (highest quality)
    curated = _match_curated(chapter.title)
    for c in curated:
        if not any(r.url == c["url"] for r in resources):
            resources.append(Resource(chapter=chapter.title, **c))

    # 1. Try cloud search (if running on GCP)
    if settings.is_cloud and settings.google_cloud_project:
        cloud = _cloud_search(chapter, exam)
        for r in cloud:
            if not any(existing.url == r.url for existing in resources):
                resources.append(r)

    # 2. Try DuckDuckGo with YouTube-specific queries for educator videos
    if len(resources) < 2:
        queries = [
            f'site:youtube.com "{chapter.title}" one shot {exam} physics wallah OR vedantu OR unacademy',
            f'{chapter.title} {exam} one shot lecture youtube physics wallah',
            f'{chapter.title} class 11 JEE NEET youtube lecture',
        ]
        for q in queries:
            if len(resources) >= 2:
                break
            for hit in _ddg_search(q, max_results=3):
                url = hit.get("url", "")
                if not url or any(r.url == url for r in resources):
                    continue
                if any(bad in url for bad in ["pinterest","facebook","instagram","quora.com","wikipedia.org","chegg","scribd","merriam-webster","justia","usa.gov"]):
                    continue
                if not _is_educator_resource(url, hit.get("title","")):
                    continue
                if not _is_relevant(chapter.title, url, hit.get("title","")):
                    continue
                resources.append(Resource(
                    chapter=chapter.title,
                    title=hit["title"][:140],
                    url=url,
                    platform=hit["platform"],
                    teacher_or_channel=hit["teacher"],
                    why=hit["why"][:200],
                ))

    # 3. DDG without site: filter as last resort, but still filter
    if len(resources) < 2:
        for hit in _ddg_search(f'{chapter.title} {exam} free lecture video', max_results=3):
            url = hit.get("url","")
            if not url or any(r.url == url for r in resources):
                continue
            if any(bad in url for bad in ["pinterest","facebook","instagram","quora.com","wikipedia.org","chegg","scribd","merriam-webster","justia"]):
                continue
            if not _is_educator_resource(url, hit.get("title","")):
                continue
            if not _is_relevant(chapter.title, url, hit.get("title","")):
                continue
            resources.append(Resource(
                chapter=chapter.title,
                title=hit["title"][:140],
                url=url,
                platform=hit["platform"],
                teacher_or_channel=hit["teacher"],
                why=hit["why"][:200],
            ))

    # 4. Ultimate fallback: YouTube search page
    if len(resources) < 1:
        topic_q = urllib.parse.quote_plus(f"{chapter.title} {exam} one shot physics wallah")
        resources.append(Resource(
            chapter=chapter.title,
            title=f"YouTube: {chapter.title} lectures for {exam}",
            url=f"https://www.youtube.com/results?search_query={topic_q}",
            platform="youtube",
            teacher_or_channel="YouTube search",
            why="Find the best lecture that matches your learning style.",
        ))

    return resources[:3]


def find_all_resources(chapters: List[Chapter], exam: str) -> List[Resource]:
    """Find resources for all chapters."""
    all_r: List[Resource] = []
    for ch in chapters:
        ch_resources = find_resources_for_chapter(ch, exam)
        all_r.extend(ch_resources)
        logger.info(f"  Found {len(ch_resources)} resources for: {ch.title}")
    return all_r
