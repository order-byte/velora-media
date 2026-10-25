"""Measure tempo, energy and structure of candidate tracks.

usage: analyze_tracks.py DIR OUT.json
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from scipy import signal

SR = 22050
HOP = 512


def decode(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


def onset_env(x):
    f, t, Z = signal.stft(x, SR, nperseg=2048, noverlap=2048 - HOP)
    mag = np.log1p(np.abs(Z) * 100)
    flux = np.maximum(0, np.diff(mag, axis=1)).sum(0)
    flux = np.concatenate([[0], flux])
    flux = flux - signal.medfilt(flux, 31)
    return np.maximum(flux, 0), np.abs(Z), f


def tempo(env):
    fps = SR / HOP
    env = env - env.mean()
    ac = np.correlate(env, env, "full")[len(env) - 1:]
    lags = np.arange(len(ac)) / fps
    bpm = 60 / np.maximum(lags, 1e-9)
    sel = (bpm >= 85) & (bpm <= 180)
    # weight toward the 110-140 dance range
    w = np.exp(-0.5 * (np.log2(bpm[sel] / 125) / 0.5) ** 2)
    i = np.argmax(ac[sel] * w)
    lag = np.where(sel)[0][i]
    # parabolic refine
    if 1 <= lag < len(ac) - 1:
        a, b, c = ac[lag - 1], ac[lag], ac[lag + 1]
        lag = lag + 0.5 * (a - c) / (a - 2 * b + c + 1e-12)
    return 60 * fps / lag, float(ac[int(round(lag))] / (ac[0] + 1e-12))


def main():
    d = Path(sys.argv[1])
    out = []
    for p in sorted(d.glob("*.mp3"), key=lambda q: int(q.stem)):
        x = decode(p)
        dur = len(x) / SR
        env, mag, f = onset_env(x)
        bpm, beat_strength = tempo(env)
        # energy per 2-second window
        win = int(2 * SR)
        rms = np.array([np.sqrt((x[i:i + win] ** 2).mean() + 1e-12) for i in range(0, len(x) - win, win)])
        db = 20 * np.log10(rms)
        top = np.percentile(db, 90)
        loud_frac = float((db > top - 3).mean())
        # biggest jump between consecutive 4-second blocks (a drop)
        blk = np.convolve(db, np.ones(2) / 2, "valid")
        jumps = blk[2:] - blk[:-2]
        drop_i = int(np.argmax(jumps))
        drop_t = (drop_i + 2) * 2.0
        # brightness: energy above 4 kHz relative to total, in the loudest region
        hi = mag[f > 4000].sum() / (mag.sum() + 1e-9)
        # rhythmic energy: mean onset strength in the loudest half
        frames_per_win = win // HOP
        strong = [env[i * frames_per_win:(i + 1) * frames_per_win].mean() for i in range(len(db)) if db[i] > np.median(db)]
        rhythm = float(np.mean(strong)) if strong else 0.0
        stretch = 128.5714 / bpm
        # if the tempo is half/double, consider the closest octave
        for k in (0.5, 2.0):
            if abs(np.log2(128.5714 / (bpm * k))) < abs(np.log2(stretch)):
                stretch = 128.5714 / (bpm * k)
        out.append({"id": p.stem, "dur": round(dur, 1), "bpm": round(bpm, 2), "beat_strength": round(beat_strength, 3),
                    "loud_db": round(float(top), 1), "dyn_range": round(float(top - np.percentile(db, 10)), 1),
                    "drop_jump_db": round(float(jumps.max()), 1), "drop_t": drop_t, "loud_frac": round(loud_frac, 2),
                    "bright": round(float(hi), 3), "rhythm": round(rhythm, 2), "stretch_pct": round((stretch - 1) * 100, 1)})
        r = out[-1]
        print(f"{r['id']:>5} dur={r['dur']:6.1f} bpm={r['bpm']:6.1f} stretch={r['stretch_pct']:+5.1f}% beat={r['beat_strength']:.2f} "
              f"loud={r['loud_db']:5.1f} dyn={r['dyn_range']:4.1f} drop={r['drop_jump_db']:4.1f}@{r['drop_t']:5.0f}s "
              f"bright={r['bright']:.3f} rhythm={r['rhythm']:.1f}", flush=True)
    json.dump(out, open(sys.argv[2], "w"), indent=1)


if __name__ == "__main__":
    main()
