/* =========================================================
   Exam Mitra — frontend logic (SSE, rendering, interactions)
   Vanilla JS, no frameworks.
   ========================================================= */
const $  = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

const form             = $("#plan-form");
const submitBtn        = $("#submit-btn");
const progressSection  = $("#progress-section");
const resultsSection   = $("#results");
const stepsList        = $("#steps-list");

const STEP_LABELS = [
  "Queued",
  "Parsing syllabus into chapters",
  "Building your day-by-day study plan",
  "Finding the best free video lectures",
  "Writing revision notes, flashcards & MCQs",
  "Finalizing your study package…",
  "Finalizing your study package…",
  "🎉 Your study package is ready!",
];
const TOTAL_STEPS = 7;

/* ---- utilities ---- */
function esc(s) {
  return (s == null ? "" : String(s)).replace(
    /[&<>"']/g,
    c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])
  );
}

/* ---- progress rendering ---- */
function renderProgress(currentStep, counts = {}) {
  progressSection.classList.remove("hidden");
  stepsList.innerHTML = "";
  for (let i = 1; i <= TOTAL_STEPS; i++) {
    let label = STEP_LABELS[i] || `Step ${i}`;
    if (i === 1 && counts.chapters) label += ` — ${counts.chapters} chapters`;
    if (i === 2 && counts.days)     label += ` — ${counts.days} days`;
    if (i === 3 && counts.resources)label += ` — ${counts.resources} resources`;
    if (i === 4 && counts.notes)    label += ` — ${counts.notes} notes, ${counts.flashcards||0} cards, ${counts.mcqs||0} MCQs`;
    const isDone   = i < currentStep;
    const isActive = i === currentStep;
    const div = document.createElement("div");
    div.className = "step" + (isDone ? " done" : isActive ? " active" : "");
    div.innerHTML = `
      <div class="step-icon"><span class="step-num">${i}</span></div>
      <div class="step-label">${label}${isActive ? "…" : ""}</div>
      <div class="step-count">${isDone ? "✓" : ""}</div>`;
    stepsList.appendChild(div);
  }
}

function resetForm() {
  submitBtn.disabled = false;
  submitBtn.classList.remove("loading");
  submitBtn.querySelector(".btn-text").textContent = "✨ Generate my study plan";
}

/* ---- SSE ---- */
function connectSSE(jobId) {
  return new Promise((resolve, reject) => {
    const es = new EventSource(`/api/jobs/${jobId}/stream`);
    let finished = false;

    es.onmessage = e => {
      try {
        const data = JSON.parse(e.data);
        const ev = data.event;
        if (ev === "init" || ev === "progress") {
          renderProgress(data.step || 1, data);
        } else if (ev === "step_complete") {
          renderProgress(data.step + 1, data);
        } else if (ev === "complete") {
          renderProgress(TOTAL_STEPS, data);
          finished = true;
          es.close();
          setTimeout(() => loadAndRenderResults(jobId), 600);
          resolve();
        } else if (ev === "error") {
          finished = true;
          es.close();
          showError(data.message || "Something went wrong. Please try again.");
          resetForm();
          resolve(); // resolve (don't reject) so UI shows error cleanly
        } else if (ev === "close") {
          es.close();
          if (!finished) resolve();
        }
      } catch (err) { console.error("SSE parse error:", err); }
    };
    es.onerror = () => {
      // EventSource auto-reconnects; don't reject on transient errors.
      console.warn("SSE connection hiccup, will retry…");
    };
  });
}

/* ---- form submit ---- */
form.addEventListener("submit", async e => {
  e.preventDefault();
  submitBtn.disabled = true;
  submitBtn.classList.add("loading");
  submitBtn.querySelector(".btn-text").textContent = "Starting agents";

  resultsSection.classList.add("hidden");
  resultsSection.innerHTML = "";
  progressSection.classList.remove("hidden");
  renderProgress(1);
  // Scroll to progress on mobile
  progressSection.scrollIntoView({ behavior: "smooth", block: "start" });

  const payload = {
    exam:         $("#exam").value.trim(),
    syllabus:     $("#syllabus").value.trim(),
    daily_hours:  parseFloat($("#hours").value) || 4,
    start_date:   $("#start-date").value || null,
    language:     $("#language").value,
  };

  try {
    const resp = await fetch("/api/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!resp.ok) {
      let msg = `Server error (${resp.status})`;
      try { const j = await resp.json(); msg = j.detail || j.error || msg; } catch(_) {}
      throw new Error(msg);
    }
    const { job_id } = await resp.json();
    history.replaceState(null, "", `?job=${job_id}`);
    await connectSSE(job_id);
  } catch (err) {
    console.error(err);
    showError(err.message);
    resetForm();
  }
});

