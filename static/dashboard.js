/* =========================================================
   Exam Mitra — Spaced Repetition (SM-2) + Weak-Area Dashboard
   Tier 2 Feature #3
   ========================================================= */

/* ---------- SM-2 Spaced Repetition Algorithm ----------
 * Based on the classic SuperMemo 2 algorithm (Piotr Wozniak, 1988).
 * Cards are stored in localStorage per-job. Rating scale:
 *   0 = completely forgot (blackout)
 *   1 = wrong but remembered seeing it
 *   2 = wrong but answer felt familiar
 *   3 = correct with effort
 *   4 = correct, easy recall
 *   5 = perfect, very easy
 */

const SR_KEY_PREFIX = "em_sr_";
const SR_META_KEY = "em_sr_meta";
const ACCURACY_KEY_PREFIX = "em_acc_";

function _today() {
  // Day counter: days since epoch (UTC, midnight-aligned)
  const now = new Date();
  const utcMidnight = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate());
  return Math.floor(utcMidnight / 86400000);
}

function _srKey(jobId) { return SR_KEY_PREFIX + jobId; }
function _accKey(jobId) { return ACCURACY_KEY_PREFIX + jobId; }

function loadSR(jobId) {
  try { return JSON.parse(localStorage.getItem(_srKey(jobId)) || "{}"); }
  catch(_) { return {}; }
}
function saveSR(jobId, data) {
  localStorage.setItem(_srKey(jobId), JSON.stringify(data));
}

/* Initialize a card's SM-2 state when first seen */
function initCardState(card, chapter) {
  return {
    front: card.front,
    back: card.back,
    chapter: chapter || card.chapter || "",
    difficulty: card.difficulty || "medium",
    reps: 0,
    interval: 0,         // days until next review
    ef: 2.5,             // easiness factor
    due: _today(),       // day number when due
    lastRating: null,
    totalCorrect: 0,
    totalAttempts: 0,
  };
}

/* Apply an SM-2 rating (0-5) and return the updated card state */
function applyRating(state, rating) {
  const q = rating; // SM-2 "quality" 0..5
  state.totalAttempts = (state.totalAttempts || 0) + 1;
  if (q >= 3) {
    state.totalCorrect = (state.totalCorrect || 0) + 1;
    if (state.reps === 0) state.interval = 1;
    else if (state.reps === 1) state.interval = 6;
    else state.interval = Math.round(state.interval * state.ef);
    state.reps += 1;
  } else {
    state.reps = 0;
    state.interval = 1; // review again tomorrow
  }
  // Update easiness factor (clamped 1.3..2.8)
  state.ef = Math.max(1.3, state.ef + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)));
  state.due = _today() + state.interval;
  state.lastRating = q;
  return state;
}

/* Load or initialize all flashcards for a job into SR store */
function ensureSRInitialized(jobId, flashcards) {
  const data = loadSR(jobId);
  let changed = false;
  flashcards.forEach((c, idx) => {
    const id = "fc_" + idx;
    if (!data[id]) {
      data[id] = initCardState(c, c.chapter);
      changed = true;
    }
  });
  if (changed) saveSR(jobId, data);
  return data;
}

/* Count due cards today */
function countDueToday(jobId) {
  const data = loadSR(jobId);
  const t = _today();
  return Object.values(data).filter(c => (c.due || 0) <= t).length;
}

/* Get flashcards due for review today, sorted by overdue (most overdue first) */
function getDueCards(jobId) {
  const data = loadSR(jobId);
  const t = _today();
  return Object.entries(data)
    .filter(([, c]) => (c.due || 0) <= t)
    .map(([id, c]) => ({ id, ...c }))
    .sort((a, b) => (a.due - b.due));
}

/* ---------- Per-chapter accuracy tracking ---------- */
function loadAccuracy(jobId) {
  try { return JSON.parse(localStorage.getItem(_accKey(jobId)) || "{}"); }
  catch(_) { return {}; }
}
function saveAccuracy(jobId, data) {
  localStorage.setItem(_accKey(jobId), JSON.stringify(data));
}

