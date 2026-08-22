// ===== Exam Mitra — frontend (async + SSE) =====
const $ = s => document.querySelector(s);
const form = $("#plan-form");
const submitBtn = $("#submit-btn");
const progressSection = $("#progress-section");
const resultsSection = $("#results");
const stepsList = $("#steps-list");

const STEP_LABELS = [
  "Starting up...",
  "Parsing syllabus into chapters",
  "Building your day-by-day study plan",
  "Finding the best free video lectures",
  "Writing revision notes, flashcards & MCQs",
  "Finalizing your study package...",
  "Finalizing your study package...",
  "🎉 Your study package is ready!",
];
const TOTAL_STEPS = 7;

function esc(s) {
  return (s||"").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
}

function renderProgress(currentStep, counts = {}) {
  progressSection.classList.remove("hidden");
  stepsList.innerHTML = "";
  for (let i = 1; i <= TOTAL_STEPS; i++) {
    let label = STEP_LABELS[i] || `Step ${i}`;
    // Show live counts for completed steps
    if (i === 1 && counts.chapters) label += ` (${counts.chapters} chapters found)`;
    if (i === 2 && counts.days) label += ` (${counts.days} days planned)`;
    if (i === 3 && counts.resources) label += ` (${counts.resources} resources found)`;
    if (i === 4 && counts.notes) label += ` (${counts.notes} notes, ${counts.flashcards||0} cards, ${counts.mcqs||0} MCQs)`;
    const isDone = i < currentStep;
    const isActive = i === currentStep;
    const div = document.createElement("div");
    div.className = "step" + (isDone ? " done" : isActive ? " active" : "");
    div.innerHTML = `<div class="step-icon"><span class="step-num">${i}</span></div><div>${label}${isActive ? "…" : ""}</div>`;
    stepsList.appendChild(div);
  }
}

function resetForm() {
  submitBtn.disabled = false;
  submitBtn.classList.remove("loading");
  submitBtn.querySelector(".btn-text").textContent = "✨ Generate my study plan";
}

// ---- SSE (real-time progress) ----

function connectSSE(jobId) {
  return new Promise((resolve, reject) => {
    const es = new EventSource(`/api/jobs/${jobId}/stream`);
    es.onmessage = e => {
      try {
        const data = JSON.parse(e.data);
        if (data.event === "init") {
          renderProgress(data.step || 1, data);
        } else if (data.event === "progress") {
          renderProgress(data.step || 1, data);
        } else if (data.event === "step_complete") {
          renderProgress(data.step + 1, data);
        } else if (data.event === "complete") {
          renderProgress(TOTAL_STEPS, data);
          es.close();
          setTimeout(() => loadAndRenderResults(jobId), 800);
          resolve();
        } else if (data.event === "error") {
          es.close();
          alert("Something went wrong: " + data.message);
          resetForm();
          reject(new Error(data.message));
        } else if (data.event === "close") {
          es.close();
        }
      } catch (err) { console.error("SSE parse error:", err); }
    };
    es.onerror = () => {
      // Don't reject on keepalive errors; SSE will auto-reconnect
      console.warn("SSE connection issue, will retry...");
    };
  });
}

// ---- Form submit ----