function showError(msg) {
  progressSection.classList.add("hidden");
  resultsSection.classList.remove("hidden");
  resultsSection.innerHTML = `
    <div class="card">
      <div class="error-banner">
        <h3>⚠️ Generation failed</h3>
        <p>${esc(msg)}</p>
        <button onclick="location.reload()" class="btn-primary" style="width:auto;margin-top:12px;padding:10px 18px;font-size:14px">Try again</button>
      </div>
    </div>`;
  resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

/* ---- results ---- */
async function loadAndRenderResults(jobId) {
  const r = await fetch(`/api/jobs/${jobId}`);
  const j = await r.json();
  renderResults(jobId, j);
  resetForm();
}

function renderResults(jobId, j) {
  if (j.error) { showError(j.error); return; }
  const pkg = j.package;
  if (!pkg) {
    resultsSection.innerHTML = `<div class="card"><p class="hint">No results yet. Status: ${esc(j.status)}</p></div>`;
    resultsSection.classList.remove("hidden");
    return;
  }
  progressSection.classList.add("hidden");

  const planUrl  = `${location.origin}/plan/${jobId}`;
  const printUrl = `${location.origin}/plan/${jobId}/print`;
  const PROGRESS_KEY = `examm_done_${jobId}`;
  const completed = new Set(JSON.parse(localStorage.getItem(PROGRESS_KEY) || "[]"));
  const doneCount = [...completed].filter(d => parseInt(d) <= pkg.total_days).length;
  const pct = pkg.total_days ? Math.round(doneCount / pkg.total_days * 100) : 0;

  const stats = [
    { n: pkg.total_chapters,       l: "Chapters" },
    { n: pkg.total_days,           l: "Days" },
    { n: Math.round(pkg.total_hours) + "h", l: "Hours" },
    { n: pkg.resources.length,     l: "Videos" },
    { n: pkg.flashcards.length,    l: "Flashcards" },
    { n: pkg.mcqs.length,          l: "MCQs" },
  ];
  const statsHtml = stats.map(s =>
    `<div class="result-stat"><div class="n">${s.n}</div><div class="l">${s.l}</div></div>`
  ).join("");

  const TABS = [
    { id: "overview",   label: "📊 Overview" },
    { id: "plan",       label: "📅 Daily Plan" },
    { id: "resources",  label: "🎬 Resources" },
    { id: "notes",      label: "📝 Notes" },
    { id: "flashcards", label: "🗂️ Flashcards" },
    { id: "mcqs",       label: "✅ Practice MCQs" },
  ];
  const tabsHtml = TABS.map((t, i) =>
    `<button class="tab ${i===0?"active":""}" data-tab="${t.id}">${t.label}</button>`
  ).join("");

  /* ---------- Overview tab ---------- */
  const overviewHtml = `
    <div class="overview-card">
      <h3>🎉 Your personalized study package is ready</h3>
      <p>Share it with friends, download as PDF, or start studying right here. Your progress is saved in this browser.</p>
    </div>
    <div class="action-row">
      <button id="copy-link" class="btn-accent">🔗 Copy shareable link</button>
      <a href="${planUrl}"  target="_blank" class="btn-ghost" rel="noopener">📖 Open share page</a>
      <a href="${printUrl}" target="_blank" class="btn-ghost" rel="noopener">📄 Download / Print PDF</a>
    </div>
    <div class="exam-pill">📘 ${esc(pkg.exam)}</div>
    <div class="progress-block" style="margin-top:14px">
      <div class="progress-block-lbl">
        <b>📊 Your study progress</b>
        <span>${doneCount}/${pkg.total_days} days completed (${pct}%)</span>
      </div>
      <div class="progress-bar"><div id="overview-progress-bar" style="width:${pct}%"></div></div>
      <p style="font-size:12px;color:var(--muted);margin:8px 0 0">Check off days in the Daily Plan tab as you finish them.</p>
    </div>`;

  /* ---------- Daily plan ---------- */
  const planHeaderHtml = `
    <div style="display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:8px">
      <span id="plan-progress-stat" style="font-size:13px;color:var(--muted)">
        <b style="color:var(--text)">${doneCount}/${pkg.total_days} days</b> completed (${pct}%)
      </span>
      <button id="reset-progress" class="btn-ghost" style="padding:5px 12px;font-size:12px">Reset progress</button>
    </div>`;

  const planDaysHtml = pkg.daily_plan.map(d => {
    const isDone   = completed.has(String(d.day));
    const isReview = (d.activities||[]).join(" ").toLowerCase().includes("revis") ||
                     d.chapter.toLowerCase().includes("revis");
    return `
      <div class="day-row ${isReview?"review":""} ${isDone?"day-done":""}" data-day="${d.day}">
        <label class="day-check" title="Mark as completed">
          <input type="checkbox" class="day-checkbox" data-day="${d.day}" ${isDone?"checked":""}>
          <span class="checkmark"></span>
        </label>
        <div class="day-badge">D${d.day}${d.date?`<small>${d.date.slice(5)}</small>`:""}</div>
        <div class="day-body">
          <h4>${esc(d.chapter)}</h4>
          <div class="hours">${d.hours} hours</div>
          <ul>${(d.activities||[]).map(a=>`<li>${esc(a)}</li>`).join("")}</ul>
        </div>
      </div>`;
  }).join("");

  /* ---------- Resources (grouped by chapter) ---------- */
  const rByCh = {};
  (pkg.resources||[]).forEach(r => { (rByCh[r.chapter] = rByCh[r.chapter]||[]).push(r); });
  const resourcesHtml = Object.keys(rByCh).length
    ? Object.entries(rByCh).map(([ch, rs]) => `
        <h4 style="margin:18px 0 8px;font-size:15px">${esc(ch)}</h4>
        ${rs.map(r => `
          <a class="resource-card" href="${esc(r.url)}" target="_blank" rel="noopener">
            <div class="resource-icon">${(r.platform||"").includes("youtube")||r.platform==="pw"||r.platform==="vedantu" ? "▶️" : "🎓"}</div>
            <div class="resource-body">
              <div class="resource-title">${esc(r.title)}</div>
              <div class="resource-meta">
                <span class="platform-badge">${esc(r.platform||"resource")}</span>
                ${r.teacher_or_channel ? esc(r.teacher_or_channel) : ""}
              </div>
              <div class="resource-why">${esc(r.why||"")}</div>
            </div>
          </a>`).join("")}`).join("")
    : `<p class="hint">No resources found for this topic.</p>`;

  /* ---------- Notes ---------- */
  const notesHtml = (pkg.notes||[]).length
    ? (pkg.notes||[]).map(n => `
        <div class="chapter-card">
          <div class="chapter-title">📝 ${esc(n.chapter || "Chapter Notes")}</div>
          <div class="chapter-body">
            ${(n.key_concepts||[]).length ? `<span class="section-label">Key concepts</span><ul>${n.key_concepts.map(k=>`<li>${esc(k)}</li>`).join("")}</ul>` : ""}
            ${(n.formulas_or_definitions||[]).length ? `<span class="section-label">Formulas / definitions</span>${n.formulas_or_definitions.map(f=>`<div class="formula-item">${esc(f)}</div>`).join("")}` : ""}
            ${(n.common_mistakes||[]).length ? `<span class="section-label">Common mistakes</span>${n.common_mistakes.map(m=>`<div class="mistake-item">⚠️ ${esc(m)}</div>`).join("")}` : ""}
            ${n.summary ? `<span class="section-label">Summary</span><div class="summary-box">${esc(n.summary)}</div>` : ""}
          </div>
        </div>`).join("")
    : `<p class="hint">No notes generated.</p>`;

  /* ---------- Flashcards ---------- */
  const cardsHtml = `
    <p class="hint" style="margin-top:0">👆 Click any card to flip and reveal the answer.</p>
    <div class="flashcard-grid">
      ${(pkg.flashcards||[]).map(c => `
        <div class="flashcard">
          <div class="flashcard-inner">
            <div class="flashcard-front">
              <span class="flashcard-tag">${esc(c.difficulty)}</span>
              <div>${esc(c.front)}</div>
              <div class="flashcard-hint">Click to flip</div>
            </div>
            <div class="flashcard-back">
              <span class="flashcard-tag">answer</span>
              <div>${esc(c.back)}</div>
            </div>
          </div>
        </div>`).join("")}
    </div>`;

  /* ---------- MCQs ---------- */
  const mcqsHtml = `
    <p class="hint" style="margin-top:0">Select an answer for each question, then click <b>Grade my answers</b> to see your score and weak areas.</p>
    <div id="mcq-list">
      ${(pkg.mcqs||[]).map((q,i) => `
        <div class="mcq" data-idx="${i}" data-correct="${esc(q.correct_answer)}">
          <div class="mcq-q"><b>Q${i+1}.</b> ${esc(q.question)}
            <small>${esc(q.chapter)} · ${esc(q.difficulty)}</small>
          </div>
          <div class="mcq-options">
            ${(q.options||[]).map(o => `
              <div class="mcq-option" data-label="${esc(o.label)}">
                <span class="letter">${esc(o.label)}</span>
                <span>${esc(o.text)}</span>
              </div>`).join("")}
          </div>
          <div class="mcq-explanation"><b>Explanation:</b> ${esc(q.explanation)}</div>
        </div>`).join("")}
    </div>
    <button id="grade-btn" class="btn-accent" style="margin-top:14px;padding:12px 24px;font-size:14px">📊 Grade my answers</button>
    <div id="grade-result"></div>`;

  /* ---------- Assemble ---------- */
  resultsSection.innerHTML = `<div class="card">
    <div class="result-header">
      <h2>✅ Your personalized study plan</h2>
      <p>Built autonomously by Exam Mitra's 7 AI agents.</p>
      <div class="result-stats">${statsHtml}</div>
    </div>
    <div class="tabs">${tabsHtml}</div>
    <div class="tab-panel active" data-panel="overview">${overviewHtml}</div>
    <div class="tab-panel" data-panel="plan">${planHeaderHtml}${planDaysHtml}</div>
    <div class="tab-panel" data-panel="resources">${resourcesHtml}</div>
    <div class="tab-panel" data-panel="notes">${notesHtml}</div>
    <div class="tab-panel" data-panel="flashcards">${cardsHtml}</div>
    <div class="tab-panel" data-panel="mcqs">${mcqsHtml}</div>
  </div>`;
  resultsSection.classList.remove("hidden");

  wireUpResultInteractions(jobId, pkg, PROGRESS_KEY, completed, pkg.total_days);

  resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

/* ---- Wire up all interactive bits inside the rendered results ---- */
function wireUpResultInteractions(jobId, pkg, PROGRESS_KEY, completed, totalDays) {
  const root = resultsSection;

  /* Tab switching */
  $$(".tab", root).forEach(tab => {
    tab.addEventListener("click", () => {
      $$(".tab", root).forEach(x => x.classList.remove("active"));
      $$(".tab-panel", root).forEach(x => x.classList.remove("active"));
      tab.classList.add("active");
      root.querySelector(`[data-panel="${tab.dataset.tab}"]`).classList.add("active");
    });
  });

  /* Copy link */
  const planUrl = `${location.origin}/plan/${jobId}`;
  $("#copy-link", root)?.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(planUrl);
      const btn = $("#copy-link", root);
      btn.textContent = "✅ Link copied!";
      setTimeout(() => btn.textContent = "🔗 Copy shareable link", 2000);
    } catch(e) {
      alert("Could not copy link: " + e.message);
    }
  });

  /* Flashcard flip (event delegation — works with nested clicks) */
  root.addEventListener("click", e => {
    const fc = e.target.closest(".flashcard");
    if (fc && !e.target.closest("a")) fc.classList.toggle("flipped");
  });

  /* Day checkboxes */
  const updateProgress = () => {
    const done = $$(".day-checkbox:checked", root).length;
    const pct = Math.round(done / totalDays * 100);
    const bar = $("#overview-progress-bar", root);
    if (bar) bar.style.width = pct + "%";
    const stat = $("#plan-progress-stat", root);
    if (stat) stat.innerHTML = `<b style="color:var(--text)">${done}/${totalDays} days</b> completed (${pct}%)`;
    $$(".day-checkbox", root).forEach(cb => {
      cb.closest(".day-row").classList.toggle("day-done", cb.checked);
      cb.checked ? completed.add(cb.dataset.day) : completed.delete(cb.dataset.day);
    });
    localStorage.setItem(PROGRESS_KEY, JSON.stringify([...completed]));
  };
  $$(".day-checkbox", root).forEach(cb => cb.addEventListener("change", updateProgress));

  $("#reset-progress", root)?.addEventListener("click", () => {
    if (!confirm("Reset all day checkmarks for this plan?")) return;
    completed.clear();
    localStorage.removeItem(PROGRESS_KEY);
    $$(".day-checkbox", root).forEach(cb => { cb.checked = false; });
    $$(".day-row", root).forEach(r => r.classList.remove("day-done"));
    updateProgress();
  });

  /* MCQ selection + grading */
  $$(".mcq", root).forEach(mcq => {
    $$(".mcq-option", mcq).forEach(opt => {
      opt.addEventListener("click", () => {
        if (mcq.classList.contains("explained")) return;
        $$(".mcq-option", mcq).forEach(o => o.classList.remove("selected"));
        opt.classList.add("selected");
      });
    });
  });

  $("#grade-btn", root)?.addEventListener("click", async () => {
    const answers = {};
    $$(".mcq", root).forEach(mcq => {
      const sel = $(".mcq-option.selected", mcq);
      if (sel) answers[mcq.dataset.idx] = sel.dataset.label;
    });
    const btn = $("#grade-btn", root);
    btn.disabled = true; btn.textContent = "Grading…";
    try {
      const resp = await fetch(`/api/jobs/${jobId}/grade`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answers }),
      });
      if (!resp.ok) throw new Error("Grade failed");
      const r = await resp.json();
      $$(".mcq", root).forEach(mcq => {
        const correct = mcq.dataset.correct;
        const picked  = answers[mcq.dataset.idx];
        mcq.classList.add("explained");
        $$(".mcq-option", mcq).forEach(o => {
          o.classList.add("locked");
          if (o.dataset.label === correct) o.classList.add("correct");
          if (o.dataset.label === picked && picked !== correct) o.classList.add("wrong");
        });
      });
      const weakHtml = (r.weak_areas||[]).length
        ? `<h4 style="margin:12px 0 6px">📌 Areas to revisit:</h4>
           <ul class="weak-list">${r.weak_areas.map(w =>
             `<li><b>${esc(w.chapter)}</b> — ${esc(w.topic)}: ${esc(w.feedback)}</li>`
           ).join("")}</ul>`
        : `<p style="margin:10px 0 0;color:var(--success);font-weight:600">🌟 Perfect score — great job!</p>`;
      $("#grade-result", root).innerHTML = `
        <div class="grade-result">
          <div class="grade-score">🎯 ${r.score}/${r.total} (${r.percentage.toFixed(0)}%)</div>
          <p class="grade-msg">${esc(r.encouragement)}</p>
          ${weakHtml}
        </div>`;
    } catch(e) {
      alert("Grading error: " + e.message);
    }
    btn.disabled = false;
    btn.textContent = "📊 Grade my answers";
  });
}

