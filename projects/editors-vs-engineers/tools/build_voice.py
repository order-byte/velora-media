"""Assemble the voice track from the chosen takes.

Reads edit/takes.json and the forced-aligned words (align_takes.py), cuts each
piece on its first/last kept word, extends to the real speech edges, squeezes
long pauses inside a piece down to a short beat, and writes:
  voice.wav  - the new dialogue track (48 kHz mono)
  edl.json   - every output span with the source time it plays, plus every word
               re-timed onto the new timeline

Usage: python3 build_voice.py TAKES.json RAW48K.wav ALIGNED.json OUT_DIR [SPEED]

SPEED (default 1.0) plays the whole performance faster, pitch kept (ffmpeg atempo);
every output time in edl.json is already scaled, and edl["speed"] says by how much.
"""
import json
import os
import subprocess
import sys
import wave

import numpy as np

HOP = 0.01          # envelope resolution (s)
SPEECH_DB = -40.0   # louder than this counts as speech
SILENT_DB = -46.0   # quieter than this counts as a pause
MAX_PAUSE = 0.26    # pauses longer than this inside a piece get squeezed...
KEEP_PAUSE = 0.13   # ...down to this
FADE = 0.008        # click-free edges on every cut


def load(path):
    w = wave.open(path)
    sr, ch = w.getframerate(), w.getnchannels()
    a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    return a.reshape(-1, ch).mean(1), sr


def envelope(a, sr):
    hop = int(HOP * sr)
    n = len(a) // hop
    rms = np.sqrt((a[:n * hop].reshape(n, hop) ** 2).mean(1))
    return 20 * np.log10(rms + 1e-9)


def cut_points(db, words, keep):
    """Cut on the kept words, grown out to where the sound really starts/ends,
    never reaching into the neighbouring (dropped) words."""
    first, last = words[keep[0]], words[keep[1]]
    lo = words[keep[0] - 1]["e"] + 0.03 if keep[0] > 0 else first["s"] - 0.35
    hi = words[keep[1] + 1]["s"] - 0.03 if keep[1] + 1 < len(words) else last["e"] + 0.35
    s, e = first["s"] - 0.06, last["e"] + 0.10
    lo, hi = max(lo, s - 0.25), min(hi, e + 0.30)   # never wander into breaths and "uh"s
    i = int(s / HOP)
    while i * HOP > lo and db[i - 1] > SILENT_DB:      # walk back through the onset
        i -= 1
    j = int(e / HOP)
    while j * HOP < hi and db[j] > SILENT_DB:          # walk forward through the tail
        j += 1
    return max(i * HOP - 0.03, lo), min(j * HOP + 0.05, hi)


def squeeze(db, s, e):
    """Split [s, e] into spans with long internal pauses cut down."""
    i0, i1 = int(s / HOP), int(e / HOP)
    quiet = db[i0:i1] < SILENT_DB
    spans, cur, k = [], s, 0
    while k < len(quiet):
        if quiet[k]:
            j = k
            while j < len(quiet) and quiet[j]:
                j += 1
            ps, pe = (i0 + k) * HOP, (i0 + j) * HOP
            if pe - ps > MAX_PAUSE and ps > s + 0.05 and pe < e - 0.05:
                half = KEEP_PAUSE / 2
                spans.append((cur, ps + half))
                cur = pe - half
            k = j
        else:
            k += 1
    spans.append((cur, e))
    return [sp for sp in spans if sp[1] - sp[0] >= 0.12]


def main():
    takes, raw, words_path, out = sys.argv[1:5]
    speed = float(sys.argv[5]) if len(sys.argv) > 5 else 1.0
    os.makedirs(out, exist_ok=True)
    pieces = json.load(open(takes))["pieces"]
    a, sr = load(raw)
    db = envelope(a, sr)
    aligned = json.load(open(words_path))

    voice, edl, t = [], [], 0.0
    fade = int(FADE * sr)
    ramp = np.linspace(0, 1, fade, dtype=np.float32)
    for p in pieces:
        if p["gap"] > 0:
            voice.append(np.zeros(int(round(p["gap"] * sr)), np.float32))
            t += p["gap"]
        words = aligned[p["id"]]
        kept = words[p["keep"][0]:p["keep"][1] + 1]
        s, e = cut_points(db, words, p["keep"])
        s, e = p.get("start_at", s), p.get("end_at", e)   # hand overrides where words run together
        for ss, se in squeeze(db, s, e):
            seg = a[int(ss * sr):int(se * sr)].copy()
            seg[:fade] *= ramp
            seg[-fade:] *= ramp[::-1]
            voice.append(seg)
            d = len(seg) / sr
            ws = [dict(w=w["w"], t=round(t + max(w["s"], ss) - ss, 3), end=round(t + min(w["e"], se) - ss, 3))
                  for w in kept if ss - 0.2 <= w["s"] < se]
            kept = [w for w in kept if w["s"] >= se]
            edl.append(dict(piece=p["id"], out=[round(t, 3), round(t + d, 3)], src=[round(ss, 3), round(se, 3)], words=ws))
            t += d
    v = np.concatenate(voice)
    natural = os.path.join(out, "voice_1x.wav")
    with wave.open(natural, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(v, -1, 1) * 32767).astype(np.int16).tobytes())
    # Rubber Band keeps formants, so the faster voice still sounds like the same person
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", natural, "-af",
                    f"rubberband=tempo={speed}:formant=preserved:pitchq=quality:window=short",
                    os.path.join(out, "voice.wav")], check=True)
    for sp in edl:
        sp["out"] = [round(x / speed, 3) for x in sp["out"]]
        for w in sp["words"]:
            w["t"], w["end"] = round(w["t"] / speed, 3), round(w["end"] / speed, 3)
    t /= speed
    json.dump(dict(duration=round(t, 3), speed=speed, spans=edl), open(os.path.join(out, "edl.json"), "w"), indent=1)
    for sp in edl:
        print(f"{sp['piece']} out {sp['out'][0]:6.2f}-{sp['out'][1]:6.2f}  src {sp['src'][0]:7.2f}-{sp['src'][1]:7.2f}  "
              + " ".join(f"{w['w']}@{w['t']:.2f}" for w in sp["words"]))
    print(f"total {t:.2f}s")


if __name__ == "__main__":
    main()
