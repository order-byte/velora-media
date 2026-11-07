"""Update preview/data/status.json while the edit renders.

Usage: python3 status.py <status.json> <ready_parts> <total_parts> [--raw N] [--done]
"""
import json, sys, time

path, ready, total = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
raw = int(sys.argv[sys.argv.index("--raw") + 1]) if "--raw" in sys.argv else 0
done = "--done" in sys.argv
s = json.load(open(path))
s["updated"] = time.strftime("%H:%M")
pct = ready / total
mins = lambda n: f"{int(n * 30 // 60)}:{int(n * 30 % 60):02d}"
end_t = "5:56" if ready >= total else mins(ready)
s["render"] = {
    "state": "done" if done else "working", "progress": round(pct, 3),
    "message": "v1 Motion ready for review" if done else f"Rendering v1 · {ready}/{total} parts ready (0:00–{end_t})",
    "headline": "Step 1 · Motion graphics",
    "detail": f"{ready} of {total} parts rendered.",
}
s["versions"] = [{"id": "v1", "label": "v1 · Motion", "path": "media/v1/", "parts": total, "partDur": 30, "ready": ready}]
if raw:
    s["raw"] = {"path": "media/raw/", "parts": total, "partDur": 30, "ready": raw}
acts = [a for a in s.get("activity", []) if a["title"] not in ("Building timeline", "Rendering v1", "Timeline built", "v1 rendered", "Raw compare track")]
acts.append({"state": "ok", "title": "Timeline built", "detail": "83 camera moves, 55 text cues, 7 graphics, 18 B-roll inserts"})
if done:
    acts.append({"state": "ok", "title": "v1 rendered", "detail": "1080p master + 720p preview, no SFX or music yet"})
else:
    acts.append({"state": "live", "title": "Rendering v1", "detail": f"{ready}/{total} parts playable now (0:00–{end_t})"})
if raw:
    acts.append({"state": "ok", "title": "Raw compare track", "detail": "press Compare with raw to watch both in sync"})
s["activity"] = acts
s["steps"][0]["state"] = "review" if done else "active"
json.dump(s, open(path, "w"), indent=1)
print(s["render"]["message"])