/* ---- Preset chips ---- */
$$(".preset-chip").forEach(chip => {
  chip.addEventListener("click", () => {
    if (chip.dataset.exam)     $("#exam").value     = chip.dataset.exam;
    if (chip.dataset.hours)    $("#hours").value    = chip.dataset.hours;
    if (chip.dataset.syllabus) $("#syllabus").value = chip.dataset.syllabus;
    $$(".preset-chip").forEach(c => c.classList.remove("active"));
    chip.classList.add("active");
    $("#syllabus").focus();
    document.getElementById("plan-form").scrollIntoView({ behavior:"smooth", block:"center" });
  });
});

/* ---- On load: auto-load ?job=XXX ---- */
window.addEventListener("DOMContentLoaded", () => {
  const params = new URLSearchParams(location.search);
  const existingJob = params.get("job");
  if (existingJob) {
    (async () => {
      try {
        const r = await fetch(`/api/jobs/${existingJob}`);
        if (!r.ok) return;
        const j = await r.json();
        if (j.status === "complete") {
          renderResults(existingJob, j);
        } else if (j.status === "error") {
          showError(j.error || "Plan not available.");
        } else {
          progressSection.classList.remove("hidden");
          renderProgress(j.step || 1, j);
          await connectSSE(existingJob);
        }
      } catch(e) {
        console.log("No existing job to resume:", e);
      }
    })();
  }
});