function recordMCQResult(jobId, chapter, correct) {
  const acc = loadAccuracy(jobId);
  if (!acc[chapter]) acc[chapter] = { correct: 0, total: 0, history: [] };
  acc[chapter].total += 1;
  if (correct) acc[chapter].correct += 1;
  acc[chapter].history.push({ correct: !!correct, ts: Date.now() });
  // Cap history at last 50 attempts per chapter
  if (acc[chapter].history.length > 50) acc[chapter].history = acc[chapter].history.slice(-50);
  saveAccuracy(jobId, acc);
  return acc;
}

/* ---------- Dashboard SVG: Radar chart (pure SVG, no library) ---------- */
function radarChart(stats, size = 320) {
  // stats = [{label, value (0..1)}]
  const cx = size / 2, cy = size / 2;
  const rMax = size / 2 - 50;
  const n = stats.length;
  if (n < 3) {
    // Not enough axes — show bar chart fallback
    return barChartFallback(stats, size);
  }
  const angle = i => (Math.PI * 2 * i / n) - Math.PI / 2;

  // Grid rings at 25/50/75/100%
  let rings = "";
  for (let p = 0.25; p <= 1.0; p += 0.25) {
    const pts = stats.map((_, i) => {
      const a = angle(i);
      return `${cx + rMax * p * Math.cos(a)},${cy + rMax * p * Math.sin(a)}`;
    }).join(" ");
    rings += `<polygon points="${pts}" fill="none" stroke="#e2e8f0" stroke-width="1"/>`;
  }
  // Axes
  let axes = "";
  stats.forEach((_, i) => {
    const a = angle(i);
    axes += `<line x1="${cx}" y1="${cy}" x2="${cx + rMax*Math.cos(a)}" y2="${cy + rMax*Math.sin(a)}" stroke="#e2e8f0" stroke-width="1"/>`;
  });
  // Data polygon
  const dataPts = stats.map((s, i) => {
    const a = angle(i);
    const v = Math.max(0, Math.min(1, s.value));
    return `${cx + rMax * v * Math.cos(a)},${cy + rMax * v * Math.sin(a)}`;
  }).join(" ");
  const dataPoly = `<polygon points="${dataPts}" fill="url(#radarGrad)" fill-opacity=".45" stroke="#4f46e5" stroke-width="2"/>`;
  // Data points
  let points = "";
  stats.forEach((s, i) => {
    const a = angle(i);
    const v = Math.max(0, Math.min(1, s.value));
    const x = cx + rMax * v * Math.cos(a);
    const y = cy + rMax * v * Math.sin(a);
    points += `<circle cx="${x}" cy="${y}" r="4" fill="#4f46e5"/>`;
  });
  // Labels
  let labels = "";
  stats.forEach((s, i) => {
    const a = angle(i);
    const lx = cx + (rMax + 26) * Math.cos(a);
    const ly = cy + (rMax + 26) * Math.sin(a) + 4;
    const anchor = Math.abs(Math.cos(a)) < 0.2 ? "middle" : (Math.cos(a) > 0 ? "start" : "end");
    const pct = Math.round(s.value * 100);
    labels += `<text x="${lx}" y="${ly}" text-anchor="${anchor}" font-size="11" fill="#334155" font-weight="600" style="paint-order:stroke;stroke:white;stroke-width:3px">${s.label.slice(0,18)}${s.label.length>18?"…":""} · ${pct}%</text>`;
  });

  return `
    <svg viewBox="0 0 ${size} ${size}" width="100%" height="${size}" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="radarGrad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#6366f1"/>
          <stop offset="100%" stop-color="#ec4899"/>
        </linearGradient>
      </defs>
      ${rings}${axes}${dataPoly}${points}${labels}
    </svg>`;
}

