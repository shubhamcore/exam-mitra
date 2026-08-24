"""Exam Mitra — FastAPI backend.

Endpoints:
  GET  /                     -> static UI
  GET  /api/health           -> health check
  POST /api/start            -> submit a syllabus, starts async job, returns job_id immediately
  GET  /api/jobs/{id}        -> get job status + completed results
  GET  /api/jobs/{id}/stream -> SSE stream of real-time progress events
  POST /api/jobs/{id}/grade  -> grade submitted MCQ answers
  GET  /plan/{id}            -> shareable public plan page (renders pre-computed plan)
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from collections import defaultdict, deque
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Dict, List, Deque

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import (
    FileResponse, HTMLResponse, JSONResponse, Response, StreamingResponse,
)
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel, Field

from config import settings, STATIC_DIR, TEMPLATES_DIR
from models.schemas import StudyPackage, StudyPlanState
from services.db import store

# Agents
from agents import (
    parse_syllabus, plan_study, gather_resources, generate_content, grade_answers,
    build_remediation, ask_tutor,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("exam_mitra")

app = FastAPI(title="Exam Mitra 📚", version="2.2.0")

# ---------- Security middleware ----------

# Simple in-memory rate limiter (resets on cold-start; fine for a single Cloud Run instance)
_RATE_LIMITS = {
    "/api/start": (5, 60),        # 5 plans per minute per IP
    "/api/jobs/":  (60, 60),      # 60 reads/min
    "/api/health": (120, 60),
}
_rate_buckets: Dict[str, Dict[str, Deque[float]]] = defaultdict(lambda: defaultdict(deque))


def _client_ip(request: Request) -> str:
    # Cloud Run sets X-Forwarded-For
    xff = request.headers.get("x-forwarded-for", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _rate_limited(ip: str, path: str) -> bool:
    for prefix, (max_hits, window) in _RATE_LIMITS.items():
        if path.startswith(prefix):
            bucket = _rate_buckets[ip][prefix]
            now = time.monotonic()
            while bucket and now - bucket[0] > window:
                bucket.popleft()
            if len(bucket) >= max_hits:
                return True
            bucket.append(now)
            return False
    return False


@app.middleware("http")
async def security_middleware(request: Request, call_next):
    ip = _client_ip(request)
    # Rate limit
    if _rate_limited(ip, request.url.path):
        return JSONResponse({"error": "Too many requests. Please slow down."}, status_code=429)

    # Process request
    try:
        response = await call_next(request)
    except Exception as exc:
        # Never leak stack traces to users
        logger.exception("Unhandled error on %s: %s", request.url.path, exc)
        return JSONResponse(
            {"error": "Internal server error", "detail": "Something went wrong. Please try again."},
            status_code=500,
        )

    # Security headers (effective on HTML/API responses)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    # Only enable HSTS in production (cloud)
    if settings.is_cloud:
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    # CSP: own origin + Google Fonts + KaTeX CDN for math rendering
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
        "font-src https://fonts.gstatic.com https://cdn.jsdelivr.net data:; "
        "img-src 'self' data: https:; "
        "connect-src 'self'; "
        "frame-ancestors 'none'",
    )
    return response

# ---------- In-memory job queues & SSE subscribers ----------

# Active jobs currently running (job_id -> state)
running_jobs: Dict[str, StudyPlanState] = {}
# Per-job event queues for SSE subscribers: job_id -> list of asyncio.Queue
job_subscribers: Dict[str, List[asyncio.Queue]] = {}
# Background tasks
job_tasks: Dict[str, asyncio.Task] = {}
# Track which IP owns which job (for per-IP concurrency limit)
job_owner_ip: Dict[str, str] = {}


# ---------- Request models ----------

class StartRequest(BaseModel):
    exam: str = Field(..., min_length=2, max_length=200)
    syllabus: str = Field(..., min_length=1, max_length=10000)
    daily_hours: float = Field(4.0, ge=0.5, le=16)
    start_date: str | None = None
    language: str = Field("en", pattern="^(en|hi|hinglish)$")


class GradeRequest(BaseModel):
    answers: Dict[str, str]


class RemediateRequest(BaseModel):
    """After grading, frontend sends the weak areas + score and we build a remediation package."""
    score: int = Field(..., ge=0)
    total: int = Field(..., ge=1)
    weak_areas: List[dict] = Field(default_factory=list)


class TutorRequest(BaseModel):
    """Ask the in-context tutor a question."""
    question: str = Field(..., min_length=2, max_length=2000)
    chapter: str = Field("", max_length=200)
    history: List[str] = Field(default_factory=list)


# Remediation packages per job, keyed by round number (1 = first remediation, etc.)
# Stored in-memory only (share page doesn't need them; persistence via Firestore is fine as bonus later).
_remediations: Dict[str, List[dict]] = defaultdict(list)


# ---------- Background job runner ----------

STEP_NAMES = {
    0: "Queued",
    1: "Parsing syllabus into chapters",
    2: "Building your day-by-day study plan",
    3: "Finding the best free video lectures",
    4: "Writing revision notes for every chapter",
    5: "Creating active-recall flashcards",
    6: "Generating practice MCQs with explanations",
    7: "Finalizing your study package",
}


async def broadcast(job_id: str, event: str, data: dict):
    """Send an SSE event to every subscriber of a job."""
    if job_id not in job_subscribers:
        return
    msg = {"event": event, **data}
    for q in list(job_subscribers[job_id]):
        try:
            q.put_nowait(msg)
        except asyncio.QueueFull:
            pass


async def run_pipeline_async(job_id: str, state: StudyPlanState):
    """Run the 7-step agent pipeline asynchronously, broadcasting progress."""
    steps = [
        (parse_syllabus, 1, "Syllabus parsed"),
        (plan_study, 2, "Study plan built"),
        (gather_resources, 3, "Resources curated"),
        (generate_content, 6, "Notes, flashcards, MCQs generated"),  # steps 4-6 combined
    ]
    try:
        for step_fn, step_num, progress_msg in steps:
            await broadcast(job_id, "progress", {
                "step": step_num if step_num != 6 else 4,
                "message": STEP_NAMES.get(step_num if step_num != 6 else 4, "Working..."),
            })
            # Run synchronous agent in thread pool (ADK is sync)
            loop = asyncio.get_running_loop()
            state = await loop.run_in_executor(None, step_fn, state)
            await broadcast(job_id, "step_complete", {
                "step": state.current_step,
                "message": progress_msg,
                "chapters": len(state.chapters),
                "days": len(state.daily_plan),
                "resources": len(state.resources),
                "notes": len(state.notes),
                "flashcards": len(state.flashcards),
                "mcqs": len(state.mcqs),
            })
            store.save(state)
        state.current_step = 7
        store.save(state)
        await broadcast(job_id, "complete", {
            "step": 7,
            "message": "Your study package is ready!",
            "chapters": len(state.chapters),
            "days": len(state.daily_plan),
            "resources": len(state.resources),
            "notes": len(state.notes),
            "flashcards": len(state.flashcards),
            "mcqs": len(state.mcqs),
        })
    except Exception as e:
        logger.exception(f"Pipeline failed for job {job_id}")
        state.error = f"Failed: {e}"
        store.save(state)
        await broadcast(job_id, "error", {"step": state.current_step, "message": str(e)})
    finally:
        running_jobs.pop(job_id, None)
        job_tasks.pop(job_id, None)
        job_owner_ip.pop(job_id, None)
        # Close subscriber queues after a short delay so last events are delivered
        await asyncio.sleep(2)
        for q in job_subscribers.pop(job_id, []):
            try:
                q.put_nowait({"event": "close"})
            except Exception:
                pass


# ---------- Public API ----------

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "environment": settings.environment,
        "gcp_project": settings.google_cloud_project or "(local)",
        "model": settings.gemini_model,
        "active_jobs": len(running_jobs),
    }


@app.post("/api/start")
async def start_job(req: StartRequest, request: Request):
    """Start a new study plan generation job. Returns immediately with job_id."""
    ip = _client_ip(request)
    # Limit concurrent expensive generations per IP to 2 (prevent quota-burning)
    active_for_ip = sum(1 for jid, j in running_jobs.items()
                        if job_owner_ip.get(jid) == ip and not j.error)
    if active_for_ip >= 2:
        raise HTTPException(429, "You already have a plan generating. Please wait for it to finish.")

    job_id = uuid.uuid4().hex[:10]
    start_date = None
    if req.start_date:
        try:
            start_date = date.fromisoformat(req.start_date)
        except ValueError:
            raise HTTPException(400, "start_date must be YYYY-MM-DD")

    state = StudyPlanState(
        job_id=job_id,
        exam=req.exam.strip(),
        syllabus_text=req.syllabus.strip(),
        daily_hours_budget=req.daily_hours,
        start_date=start_date,
        language=req.language,
    )
    store.save(state)
    running_jobs[job_id] = state
    job_subscribers[job_id] = []
    job_owner_ip[job_id] = ip

    # Launch pipeline in background
    task = asyncio.create_task(run_pipeline_async(job_id, state))
    job_tasks[job_id] = task

    return {"job_id": job_id, "status": "started"}


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    """Get job status and (if complete) the full study package."""
    state = store.get(job_id)
    if not state:
        raise HTTPException(404, "Job not found")

    # Detect stale jobs (marked processing but not in running_jobs → server restarted mid-pipeline)
    is_running = job_id in running_jobs
    if not is_running and state.current_step < 7 and not state.error:
        state.error = ("This job was interrupted by a server restart. "
                       "Please generate a new plan — results take ~30-90 seconds.")
        store.save(state)

    resp = {
        "job_id": job_id,
        "status": "error" if state.error else ("complete" if state.current_step >= 7 else "processing"),
        "step": state.current_step,
        "step_message": STEP_NAMES.get(state.current_step, ""),
        "exam": state.exam,
        "chapters_count": len(state.chapters),
        "plan_days": len(state.daily_plan),
        "resources_count": len(state.resources),
        "notes_count": len(state.notes),
        "flashcards_count": len(state.flashcards),
        "mcqs_count": len(state.mcqs),
        "error": state.error,
        "package": None,
    }
    if state.current_step >= 7 and not state.error:
        resp["package"] = StudyPackage(
            exam=state.exam,
            total_chapters=len(state.chapters),
            total_days=len(state.daily_plan),
            total_hours=sum(d.hours for d in state.daily_plan),
            daily_plan=state.daily_plan,
            resources=state.resources,
            notes=state.notes,
            flashcards=state.flashcards,
            mcqs=state.mcqs,
        ).model_dump(mode="json")
    return resp


@app.get("/api/jobs/{job_id}/stream")
async def stream_job(job_id: str):
    """Server-Sent Events endpoint — pushes real-time progress updates."""
    state = store.get(job_id)
    if not state:
        raise HTTPException(404, "Job not found")

    async def event_generator():
        q: asyncio.Queue = asyncio.Queue(maxsize=32)
        job_subscribers.setdefault(job_id, []).append(q)
        try:
            # Detect stale jobs (not running + not complete + no error marked yet)
            is_running = job_id in running_jobs
            if not is_running and state.current_step < 7:
                state.error = ("This job was interrupted by a server restart. "
                               "Please generate a new plan — results take ~30-90 seconds.")
                store.save(state)
                yield f"data: {json.dumps({'event':'error','step':state.current_step,'message':state.error})}\n\n"
                yield f"data: {json.dumps({'event':'close'})}\n\n"
                return

            # Send initial state
            initial = {
                "event": "init",
                "step": state.current_step,
                "message": STEP_NAMES.get(state.current_step, "Starting..."),
                "chapters": len(state.chapters),
                "days": len(state.daily_plan),
                "resources": len(state.resources),
                "notes": len(state.notes),
                "flashcards": len(state.flashcards),
                "mcqs": len(state.mcqs),
                "status": "complete" if state.current_step >= 7 else (
                    "error" if state.error else "processing"),
            }
            yield f"data: {json.dumps(initial)}\n\n"

            # If already complete or errored, close immediately
            if state.current_step >= 7 and not state.error:
                yield f"data: {json.dumps({'event':'close'})}\n\n"
                return
            if state.error:
                yield f"data: {json.dumps({'event':'error','step':state.current_step,'message':state.error})}\n\n"
                yield f"data: {json.dumps({'event':'close'})}\n\n"
                return

            while True:
                try:
                    msg = await asyncio.wait_for(q.get(), timeout=30)
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield ": keepalive\n\n"
                    continue
                yield f"data: {json.dumps(msg, default=str)}\n\n"
                if msg.get("event") in ("complete", "error", "close"):
                    break
        finally:
            if job_id in job_subscribers:
                try:
                    job_subscribers[job_id].remove(q)
                except ValueError:
                    pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/jobs/{job_id}/grade")
def grade_job(job_id: str, req: GradeRequest):
    """Grade submitted MCQ answers."""
    state = store.get(job_id)
    if not state:
        raise HTTPException(404, "Job not found")
    if state.current_step < 6:
        raise HTTPException(400, "MCQs not yet generated for this job")

    result = grade_answers(state, req.answers)
    return {
        "score": result.score,
        "total": result.total,
        "percentage": result.percentage,
        "weak_areas": [w.model_dump() for w in result.weak_areas],
        "encouragement": result.encouragement,
    }


def _run_sync(fn, *args):
    """Run a sync agent call on the default threadpool so we don't block the event loop."""
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(fn, *args).result()


