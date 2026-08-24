# 🚀 How to Push Exam Mitra to GitHub (Step by Step)

Your GitHub username: **shubham00000100010101010**
Project repo name suggestion: **exam-mitra**
Make it **PRIVATE** first (make public on Aug 30 before submission)

---

## Method 1: Upload the ZIP directly (EASIEST — no Git needed)

1. Go to https://github.com/new and sign in as `shubham00000100010101010`
2. Repository name: `exam-mitra`
3. Description: `🏆 Exam Mitra — Autonomous AI Study Agent for All Indian Exams (JEE/NEET/UPSC/SSC/Banking/Boards/NDA/CTET/State PSCs/College). Built for Google Cloud "All Things Agentic" Hackathon.`
4. Select **Private** (IMPORTANT — don't make public until Aug 30)
5. **DO NOT** check "Add a README", "Add .gitignore", "Add a license" (we already have all of these)
6. Click **Create repository**
7. On the next page, click **"uploading an existing file"** link
8. Unzip `exam-mitra.zip` on your computer, then drag-and-drop ALL the files from inside the `exam-mitra` folder into the upload area
9. At the bottom, write commit message: `Initial release: Exam Mitra v2.4.1 - complete codebase`
10. Click **Commit changes**

⚠️ This method does NOT preserve git history (15 commit timeline). If you want proper git history, use Method 2.

---

## Method 2: Push via Git command line (RECOMMENDED — preserves commit history)

### Step 1: Install Git (if not installed)
- **Windows**: Download from https://git-scm.com/download/win, install with defaults
- **Mac**: `brew install git` or run `git --version` in Terminal (it will prompt install)
- **Linux**: `sudo apt install git`

### Step 2: Unzip the project
```bash
# On Windows, right-click exam-mitra.zip → Extract All
# On Mac/Linux:
unzip exam-mitra.zip -d ~/
cd ~/exam-mitra
```

### Step 3: Configure Git (only first time on your machine)
```bash
git config --global user.name "Shubham"
git config --global user.email "shubham@exammitra.ai"
```

### Step 4: Create GitHub repo
1. Go to https://github.com/new
2. Name: `exam-mitra`
3. Select **Private**
4. **DO NOT** check README/.gitignore/license
5. Click "Create repository"

### Step 5: Connect local repo to GitHub and push
```bash
cd exam-mitra   # make sure you're inside the project folder

# Add your GitHub repo as the "origin" remote
git remote add origin https://github.com/shubham00000100010101010/exam-mitra.git

# Rename branch to main (if not already)
git branch -M main

# Push everything (all 16 commits with full history)
git push -u origin main
```

### Step 6: When prompted for credentials
GitHub no longer accepts password for HTTPS — use a **Personal Access Token (PAT)**:
1. Go to https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Note: `exam-mitra-push`
4. Expiration: `No expiration`
5. Check **repo** (full repo control)
6. Click "Generate token" and COPY IT immediately (you won't see it again)
7. Use it as your password when Git asks

💡 **Tip for Windows**: Git Credential Manager will save it so you don't have to type it again.

---

## Method 3: If Git asks for your username/password every time
Run this once to cache credentials:
```bash
git config --global credential.helper store
```

---

## AFTER pushing — Verify ✅

1. Go to `https://github.com/shubham00000100010101010/exam-mitra`
2. You should see all files (README.md, main.py, agents/, static/, templates/...)
3. Click "commits" — you should see 16 commits spanning Aug 22 → Aug 24, all authored by **Shubham**
4. Click `.env.example` — you should see the template (NOT the real API key)
5. `.env` should NOT appear in the file list (it's in .gitignore — SAFE)

---

## Making future commits

If you edit any file later (e.g. fixing a bug, adding a feature):

```bash
cd exam-mitra

# See what changed
git status

# Add all changed files
git add .

# Commit with a message
git commit -m "Describe what you changed, e.g.: v2.4.2 - performance improvements"

# Push to GitHub
git push
```

---

## Making it PUBLIC on Aug 30 (submission day)

1. Go to repo Settings → scroll to bottom → **Change visibility** → "Make public"
2. Or keep it private and add the Devpost/judges as collaborators (safer)
3. Add repo link to your Devpost submission: `https://github.com/shubham00000100010101010/exam-mitra`

---

## After cloning on a new machine (to run locally)

```bash
git clone https://github.com/shubham00000100010101010/exam-mitra.git
cd exam-mitra
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env           # then edit .env to put your real GEMINI_API_KEY
python main.py
# Open http://localhost:8080
```

---

## Project summary (for your Devpost / reference)

| Detail | Value |
|---|---|
| Name | Exam Mitra |
| Version | v2.4.1 |
| Author | Shubham (solo) |
| Started | Aug 22, 2026 |
| Architecture | FastAPI + Google ADK + Gemini 3.5 Flash Lite + GCP Cloud Run + Firestore |
| Agents | 9 (parse → plan → resources → content × 3 → grade → remediate → tutor) |
| Exams covered | 56+ presets across 10 categories (JEE/NEET/UPSC/SSC/Banking/Railway/NDA/CTET/Boards/State PSCs/College) |
| Languages | English, Hindi (Devanagari), Hinglish |
| Tier 2 features | Photo syllabus OCR, PWA offline, Spaced Repetition SM-2 + radar dashboard |
| License | MIT |
| Hackathon track | The Taskmaster (Google Cloud "All Things Agentic") |
| Devpost | exam-mitra-ai-study-agent-for-indian-exams |
