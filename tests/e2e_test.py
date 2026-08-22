"""End-to-end test: submit Kinematics (single topic), stream SSE, verify quality."""
import json
import sys
import time
import urllib.request
import urllib.error

API = "http://127.0.0.1:8080"


def post_start(exam, syllabus, hours=4, lang="en"):
    data = json.dumps({
        "exam": exam,
        "syllabus": syllabus,
        "daily_hours": hours,
        "language": lang,
    }).encode()
    req = urllib.request.Request(
        f"{API}/api/start",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def stream_events(job_id, timeout=180):
    """Stream SSE until complete/error/close."""
    events = []
    url = f"{API}/api/jobs/{job_id}/stream"
    req = urllib.request.Request(url)
    start = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        buf = b""
        while time.time() - start < timeout:
            chunk = resp.read(1)
            if not chunk:
                break
            buf += chunk
            if buf.endswith(b"\n\n"):
                line = buf.decode().strip()
                buf = b""
                if line.startswith("data:"):
                    payload = line[5:].strip()
                    if payload:
                        try:
                            evt = json.loads(payload)
                            events.append(evt)
                            t = time.time() - start
                            ev = evt.get("event", "?")
                            msg = evt.get("message", "")
                            print(f"  [{t:5.1f}s] {ev:14s} | {msg[:80]}")
                            if ev in ("complete", "error", "close"):
                                return events
                        except json.JSONDecodeError:
                            pass
    return events


def get_job(job_id):
    with urllib.request.urlopen(f"{API}/api/jobs/{job_id}", timeout=10) as r:
        return json.loads(r.read())


def validate_package(pkg):
    """Run quality checks and report PASS/FAIL."""
    results = []

    def check(name, ok, detail=""):
        results.append((name, ok, detail))
        mark = "✅ PASS" if ok else "❌ FAIL"
        print(f"  {mark}: {name}" + (f" — {detail}" if detail else ""))

    # 1. Exactly 1 chapter for single-topic "Kinematics"
    ch_count = pkg["total_chapters"]
    check("Single topic → 1 chapter", ch_count == 1, f"got {ch_count}")

    # 2. Realistic study days (for 8-10 hr topic @ 4hr/day = ~2-4 days)
    days = pkg["total_days"]
    check("Day count realistic (2-6)", 2 <= days <= 8, f"got {days} days")

    # 3. Resources per chapter >= 2
    res_count = len(pkg["resources"])
    check("At least 2 resources", res_count >= 2, f"got {res_count}")
    if res_count > 0:
        r0 = pkg["resources"][0]
        check("Resources have real URLs",
              r0.get("url", "").startswith("http"),
              f"first URL: {r0.get('url','')[:60]}")
        # Check for known educator brands
        joined = " ".join(r.get("title","") + " " + r.get("teacher_or_channel","") for r in pkg["resources"]).lower()
        has_brand = any(b in joined for b in ["physics wallah","pw","vedantu","khan","mohit tyagi","youtube"])
        check("Resources from known educator", has_brand,
              f"titles: {[r.get('title','')[:40] for r in pkg['resources'][:2]]}")

    # 4. Notes: 1 note for the chapter
    notes = pkg["notes"]
    check("Exactly 1 note", len(notes) == 1, f"got {len(notes)}")
    if notes:
        n0 = notes[0]
        kc = n0.get("key_concepts", [])
        fm = n0.get("formulas_or_definitions", n0.get("formulas", []))
        cm = n0.get("common_mistakes", [])
        check("8-12 key concepts", 5 <= len(kc) <= 15, f"got {len(kc)}")
        check("6+ formulas/definitions", len(fm) >= 4, f"got {len(fm)}")
        check("3+ common mistakes", len(cm) >= 2, f"got {len(cm)}")

        # Check key kinematics formulas appear
        fm_text = " ".join(str(x) for x in fm).lower()
        required = ["v=u+at", "v=u+at", "s=ut", "v²=u²+2as", "v2=u2+2as", "v^2=u^2",
                    "s_nth", "projectile", "range", "f=ma", "gravity"]
        found = [r for r in required if any(part in fm_text for part in [r[:5]])]
        check("Key kinematics formulas present",
              any(k in fm_text for k in ["v=u", "v = u", "v=u+at", "s=ut", "v²", "v2=u", "v^2"]),
              f"formulas preview: {[str(f)[:60] for f in fm[:4]]}")

    # 5. Flashcards: 5-8
    cards = pkg["flashcards"]
    check("5-8 flashcards", 4 <= len(cards) <= 12, f"got {len(cards)}")
    if cards:
        sample = cards[0]
        check("Flashcards have front+back",
              bool(sample.get("front")) and bool(sample.get("back")),
              f"front='{sample.get('front','')[:40]}' back='{sample.get('back','')[:40]}'")

    # 6. MCQs: 4 with proper options arrays
    mcqs = pkg["mcqs"]
    check("4 MCQs", len(mcqs) == 4, f"got {len(mcqs)}")
    if mcqs:
        m0 = mcqs[0]
        opts = m0.get("options", [])
        check("MCQ has 4 options (array)", len(opts) == 4,
              f"got {len(opts)} opts, type={type(opts).__name__}")
        if opts and isinstance(opts, list):
            opt0 = opts[0]
            check("Options are {label,text} objects",
                  isinstance(opt0, dict) and "label" in opt0 and "text" in opt0,
              f"opt0={opt0}")
        ca = m0.get("correct_answer", "")
        check("Correct answer is A/B/C/D", ca in "ABCD", f"got '{ca}'")
        expl = m0.get("explanation", "")
        check("Explanation 3+ sentences", len(expl) > 80,
              f"len={len(expl)}: {expl[:80]}...")

    # 7. Daily plan: each day has 3-4 specific activities
    if pkg["daily_plan"]:
        acts = pkg["daily_plan"][0].get("activities", [])
        check("Daily activities specific (3-4)", len(acts) >= 2,
              f"day1 activities: {acts}")

    # Summary
    passes = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"\n{'='*60}")
    print(f"  Score: {passes}/{total} checks passed")
    print(f"{'='*60}")
    return passes == total


def main():
    print("=== Exam Mitra End-to-End Test: Kinematics (single topic) ===\n")
    print("[1] Submitting job...")
    try:
        resp = post_start("JEE Mains Physics", "Kinematics", hours=4)
    except Exception as e:
        print(f"❌ Failed to submit: {e}")
        sys.exit(1)
    job_id = resp["job_id"]
    print(f"    job_id = {job_id}\n")

    print("[2] Streaming events...")
    events = stream_events(job_id, timeout=240)
    ev_types = [e.get("event") for e in events]
    if "error" in ev_types:
        err = [e for e in events if e.get("event") == "error"][0]
        print(f"\n❌ Pipeline ERROR: {err.get('message','')}")
        sys.exit(1)
    if "complete" not in ev_types:
        print(f"\n❌ Pipeline did not complete. Events: {ev_types[-5:]}")
        sys.exit(1)

    print("\n[3] Fetching final package...")
    job = get_job(job_id)
    pkg = job.get("package")
    if not pkg:
        print("❌ No package in response")
        print(json.dumps(job, indent=2)[:500])
        sys.exit(1)

    # Save for inspection
    with open("/tmp/e2e_result.json", "w") as f:
        json.dump(pkg, f, indent=2, default=str)
    print("    Saved to /tmp/e2e_result.json\n")

    print("[4] Quality validation...")
    ok = validate_package(pkg)
    sys.exit(0 if ok else 2)


if __name__ == "__main__":
    main()