function barChartFallback(stats, size = 320) {
  const w = size, h = size, pad = 40, bw = Math.max(28, (w - 2*pad) / Math.max(stats.length,1) - 8);
  let bars = "";
  stats.forEach((s, i) => {
    const x = pad + i * ((w - 2*pad) / Math.max(stats.length,1));
    const bh = (h - 2*pad) * Math.max(0, Math.min(1, s.value));
    const y = h - pad - bh;
    bars += `<rect x="${x}" y="${y}" width="${bw}" height="${bh}" rx="4" fill="url(#barGrad)"/>`;
    bars += `<text x="${x + bw/2}" y="${y - 6}" text-anchor="middle" font-size="11" font-weight="700" fill="#4f46e5">${Math.round(s.value*100)}%</text>`;
    const lbl = s.label.slice(0,14);
    bars += `<text x="${x + bw/2}" y="${h - pad + 16}" text-anchor="middle" font-size="10" fill="#64748b">${lbl}</text>`;
  });
  return `
    <svg viewBox="0 0 ${w} ${h}" width="100%" height="${h}" xmlns="http://www.w3.org/2000/svg">
      <defs><linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#6366f1"/><stop offset="100%" stop-color="#8b5cf6"/></linearGradient></defs>
      <line x1="${pad}" y1="${h-pad}" x2="${w-pad}" y2="${h-pad}" stroke="#e2e8f0"/>
      ${bars}
    </svg>`;
}

/* ---------- Aggregate dashboard stats ---------- */
function buildDashboardStats(jobId, pkg) {
  const acc = loadAccuracy(jobId);
  const sr = loadSR(jobId);

  // Build per-chapter stats combining MCQ accuracy + flashcard mastery
  const chapterMap = {};
  (pkg.notes || []).forEach(n => { chapterMap[n.chapter] = { label: n.chapter, mcqCorrect: 0, mcqTotal: 0, fcMastery: 0, fcCount: 0 }; });
  (pkg.daily_plan || []).forEach(d => { if (!chapterMap[d.chapter]) chapterMap[d.chapter] = { label: d.chapter, mcqCorrect:0, mcqTotal:0, fcMastery:0, fcCount:0 }; });

  // MCQ accuracy
  Object.entries(acc).forEach(([ch, v]) => {
    if (!chapterMap[ch]) chapterMap[ch] = { label: ch, mcqCorrect:0, mcqTotal:0, fcMastery:0, fcCount:0 };
    chapterMap[ch].mcqCorrect = v.correct;
    chapterMap[ch].mcqTotal = v.total;
  });
  // Flashcard mastery (proportion of cards with reps >= 2)
  Object.values(sr).forEach(c => {
    const ch = c.chapter || "General";
    if (!chapterMap[ch]) chapterMap[ch] = { label: ch, mcqCorrect:0, mcqTotal:0, fcMastery:0, fcCount:0 };
    chapterMap[ch].fcCount += 1;
    if ((c.reps || 0) >= 2) chapterMap[ch].fcMastery += 1;
  });

  const stats = Object.values(chapterMap).map(c => {
    const mcqAcc = c.mcqTotal ? c.mcqCorrect / c.mcqTotal : 0;
    const fcAcc = c.fcCount ? c.fcMastery / c.fcCount : 0;
    // Weighted: MCQs weigh more (real test performance); untried chapters default to ~0.4 so radar doesn't show 0
    const weight = c.mcqTotal > 0 ? 0.7 * mcqAcc + 0.3 * fcAcc : (c.fcCount > 0 ? fcAcc : 0.35);
    return { label: c.label, value: weight, mcqAcc, fcAcc, mcqTotal: c.mcqTotal, fcCount: c.fcCount };
  }).sort((a, b) => a.label.localeCompare(b.label));

  const totalMcqCorrect = Object.values(acc).reduce((s, v) => s + v.correct, 0);
  const totalMcq = Object.values(acc).reduce((s, v) => s + v.total, 0);
  const totalMastered = Object.values(sr).filter(c => (c.reps||0) >= 2).length;
  const totalCards = Object.keys(sr).length;
  const dueToday = countDueToday(jobId);
  const weakChapters = stats.filter(s => s.mcqTotal > 0 && s.mcqAcc < 0.6).sort((a,b) => a.mcqAcc - b.mcqAcc).slice(0, 3);

  return { stats, totalMcqCorrect, totalMcq, totalMastered, totalCards, dueToday, weakChapters, sr };
}