form.addEventListener("submit", async e => {
  e.preventDefault();
  submitBtn.disabled = true;
  submitBtn.classList.add("loading");
  submitBtn.querySelector(".btn-text").textContent = "Starting agents";

  resultsSection.classList.add("hidden");
  resultsSection.innerHTML = "";
  progressSection.classList.remove("hidden");
  renderProgress(1);

  const payload = {
    exam: $("#exam").value.trim(),
    syllabus: $("#syllabus").value.trim(),
    daily_hours: parseFloat($("#hours").value) || 4,
    start_date: $("#start-date").value || null,
    language: $("#language").value,
  };

  try {
    const resp = await fetch("/api/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!resp.ok) throw new Error(`Server error ${resp.status}`);
    const { job_id } = await resp.json();

    // Update URL without reload
    history.replaceState(null, "", `?job=${job_id}`);

    // Connect to SSE for real-time progress
    await connectSSE(job_id);
  } catch (err) {
    console.error(err);
    alert("Error starting job: " + err.message);
    resetForm();
  }
});

// ---- Results rendering ----

async function loadAndRenderResults(jobId) {
  const r = await fetch(`/api/jobs/${jobId}`);
  const j = await r.json();
  renderResults(jobId, j);
  resetForm();
}

function renderResults(jobId, j) {
  const pkg = j.package;
  if (!pkg) {
    resultsSection.innerHTML = `<div class="card"><p>No results yet. Status: ${j.status}</p></div>`;
    resultsSection.classList.remove("hidden");
    return;
  }
  progressSection.classList.add("hidden");

  const planUrl = `${location.origin}/plan/${jobId}`;
  const stats = [
    {n: pkg.total_chapters, l: "Chapters"},
    {n: pkg.total_days, l: "Days"},
    {n: Math.round(pkg.total_hours)+"h", l: "Total hours"},
    {n: pkg.resources.length, l: "Resources"},
    {n: pkg.flashcards.length, l: "Flashcards"},
    {n: pkg.mcqs.length, l: "MCQs"},
  ];
  const statsHtml = stats.map(s => `<div class="result-stat"><div class="n">${s.n}</div><div class="l">${s.l}</div></div>`).join("");

  // Tabs
  const TABS = [
    {id:"overview", label:"📊 Overview"},
    {id:"plan", label:"📅 Daily Plan"},
    {id:"resources", label:"🎬 Resources"},
    {id:"notes", label:"📝 Notes"},
    {id:"flashcards", label:"🗂️ Flashcards"},
    {id:"mcqs", label:"✅ Practice MCQs"},
  ];
  const tabsHtml = TABS.map((t,i)=>`<button class="tab ${i===0?'active':''}" data-tab="${t.id}">${t.label}</button>`).join("");

  // Overview
  const overviewHtml = `
    <div style="background:linear-gradient(135deg,#ecfdf5,#d1fae5);border-radius:12px;padding:18px 20px;margin-bottom:16px">
      <h3 style="margin:0 0 6px;color:#065f46">🎉 Your personalized study package is ready</h3>
      <p style="margin:0;color:#064e3b">Share this plan with friends or save it for later — it's saved at a permanent link.</p>
    </div>
    <div style="display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap">
      <button id="copy-link" class="btn-primary" style="width:auto;padding:10px 18px;font-size:14px">🔗 Copy shareable link</button>
      <a href="/plan/${jobId}" target="_blank" style="padding:10px 18px;border:1.5px solid var(--accent);color:var(--accent);border-radius:12px;text-decoration:none;font-weight:600;font-size:14px">📖 Open shareable page</a>
    </div>
    <div class="chapter-card"><b>Exam:</b> ${esc(pkg.exam)}</div>
    <p style="font-size:13px;color:var(--muted);margin-top:12px">
      💡 Use the tabs to explore each section. Start with Daily Plan to see what to study each day, then Resources for videos, Notes for revision, Flashcards for active recall, and MCQs for practice.
    </p>`;

  // Daily plan
  const planHtml = pkg.daily_plan.map(d => `
    <div class="day-row ${d.activities.join(' ').toLowerCase().includes('revis') || d.chapter.toLowerCase().includes('revis') ? 'review' : ''}">
      <div class="day-badge">D${d.day}${d.date?`<small>${d.date.slice(5)}</small>`:''}</div>
      <div class="day-body"><h4>${esc(d.chapter)}</h4>
        <div class="hours">⏱ ${d.hours} hours</div>
        <ul>${d.activities.map(a=>`<li>${esc(a)}</li>`).join("")}</ul>
      </div>
    </div>`).join("");

  // Resources grouped by chapter
  const rByCh = {};
  pkg.resources.forEach(r => { (rByCh[r.chapter] = rByCh[r.chapter]||[]).push(r); });
  const resHtml = Object.keys(rByCh).length ? Object.entries(rByCh).map(([ch, rs]) => `
    <h4 style="margin:16px 0 8px">${esc(ch)}</h4>
    ${rs.map(r=>`<a class="resource-card" href="${esc(r.url)}" target="_blank" rel="noopener">
      <div class="resource-icon">${r.platform==='youtube'||r.platform==='pw'||r.platform==='vedantu'?'▶️':'🎓'}</div>
      <div class="resource-body">
        <div class="resource-title">${esc(r.title)}</div>
        <div class="resource-meta">${esc(r.platform)}${r.teacher_or_channel?' · '+esc(r.teacher_or_channel):''}</div>
        <div class="resource-why">${esc(r.why)}</div>
      </div></a>`).join("")}`).join("") : `<p style="color:var(--muted)">No resources found for this topic. Use YouTube to search for lectures.</p>`;

  // Notes
  const notesHtml = pkg.notes.length ? pkg.notes.map(n => `
    <div class="chapter-card">
      <div class="chapter-title">📝 ${esc(n.chapter || "Chapter Notes")}</div>
      <div class="chapter-body">
        ${n.key_concepts.length ? `<span class="label">Key concepts</span><ul>${n.key_concepts.map(k=>`<li>${esc(k)}</li>`).join("")}</ul>`:""}
        ${n.formulas_or_definitions.length ? `<span class="label">Formulas / definitions</span><ul>${n.formulas_or_definitions.map(f=>`<li>${esc(f)}</li>`).join("")}</ul>`:""}
        ${n.common_mistakes.length ? `<span class="label">Common mistakes</span><ul>${n.common_mistakes.map(m=>`<li>${esc(m)}</li>`).join("")}</ul>`:""}
        ${n.summary ? `<span class="label">Summary</span><p>${esc(n.summary)}</p>`:""}
      </div>
    </div>`).join("") : `<p style="color:var(--muted)">No notes generated.</p>`;

  // Flashcards
  const cardsHtml = `
    <p style="color:var(--muted);font-size:13px;margin-top:0">👆 Click any card to flip it and reveal the answer.</p>
    ${pkg.flashcards.map(c=>`<div class="flashcard" onclick="this.classList.toggle('flipped')"><div class="flashcard-inner">
      <div class="flashcard-front"><span class="flashcard-tag">${esc(c.difficulty)}</span><div>${esc(c.front)}</div></div>
      <div class="flashcard-back"><span class="flashcard-tag">answer</span><div>${esc(c.back)}</div></div>
    </div></div>`).join("")}`;

  // MCQs (with interactive grading)
  const mcqsHtml = `
    <p style="color:var(--muted);font-size:13px;margin-top:0">Select an answer for each question, then click "Grade answers" to see your score and weak areas.</p>
    <div id="mcq-list">
      ${pkg.mcqs.map((q,i)=>`
        <div class="mcq" data-idx="${i}" data-correct="${esc(q.correct_answer)}">
          <div class="mcq-question"><b>Q${i+1}.</b> ${esc(q.question)} <small style="color:var(--muted);font-weight:400">(${esc(q.chapter)})</small></div>
          <div class="mcq-options">
            ${q.options.map(o=>`<div class="mcq-option" data-label="${esc(o.label)}"><span class="letter">${esc(o.label)}</span><span>${esc(o.text)}</span></div>`).join("")}
          </div>
          <div class="mcq-explanation"><b>Explanation:</b> ${esc(q.explanation)}</div>
        </div>`).join("")}
    </div>
    <button id="grade-btn" class="btn-primary" style="width:auto;margin-top:12px;padding:12px 24px">📊 Grade my answers</button>
    <div id="grade-result" style="margin-top:16px"></div>`;

  resultsSection.innerHTML = `<div class="card">
    <div class="result-header">
      <h2>✅ Your personalized study plan</h2>
      <p>Built by Exam Mitra's 7-step autonomous agent pipeline.</p>
      <div class="result-stats">${statsHtml}</div>
    </div>
    <div class="tabs">${tabsHtml}</div>
    <div class="tab-panel active" data-panel="overview">${overviewHtml}</div>
    <div class="tab-panel" data-panel="plan">${planHtml}</div>
    <div class="tab-panel" data-panel="resources">${resHtml}</div>
    <div class="tab-panel" data-panel="notes">${notesHtml}</div>
    <div class="tab-panel" data-panel="flashcards">${cardsHtml}</div>
    <div class="tab-panel" data-panel="mcqs">${mcqsHtml}</div>
  </div>`;

  resultsSection.classList.remove("hidden");

  // Tab switching
  resultsSection.querySelectorAll(".tab").forEach(tab => {
    tab.addEventListener("click", () => {
      resultsSection.querySelectorAll(".tab").forEach(x=>x.classList.remove("active"));
      resultsSection.querySelectorAll(".tab-panel").forEach(x=>x.classList.remove("active"));
      tab.classList.add("active");
      resultsSection.querySelector(`[data-panel="${tab.dataset.tab}"]`).classList.add("active");
    });
  });

  // Flashcard flip
  resultsSection.querySelectorAll(".flashcard").forEach(c=>c.addEventListener("click",()=>c.classList.toggle("flipped")));

  // MCQ selection & grading
  resultsSection.querySelectorAll(".mcq").forEach(mcq=>{
    mcq.querySelectorAll(".mcq-option").forEach(opt=>{
      opt.addEventListener("click",()=>{
        if(mcq.classList.contains("explained")) return;
        mcq.querySelectorAll(".mcq-option").forEach(o=>o.classList.remove("selected"));
        opt.classList.add("selected");
      });
    });
  });

  const gradeBtn = resultsSection.querySelector("#grade-btn");
  if (gradeBtn) gradeBtn.addEventListener("click", async () => {
    const answers = {};
    resultsSection.querySelectorAll(".mcq").forEach(mcq=>{
      const sel = mcq.querySelector(".mcq-option.selected");
      if (sel) answers[mcq.dataset.idx] = sel.dataset.label;
    });
    gradeBtn.disabled = true; gradeBtn.textContent = "Grading…";
    try {
      const resp = await fetch(`/api/jobs/${jobId}/grade`, {
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({answers})
      });
      const r = await resp.json();
      resultsSection.querySelectorAll(".mcq").forEach(mcq=>{
        const correct = mcq.dataset.correct;
        const picked = answers[mcq.dataset.idx];
        mcq.classList.add("explained");
        mcq.querySelectorAll(".mcq-option").forEach(o=>{
          if(o.dataset.label===correct) o.classList.add("correct");
          if(o.dataset.label===picked && picked!==correct) o.classList.add("wrong");
        });
      });
      const weakHtml = r.weak_areas.length
        ? `<h4>📌 Areas to revisit:</h4><ul>${r.weak_areas.map(w=>`<li><b>${esc(w.chapter)}</b> — ${esc(w.topic)}: ${esc(w.feedback)}</li>`).join("")}</ul>`
        : "<p>🌟 No weak areas detected — great job!</p>";
      resultsSection.querySelector("#grade-result").innerHTML = `
        <div class="chapter-card" style="background:linear-gradient(135deg,#eef2ff,#f5f3ff);border-color:#c7d2fe">
          <h3 style="margin-top:0">🎯 Score: ${r.score}/${r.total} (${r.percentage.toFixed(0)}%)</h3>
          <p>${esc(r.encouragement)}</p>${weakHtml}
        </div>`;
    } catch(e) { alert("Grading error: "+e.message); }
    gradeBtn.disabled = false; gradeBtn.textContent = "📊 Grade my answers";
  });

  // Copy link button
  const copyBtn = resultsSection.querySelector("#copy-link");
  if (copyBtn) copyBtn.addEventListener("click", async () => {
    await navigator.clipboard.writeText(planUrl);
    copyBtn.textContent = "✅ Link copied!";
    setTimeout(()=>copyBtn.textContent="🔗 Copy shareable link", 2000);
  });

  // Scroll to results
  resultsSection.scrollIntoView({behavior:"smooth", block:"start"});
}

// ---- On page load: if ?job=XXX in URL, poll/stream for that job ----
window.addEventListener("DOMContentLoaded", () => {
  const params = new URLSearchParams(location.search);
  const existingJob = params.get("job");
  if (existingJob) {
    (async () => {
      try {
        const r = await fetch(`/api/jobs/${existingJob}`);
        const j = await r.json();
        if (j.status === "complete") {
          renderResults(existingJob, j);
        } else {
          progressSection.classList.remove("hidden");
          renderProgress(j.step || 1, j);
          await connectSSE(existingJob);
        }
      } catch(e) {
        console.log("No existing job:", e);
      }
    })();
  }
});