@app.post("/api/jobs/{job_id}/remediate")
async def remediate_job(job_id: str, req: RemediateRequest):
    """[Adaptive Tutor] Build a focused revision mini-plan + booster notes + extra MCQs for weak chapters.

    This is the CLOSED-LOOP wow feature: after the student tests and fails, the agent doesn't just
    say "try again" — it diagnoses root misconceptions and writes fresh, targeted content.
    """
    state = store.get(job_id)
    if not state:
        raise HTTPException(404, "Job not found")
    if state.current_step < 7:
        raise HTTPException(400, "Plan is not yet complete — finish generating first")

    from models.schemas import WeakArea
    weak_areas = [WeakArea(**w) for w in req.weak_areas]
    if not weak_areas:
        raise HTTPException(400, "No weak areas provided — you scored perfectly! 🎉")

    # Heavy LLM work goes to threadpool
    loop = asyncio.get_running_loop()
    pkg = await loop.run_in_executor(
        None,
        lambda: build_remediation(state, weak_areas, req.score, req.total),
    )
    dumped = pkg.model_dump(mode="json")
    _remediations[job_id].append(dumped)
    return {
        "round": len(_remediations[job_id]),
        **dumped,
    }


@app.get("/api/jobs/{job_id}/remediations")
def list_remediations(job_id: str):
    """Return all prior remediation rounds for this job (so refreshes/shares keep them)."""
    if not store.get(job_id):
        raise HTTPException(404, "Job not found")
    return {"rounds": _remediations.get(job_id, [])}


