#!/usr/bin/env python3
"""Fit the user's voice phrases into the reference reel's phrase timing.

usage: retime.py voice48.wav OUT_raw.wav OUT_map.json
Each phrase = list of (start, end) cuts in the user's recording + the reference start of that phrase.
The phrase is compressed (internal pauses shortened) and, only if still too long, time-stretched with
rubberband so it ends before the next reference phrase starts.
"""
import json, os, subprocess, sys, tempfile, wave
import numpy as np

SR = 48000
# id, text, reference start, reference start of the next phrase, user cuts
PHRASES = [
    ("A", "How to get clients as a video editor?", 0.34, 3.28, [(0.95, 3.22)]),
    ("B", "This is probably the most asked question on this page.", 3.30, 6.38, [(3.52, 3.95), (4.68, 7.38)]),
    ("C", "And let me break it down for you.", 6.38, 7.84, [(8.40, 10.16)]),
    ("D", "Step 1.", 7.86, 8.68, [(11.76, 12.70)]),
    ("E", "Pick a niche.", 8.70, 9.42, [(13.04, 13.93)]),
    ("F", "Stop editing everything.", 9.44, 10.64, [(14.58, 16.06)]),
    ("G", "Pick one niche out of these and be known for one thing.", 10.66, 13.66, [(22.62, 26.24)]),
    ("H", "Step 2.", 13.70, 14.60, [(26.84, 27.55)]),
    ("I", "Build a portfolio.", 14.62, 15.66, [(27.85, 28.99)]),
    ("J", "Without clients you can still make a portfolio,", 15.68, 17.74, [(29.77, 32.54)]),
    ("K", "shoot your own footage", 17.76, 18.66, [(33.13, 34.24)]),
    ("L", "or use free clips from the internet", 18.68, 20.66, [(34.24, 36.66)]),
    ("M", "and create your best work.", 20.68, 22.58, [(36.66, 38.36)]),
    ("N", "Now put all the best work on a professional portfolio website,", 22.60, 25.80, [(39.42, 43.16)]),
    ("O", "don't just use Google Drive.", 25.82, 27.26, [(46.08, 47.72)]),
    ("P", "Now step 3.", 27.28, 28.24, [(49.32, 50.55)]),
    ("Q", "Outreach.", 28.26, 28.95, [(50.62, 51.34)]),
    ("R", "Send 20 to 30 DMs and emails every day", 28.99, 31.70, [(51.70, 54.79)]),
    ("S", "to these specific people you can find on Instagram", 31.72, 34.00, [(55.50, 58.40)]),
    ("T", "and you can also get my exact outreach template if you just comment clients.", 34.02, 38.46,
     [(71.45, 71.86), (72.50, 74.22), (75.06, 78.28)]),
    ("U", "Now step 4.", 38.48, 39.38, [(79.00, 80.04)]),
    ("V", "Overdeliver.", 39.40, 40.06, [(80.25, 81.10)]),
    ("W", "Because this is your first client, be reliable,", 40.08, 42.54, [(81.46, 84.57)]),
    ("X", "communicate well and give the best edit to your client.", 42.56, 45.36, [(84.87, 88.31)]),
    ("Y", "Because one happy client can bring in 10 more.", 45.38, 48.08, [(89.40, 92.38), (93.72, 94.70)]),
    ("Z", "Now fifth and final step, build your personal brand.", 48.10, 51.00, [(95.75, 99.07)]),
    ("AA", "You can post before and after edits, BTS and edit breakdowns", 51.04, 54.64,
     [(99.72, 102.16), (102.40, 103.08), (113.28, 114.74)]),
    ("AB", "which can get you a lot of clients in the long run.", 54.66, 57.40, [(116.84, 120.52)]),
]


def read(path):
    w = wave.open(path)
    return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768.0


def write(path, x):
    w = wave.open(path, "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()


def fade(x, ms=6):
    n = int(SR * ms / 1000)
    if len(x) > 2 * n:
        r = np.linspace(0, 1, n, dtype=np.float32); x = x.copy(); x[:n] *= r; x[-n:] *= r[::-1]
    return x


def squeeze_pauses(x, thr_db=-38.0, min_gap=0.12, keep=0.07):
    """Shorten silent stretches longer than min_gap down to `keep` seconds."""
    hop = int(SR * 0.01)
    n = len(x) // hop
    rms = np.array([np.sqrt(np.mean(x[i * hop:(i + 1) * hop] ** 2) + 1e-12) for i in range(n)])
    db = 20 * np.log10(rms)
    quiet = db < thr_db
    out, i = [], 0
    while i < n:
        if quiet[i]:
            j = i
            while j < n and quiet[j]:
                j += 1
            gap = (j - i) * hop / SR
            # leave leading/trailing silence alone; they are trimmed by the cuts already
            if gap > min_gap and i > 0 and j < n:
                k = int(keep * SR / hop)
                out.append(x[i * hop:(i + k // 2) * hop]); out.append(x[(j - k // 2) * hop:j * hop])
            else:
                out.append(x[i * hop:j * hop])
            i = j
        else:
            j = i
            while j < n and not quiet[j]:
                j += 1
            out.append(x[i * hop:j * hop]); i = j
    out.append(x[n * hop:])
    return np.concatenate(out)


def stretch(x, ratio):
    if ratio <= 1.001:
        return x
    with tempfile.TemporaryDirectory() as d:
        a, b = os.path.join(d, "a.wav"), os.path.join(d, "b.wav")
        write(a, x)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a, "-af",
                        f"rubberband=tempo={ratio:.4f}:pitchq=quality:formant=preserved:transients=mixed", b], check=True)
        return read(b)


def main():
    src, out_wav, out_map = sys.argv[1], sys.argv[2], sys.argv[3]
    a = read(src)
    total = PHRASES[-1][3] + 0.2
    y = np.zeros(int(SR * (total + 1)), np.float32)
    report = []
    for pid, text, rs, rnext, cuts in PHRASES:
        parts = []
        for k, (s, e) in enumerate(cuts):
            parts.append(fade(a[int(s * SR):int(e * SR)]))
            if k < len(cuts) - 1:
                parts.append(np.zeros(int(SR * 0.06), np.float32))
        x = squeeze_pauses(np.concatenate(parts))
        win = (rnext - 0.04) - rs
        ratio = max(1.0, (len(x) / SR) / win)
        x = fade(stretch(x, ratio), 4)
        i = int(rs * SR)
        y[i:i + len(x)] += x[: len(y) - i]
        report.append(dict(id=pid, text=text, start=rs, end=round(rs + len(x) / SR, 3), ratio=round(ratio, 3)))
        print(f"{pid:3s} {rs:6.2f}-{rs + len(x) / SR:6.2f}  x{ratio:4.2f}  {text}")
    end = max(r["end"] for r in report)
    write(out_wav, y[: int(SR * (end + 0.05))])
    json.dump(report, open(out_map, "w"), indent=1)


if __name__ == "__main__":
    main()
