"""Place a music track against the edit so its bars land on the cut's big moments.

Usage: python music_align.py <beats.json> <duration_s> <out.json> [analysis.json]
The edit uses the music in two runs: 0 -> 14.98 s (stops dead on the record-scratch freeze) and
15.38 -> end. For each run every bar start in the track is tried as the anchor:
  run 1: the bar lands on the name reveal at 2.9 s (the hook before it plays low-passed),
  run 2: the bar lands on 15.38 s, where the music slams back in.
A placement scores higher when the edit's hits fall on beats (big hits weigh more), when the
anchor is a measured energy lift, and when the run stays inside the track.
Writes the chosen offsets and the timeline beat grid.
"""
import json, sys
import numpy as np

beats = np.array(json.load(open(sys.argv[1])), float)
track_dur = float(sys.argv[2])
out = sys.argv[3]
ana = json.load(open(sys.argv[4])) if len(sys.argv) > 4 else {}
period = float(np.median(np.diff(beats)))
phase = ana.get("downbeat_phase_hint", 0)
bars = beats[phase::4]
lifts = [e["t"] for e in ana.get("lift_drop_events", []) if e.get("type") == "lift"]

RUN1 = dict(start=0.0, end=14.98, anchor=2.9,
            hits={0.0: 1, 0.68: 1, 2.9: 3, 3.22: 2, 5.0: 1, 5.6: 1, 6.4: 1, 7.27: 1, 7.71: 1, 8.78: 3, 9.33: 2,
                  10.06: 2, 11.3: 1, 12.56: 1, 13.0: 1, 13.45: 2, 14.98: 2})
RUN2 = dict(start=15.38, end=38.9333, anchor=15.38,
            hits={15.38: 2, 15.95: 1, 16.66: 1, 17.85: 1, 18.86: 2, 20.33: 1, 21.0: 1, 21.8: 3, 22.5: 1, 23.25: 2,
                  24.09: 1, 24.47: 1, 24.75: 1, 25.42: 1, 26.4: 1, 27.83: 2, 28.93: 1, 29.46: 3, 30.65: 1, 31.02: 1,
                  32.09: 1, 32.7: 1, 32.82: 3, 33.62: 2, 35.9: 1, 37.33: 3, 37.8: 2})


def beat_err(src_t):
    i = np.searchsorted(beats, src_t)
    cands = beats[max(0, i - 1):i + 1]
    return float(np.min(np.abs(cands - src_t))) if len(cands) else period


def place(run, exclude_before=0.0):
    best = None
    for b in bars:
        src0 = b - (run["anchor"] - run["start"])
        if src0 < 0 or src0 + (run["end"] - run["start"]) > track_dur - 0.3 or b < exclude_before:
            continue
        score = 0.0
        for h, w in run["hits"].items():
            e = beat_err(src0 + (h - run["start"])) / (period / 2)  # 0 on the beat, 1 on the off-beat
            score += w * (1 - min(1.0, e) * 2)
        if any(abs(b - l) < 0.2 for l in lifts):
            score += 6
        if best is None or score > best[0]:
            best = (score, src0, b)
    return best


r1 = place(RUN1)
r2 = place(RUN2)
res = {
    "period_s": round(period, 4),
    "bpm": round(60 / period, 2),
    "run1": {"score": round(r1[0], 2), "src": round(r1[1], 4), "anchor_bar": round(r1[2], 4)},
    "run2": {"score": round(r2[0], 2), "src": round(r2[1], 4), "anchor_bar": round(r2[2], 4)},
}
# beat grid on the edit timeline (for picture pulses)
grid = []
for run, (sc, src0, _) in ((RUN1, r1), (RUN2, r2)):
    for bt in beats:
        tl = run["start"] + (bt - src0)
        if run["start"] <= tl < run["end"]:
            grid.append(round(float(tl), 4))
res["timeline_beats"] = grid
json.dump(res, open(out, "w"), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != "timeline_beats"}))
