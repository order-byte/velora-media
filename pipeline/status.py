"""Update preview/data/status.json while an edit version renders.

Usage: python3 status.py <status.json> --version v11 --label "v1.1 · reference match" --path media/v11/
         --edl data/edl.json --ready N --total 12 [--done] [--raw N]
"""
import argparse, json, time

ap = argparse.ArgumentParser()
ap.add_argument("status")
ap.add_argument("--version", required=True)
ap.add_argument("--label", required=True)
ap.add_argument("--path", required=True)
ap.add_argument("--edl", default="data/edl.json")
ap.add_argument("--ready", type=int, required=True)
ap.add_argument("--total", type=int, default=12)
ap.add_argument("--raw", type=int, default=0)
ap.add_argument("--done", action="store_true")
a = ap.parse_args()

s = json.load(open(a.status))
s["updated"] = time.strftime("%H:%M")
end_t = "5:56" if a.ready >= a.total else f"{a.ready * 30 // 60}:{a.ready * 30 % 60:02d}"
vs = [v for v in s.get("versions", []) if v["id"] != a.version]
vs.append({"id": a.version, "label": a.label, "path": a.path, "edl": a.edl, "parts": a.total, "partDur": 30, "ready": a.ready})
s["versions"] = vs
s["render"] = {
    "state": "done" if a.done else "working", "progress": round(a.ready / a.total, 3),
    "message": f"{a.label} ready for review" if a.done else f"Rendering {a.label} · {a.ready}/{a.total} parts (0:00–{end_t})",
    "headline": "Step 1 · Motion graphics", "detail": f"{a.ready} of {a.total} parts rendered.",
}
if a.raw:
    s["raw"] = {"path": "media/raw/", "parts": a.total, "partDur": 30, "ready": a.raw}
title = f"Rendering {a.label}"
acts = [x for x in s.get("activity", []) if not x["title"].startswith("Rendering ") and x["title"] != "Building v1.1"
        and x["title"] != f"{a.label} rendered"]
acts.append({"state": "ok" if a.done else "live", "title": f"{a.label} rendered" if a.done else title,
             "detail": "all 30 reference motions placed, no SFX or music yet" if a.done else f"{a.ready}/{a.total} parts playable now (0:00–{end_t})"})
s["activity"] = acts
s["steps"][0]["state"] = "review" if a.done else "active"
json.dump(s, open(a.status, "w"), indent=1)
print(s["render"]["message"])
