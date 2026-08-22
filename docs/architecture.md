# Architecture Overview

![Architecture Diagram](/static/architecture.svg)

## Why Exam Mitra is an *Agentic* System (not a chatbot)

The user submits a syllabus in **one click**. From there the system runs an **autonomous 7-step pipeline** of specialized sub-agents — each with its own system prompt, JSON output schema, retry policy, and model fallback — streams progress to the browser in real time over Server-Sent Events, and produces a complete shareable study package without further human prompting.

```
                       ┌──────────────────────────┐
                       │     Student Browser      │
                       │  (HTML/CSS/JS + SSE)     │
                       └────────────┬─────────────┘
                                    │ POST /api/start  (syllabus, exam, hours)
                                    ▼
┌────────────────────────────────────────────────────────────────────┐
│                      Cloud Run (FastAPI + Uvicorn)                 │
│                                                                    │
│   POST /api/start ─▶ creates job_id, launches run_pipeline_async   │
│   GET  /api/jobs/:id/stream ─▶ SSE real-time progress              │
│   GET  /api/jobs/:id ─▶ current state + final StudyPackage         │
│   POST /api/jobs/:id/grade ─▶ answer_grader agent (on demand)      │
│   GET  /plan/:id ─▶ Jinja2 server-rendered share page              │
│                                                                    │
│   Pipeline (runs in asyncio thread pool, ADK agents are sync):     │
│     1. syllabus_parser     → structured Chapter[]                  │
│     2. study_planner       → DailyTask[] with revision days        │
│     3. resource_finder     → curated + DuckDuckGo resources        │
│     4-6. content_generator → notes + flashcards + MCQs (batched)   │
│     7. answer_grader       → grade MCQ answers (post-practice)     │
│                                                                    │
│   After every step: broadcast SSE + persist state                  │
│                                                                    │
│   ┌───────────────────────────────────────────────────────────┐    │
│   │              Google ADK  (google-adk Python SDK)           │    │
│   │  LlmAgent + Runner + InMemorySessionService                │    │
│   │  • { curly braces } auto-escaped in instructions          │    │
│   │  • Exponential backoff + model fallback queue on 429/503   │    │
│   │  • 3-attempt JSON repair on parse failures                 │    │
│   └──────────────────────────┬────────────────────────────────┘    │
│                              │                                     │
│               ┌──────────────┴──────────────┐                      │
│               ▼                             ▼                      │
│     ┌──────────────────┐         ┌──────────────────────┐           │
│     │ Gemini 3.5 Flash │         │  Resource finder     │           │
│     │ (auto-fallback:  │         │  • Curated PW/Vedu/  │           │
│     │  flash-lite →    │         │    Khan/Mohit Tyagi  │           │
│     │  3.5-flash →     │         │  • DuckDuckGo multi- │           │
│     │  3.6-flash)      │         │    query strategies  │           │
│     │ Vertex on cloud, │         │  • Google Search     │           │
│     │ API key locally  │         │    Grounding (cloud) │           │
│     └────────┬─────────┘         └──────────┬───────────┘           │
│              │                              │                       │
│              ▼                              ▼                       │
│   ┌──────────────────────────────────────────────────────┐         │
│   │   Firestore (cloud)  /  JSON file (local dev)         │         │
│   │   - StudyPlanState persisted after every step         │         │
│   │   - Jobs resumable across cold starts                 │         │
│   └──────────────────────────────────────────────────────┘         │
└────────────────────────────────────────────────────────────────────┘
```

## Stack

| Concern        | Choice                                              | Why |
|----------------|-----------------------------------------------------|-----|
| Agent framework| **Google ADK** (`LlmAgent`, `Runner`)              | Hackathon requires ≥1 Google Agent Framework. Native structured outputs, session management, retry hooks. |
| LLM            | **Gemini 3.5 Flash-Lite** (primary) w/ fallback queue to 3.5 Flash / 3.6 Flash | Flash-Lite has higher RPM on the free tier; fallbacks handle 429/503/quota gracefully. |
| Backend        | **FastAPI + Uvicorn**                               | Async-native, SSE works cleanly, minimal overhead. |
| Real-time UX   | **Server-Sent Events (SSE)**                        | Simpler than websockets for one-way progress streams; works through proxies. |
| Frontend       | **Vanilla HTML/CSS/JS** (no build)                  | Zero compile step = fast deploys, Cloud Run friendly. Tabs, flip-cards, MCQ interactions in ~300 lines. |
| Database       | **Firestore** (cloud) / **JSON file** (dev)         | Hackathon requires ≥1 GCP service; Firestore gives per-job persistence without schema migrations. |
| Deployment     | **Cloud Run** (Dockerfile, python:3.11-slim)        | Scales to zero, cheap with $150 credits, easy `gcloud run deploy`. |
| Share pages    | **Jinja2 server-rendered** at `/plan/:id`           | SEO/OG meta for social sharing; no JS required to view a plan. |

## Resilience features

- **Model fallback queue**: if the primary model returns 429 or 503, we automatically cycle to the next model with cooldowns per model.
- **Per-attempt JSON repair**: if the model outputs markdown fences or invalid JSON, we retry with an explicit "fix your JSON" reminder (up to 3 times per agent).
- **Partial batch failure**: if one content batch fails, we keep the batches that succeeded instead of failing the entire pipeline.
- **SSE keepalives**: a `: keepalive` comment every 30s prevents proxy timeouts.
- **Instruction auto-escaping**: ADK 2.7+ treats `{var}` in instructions as a session-state variable; our `_escape_instruction` pre-processor doubles literal braces to prevent `KeyError`.

## Data contracts

Every agent communicates through strongly-typed Pydantic models in `models/schemas.py`. The `StudyPlanState` object is the single source of truth and is persisted after each step. This makes the pipeline:

1. **Testable** — each agent is a pure function: `State → State`.
2. **Resumable** — if Cloud Run cold-starts mid-pipeline, state is reloaded from Firestore.
3. **Debuggable** — logs show chapter/plan/card counts at each step.
