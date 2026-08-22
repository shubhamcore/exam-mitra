# Exam Mitra 📚 — Your AI Study Companion for Indian Competitive Exams

> **Built for the [All Things Agentic Hackathon](https://allthingsagentichackathon.devpost.com/) (Google Cloud, Aug 2026)**
> Track: **The Taskmaster** — Category: Individual/Hobbyist & Best Architectural Design

**Exam Mitra** is an autonomous AI study agent that takes an exam syllabus and handles the entire study-planning workflow end-to-end: parsing the syllabus → building a daily plan → finding the best free video lectures → generating concise notes → creating flashcards → generating practice MCQs → grading answers and identifying weak areas → sending daily reminders.

Unlike chatbots that wait for you to ask, Exam Mitra runs as an autonomous workflow and outputs a complete study package in one go.

![Architecture](docs/architecture.png)

---

## 🚀 Quick Start (Local)

```bash
# 1. Clone and install
git clone <your-repo-url>
cd exam-mitra
pip install -r requirements.txt

# 2. Get a free Gemini API key from https://aistudio.google.com/apikey
cp .env.example .env
# Edit .env and set GEMINI_API_KEY=your_key_here

# 3. Run
python main.py
# Open http://localhost:8080 in your browser
```

---

## 🏗️ Tech Stack (All Google Cloud + Google ADK)

| Layer | Technology | Why |
|---|---|---|
| Agent Framework | **Google ADK** (Agent Development Kit) | Required by hackathon; provides multi-agent orchestration, tool use, workflow loops |
| LLM | **Gemini 3.5 Flash** via google-genai SDK | Fast, cheap, excellent for structured outputs |
| Backend | **FastAPI** (Python 3.11+) | Async, auto-docs, easy Cloud Run deployment |
| Hosting | **Google Cloud Run** | Required GCP service; serverless, scales to zero |
| Database | **Firestore** (Cloud mode) | Required GCP service; realtime, no-ops, free tier generous |
| Frontend | Vanilla HTML/CSS/JS | Zero build step, fast to ship |
| Search | Google Search Grounding (Vertex AI) in cloud / DuckDuckGo fallback locally | Finds real, recent lecture resources |
| Auth / Email | SendGrid / SMTP (optional reminders) | Background async notifications |
| Container | Docker | Reproducible deploys to Cloud Run |

---

## 🧠 Agent Architecture

Exam Mitra uses a **7-step sequential pipeline** orchestrated by Google ADK, with state persisted to Firestore. Each step is an independent sub-agent with a single responsibility (Single Responsibility Principle), passing a structured state object downstream.

```
[User Input]
     │
     ▼
┌─────────────────────┐
│ 1. SyllabusParser   │  ← Parses PDF/text/topic, extracts structured chapters
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ 2. StudyPlanner     │  ← Breaks into day-by-day plan with hour budgets
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ 3. ResourceFinder   │  ← Searches for best free YouTube lectures per topic
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ 4. NotesGenerator   │  ← Writes concise revision notes per chapter
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ 5. FlashcardMaker   │  ← Creates Q/A flashcards for spaced repetition
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ 6. MCQGenerator     │  ← Generates practice MCQs with explanations
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ 7. AnswerGrader     │  ← (After user practice) Grades, identifies weak areas
└─────────────────────┘
           │
           ▼
[Full Study Package: Plan + Resources + Notes + Flashcards + MCQs]
```

Each agent is built using Google ADK's `LlmAgent` with structured Pydantic output schemas, tool-use enabled, and shared `RunState` so progress is resumable if interrupted.

---

## 🎯 The Problem (for Indian Students)

Every year 10 lakh+ Indian students prepare for JEE, NEET, UPSC, SSC, banking, and state exams. The biggest time sinks:

1. **Planning paralysis** — "Where do I even start with this 50-chapter syllabus?"
2. **Resource overwhelm** — 1000s of YouTube channels, which teacher to follow per topic?
3. **Note-making time** — Copying from books/videos for hours instead of learning
4. **No active recall** — Reading without testing = 80% forgotten in 2 weeks
5. **No feedback loop** — Without graded practice, weak areas stay weak

Exam Mitra automates steps 1-4 in under 2 minutes, so students can spend their time actually learning, not organizing.

---

## 📁 Project Structure

```
exam-mitra/
├── main.py                  # FastAPI app + ADK workflow runner
├── config.py                # Environment + cloud detection
├── requirements.txt         # Dependencies
├── Dockerfile               # Cloud Run container
├── .env.example
├── agents/                  # ADK sub-agents (one per pipeline step)
│   ├── __init__.py
│   ├── syllabus_parser.py
│   ├── study_planner.py
│   ├── resource_finder.py
│   ├── notes_generator.py
│   ├── flashcard_maker.py
│   ├── mcq_generator.py
│   └── answer_grader.py
├── services/                # Infrastructure (LLM, DB, search, notifications)
│   ├── __init__.py
│   ├── llm.py
│   ├── db.py
│   └── search.py
├── models/
│   ├── __init__.py
│   └── schemas.py           # Pydantic models for state and outputs
├── static/                  # Frontend
│   ├── index.html
│   ├── style.css
│   └── app.js
├── tests/
│   └── test_agents.py
└── docs/
    └── architecture.md
```

---

## ☁️ Deployment (Google Cloud Run)

```bash
# Set project
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com aiplatform.googleapis.com firestore.googleapis.com

# Build and deploy
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/exam-mitra
gcloud run deploy exam-mitra \
  --image gcr.io/YOUR_PROJECT_ID/exam-mitra \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi
```

Free credits cover this entire deployment: $150 hackathon credit + $300 GCP free trial = **$450 of runway**, enough for this demo + 1000s of runs.

---

## ✅ Hackathon Submission Checklist

- [x] Gemini 3.5 or newer — **using Gemini 3.5 Flash**
- [x] Google Agent Framework — **using Google ADK**
- [x] Google Cloud infrastructure — **Cloud Run + Firestore**
- [x] Asynchronous/autonomous workflow (not chatbot) — **7-step pipeline runs to completion**
- [x] Live URL on Cloud Run (`.run.app`)
- [x] Public GitHub repo with MIT license
- [x] README with spin-up instructions
- [x] Architecture diagram (in `docs/`)
- [x] ~4 min demo video
- [x] Bonus: blog post on dev.to/Medium
- [x] Bonus: social post with #AllThingsAgenticHackathon

---

## 🔑 Judging Criteria Alignment

| Criteria | Weight | How We Address It |
|---|---|---|
| **Innovation & Utility** | 40% | Solves real pain for 10M+ Indian students; fully autonomous multi-step pipeline (not chat); produces actionable output |
| **Architectural Discipline** | 30% | 7 decoupled ADK sub-agents; Pydantic-validated state; Firestore persistence for resumability; proper error handling; Dockerized |
| **Demo & Production Readiness** | 30% | Live on Cloud Run; clean UI; architecture diagram; reproducible setup; visible GCP Console/Cloud Run proof in video |

---

## 📜 License

MIT — free to use, modify, distribute.

---

## 👤 Builder

Built solo by a student from India for the Google Cloud All Things Agentic Hackathon 2026.

*"AI shouldn't just answer your questions — it should do the work."*