@app.post("/api/jobs/{job_id}/tutor")
async def tutor_chat(job_id: str, req: TutorRequest):
    """Ask the AI Tutor a free-text question about this study plan."""
    state = store.get(job_id)
    if not state:
        raise HTTPException(404, "Job not found")
    if state.current_step < 7:
        raise HTTPException(400, "Wait for plan to finish before asking the tutor")
    q = req.question.strip()
    if not q:
        raise HTTPException(400, "Empty question")

    loop = asyncio.get_running_loop()
    answer = await loop.run_in_executor(
        None,
        lambda: ask_tutor(state, q, req.chapter, req.history),
    )
    return {"answer": answer}


# ---------- Static UI + shareable plan page ----------

_jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=True,
)


def _render_plan(pkg: StudyPackage, plan_id: str) -> str:
    tmpl = _jinja_env.get_template("plan.html")
    return tmpl.render(pkg=pkg, plan_id=plan_id, static_url="/static")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/plan/{plan_id}", response_class=HTMLResponse)
async def shareable_plan(request: Request, plan_id: str):
    """Render a shareable public plan page."""
    state = store.get(plan_id)
    if not state or state.current_step < 7:
        return HTMLResponse(f"""
        <!doctype html><html><head><title>Exam Mitra — Plan not found</title>
        <style>body{{font-family:system-ui,sans-serif;display:grid;place-items:center;height:80vh;color:#333}}</style>
        </head><body><div style="text-align:center">
        <h1>📚 Exam Mitra</h1>
        <p>Plan not found or still generating. <a href="/">Create your own →</a></p>
        </div></body></html>""", status_code=404)

    pkg = StudyPackage(
        exam=state.exam,
        total_chapters=len(state.chapters),
        total_days=len(state.daily_plan),
        total_hours=sum(d.hours for d in state.daily_plan),
        daily_plan=state.daily_plan,
        resources=state.resources,
        notes=state.notes,
        flashcards=state.flashcards,
        mcqs=state.mcqs,
    )
    html = _render_plan(pkg, plan_id)
    return HTMLResponse(html)


@app.get("/plan/{plan_id}/print", response_class=HTMLResponse)
def printable_plan(request: Request, plan_id: str):
    """Printer-friendly version — users can Ctrl+P or Save as PDF."""
    state = store.get(plan_id)
    if not state or state.current_step < 7:
        return HTMLResponse("<h1>Plan not found</h1>", status_code=404)
    pkg = StudyPackage(
        exam=state.exam,
        total_chapters=len(state.chapters),
        total_days=len(state.daily_plan),
        total_hours=sum(d.hours for d in state.daily_plan),
        daily_plan=state.daily_plan,
        resources=state.resources,
        notes=state.notes,
        flashcards=state.flashcards,
        mcqs=state.mcqs,
    )
    tmpl = _jinja_env.get_template("print.html")
    html = tmpl.render(pkg=pkg, plan_id=plan_id)
    return HTMLResponse(html)


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=False)
