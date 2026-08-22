# 🚀 Setup & Run Guide — Exam Mitra

This is the full project for the **All Things Agentic (Google Cloud)** hackathon. It's already built and ready to run locally or deploy to Google Cloud Run.

---

## 📋 Prerequisites

1. **Python 3.11+** (3.13 works too — both tested)
2. A free **Gemini API key** → https://aistudio.google.com/apikey (click "Create API key")
3. (Optional, for cloud deploy) A Google Cloud account with billing enabled ($150 free credits provided by the hackathon)

---

## 🏃 Run locally (2 minutes)

```bash
cd exam-mitra

# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
# Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
# if you see LiteLLM warning, also run: pip install "google-adk[extensions]"

# Copy env template and add your key
cp .env.example .env
# edit .env and set: GEMINI_API_KEY=your_key_here

# Run the server
python main.py
# → Open http://localhost:8080 in your browser
```

You'll see the Exam Mitra UI. Paste a syllabus (try "JEE Mains Physics — Kinematics, Laws of Motion, Rotational Motion, Thermodynamics" for testing) and click Generate.

---

## ☁️ Deploy to Google Cloud Run (for live demo)

The hackathon gives you **$150 in Google Cloud credits** — use them!

```bash
# 1. Install gcloud CLI: https://cloud.google.com/sdk/docs/install
gcloud init                     # authenticate and pick a project
gcloud services enable run.googleapis.com aiplatform.googleapis.com firestore.googleapis.com cloudbuild.googleapis.com

# 2. Set project
export PROJECT_ID=your-project-id
gcloud config set project $PROJECT_ID

# 3. Build & deploy (one command)
gcloud run deploy exam-mitra \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --set-env-vars=ENVIRONMENT=cloud,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GEMINI_MODEL=gemini-2.0-flash
```

After ~3 minutes you get a public `https://exam-mitra-xxxx-uc.a.run.app` URL you can submit directly on Devpost.

⚠️ **Important for Vertex AI**: On Cloud Run the default service account needs the `Vertex AI User` and `Cloud Datastore User` roles:
```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$PROJECT_ID-compute@developer.gserviceaccount.com" \
  --role="roles/aiplatform.user"
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$PROJECT_ID-compute@developer.gserviceaccount.com" \
  --role="roles/datastore.user"
```

---

## 🧪 To test the agent pipeline end-to-end

Once the server is running locally:

1. Open http://localhost:8080
2. Exam name: `JEE Mains Physics`
3. Daily hours: `4`
4. Syllabus (paste this for quick test):
   ```
   Units & Dimensions; Kinematics (1D & 2D); Laws of Motion; Work, Energy, Power; Rotational Motion; Gravitation; Thermodynamics; Oscillations & Waves; Electrostatics; Current Electricity; Magnetism; Optics; Modern Physics
   ```
5. Click **Generate my study plan** — expect 60–120 seconds the first time while all 7 agent steps run.
6. You'll get: daily plan, video resources, notes, flashcards, and MCQs — all auto-graded when you answer them.

---

## 📁 Project structure

```
exam-mitra/
├── main.py                     # FastAPI app + pipeline orchestrator
├── config.py                   # Settings (env vars auto-detect local/cloud)
├── requirements.txt            # Python deps
├── Dockerfile                  # Cloud Run container
├── agents/
│   ├── _adk.py                 # Shared Google ADK helpers (Gemini, runner)
│   ├── syllabus_parser.py      # Step 1 — chapters + importance
│   ├── study_planner.py        # Step 2 — day-by-day plan
│   ├── resource_finder.py      # Step 3 — YouTube/lecture search
│   ├── notes_generator.py      # Step 4 — revision notes
│   ├── flashcard_maker.py      # Step 5 — Q/A flashcards
│   ├── mcq_generator.py        # Step 6 — practice MCQs
│   └── answer_grader.py        # Step 7 — grade + weak areas
├── models/schemas.py           # Pydantic models (strongly-typed state)
├── services/
│   ├── llm.py                  # Gemini client wrapper
│   ├── search.py               # Google Search / DuckDuckGo
│   └── db.py                   # Firestore (cloud) / JSON (local)
├── static/                     # Frontend (HTML/CSS/JS)
│   ├── index.html
│   ├── style.css
│   └── app.js
└── docs/architecture.md        # Diagram + architecture notes
```

---

## 🏆 How to maximize your chance of winning

1. **Polish the demo video** — this is 30% of the score. Record your screen, show the full flow (paste syllabus → wait 2 min → click through each tab → answer MCQs → see score/weaknesses). Narrate in English.
2. **Write a great Devpost submission** — describe the problem (10L+ Indian students overwhelmed by syllabus), your solution (autonomous 7-step pipeline), architecture (show the diagram in `docs/architecture.md`), what you learned, what's next.
3. **Submit before the deadline** — Aug 31, 2026, 8pm EDT = Sep 1, ~5:30 AM IST. Aim to submit Aug 30 to avoid last-minute issues.
4. **Make sure Google Cloud is visibly used** — demo must show Cloud Run URL, and in the video briefly show the GCP console (Cloud Run service, Firestore database) to prove you used required services.
5. **Add 1–2 "wow" features** if time permits:
   - Email/Telegram daily reminders (SendGrid/Twilio)
   - PDF export of the study plan
   - Hindi/regional language output (already supported via `language` param)
   - Spaced-repetition scheduler for flashcards (track when cards are due)

---

## ❓ Troubleshooting

- **"GEMINI_API_KEY is not set"** — copy `.env.example` to `.env` and add your key.
- **"Model gemini-2.0-flash not found"** — change model in `.env` to `gemini-2.5-flash` or `gemini-1.5-flash`.
- **Slow responses** — Gemini calls are sequential; each step takes 5–15 seconds. Expect ~90 seconds total for a full syllabus.
- **JSON parse errors from LLM** — the code automatically retries once and falls back to direct structured generation. If it still fails, reduce the number of chapters in your syllabus.

---

Built with ❤️ for the Google Cloud All Things Agentic Hackathon 2026.
