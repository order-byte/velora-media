"""Mixes the reel's soundtrack: voice + music (Aphelion by Scott Buckley, CC BY 4.0) + sound
effects built only from the hits cut out of the reference clip (sfx/lib).

Reads timing.json, events.json (written by render.js), voice.wav; writes audio.wav.
"""
import json
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import butter, fftconvolve, sosfilt

HERE = Path(__file__).resolve().parent
LIB = HERE.parent / "sfx" / "lib"
MUSIC = HERE.parent / "dl-music" / "Aphelion.mp3"
SR = 48000
MUSIC_PEAK = 132.0          # seconds into Aphelion where the build reaches its peak
rng = np.random.default_rng(5)


def load(name):
    x, sr = sf.read(LIB / f"{name}.wav", always_2d=True)
    return x.astype(np.float64)


def pitch(x, f):
    """Resample-style pitch/time shift: f < 1 is lower and longer."""
    n = int(len(x) / f)
    src = np.arange(n) * f
    return np.stack([np.interp(src, np.arange(len(x)), x[:, c]) for c in range(2)], 1)


def filt(x, kind, hz):
    sos = butter(2, hz, kind, fs=SR, output="sos")
    return sosfilt(sos, x, axis=0)


def reverb(x, secs, wet):
    n = int(secs * SR)
    t = np.arange(n) / SR
    ir = rng.standard_normal((n, 2)) * np.exp(-t * 6.9 / secs)[:, None]
    ir = filt(ir, "low", 6000)
    ir /= np.sqrt((ir ** 2).sum(0))
    out = np.zeros((len(x) + n - 1, 2))
    for c in range(2):
        out[:, c] = fftconvolve(x[:, c], ir[:, c])
    dry = np.zeros_like(out); dry[: len(x)] = x
    return dry * (1 - wet) + out * wet * 1.6


def norm(x, peak=0.9):
    return x * (peak / (np.abs(x).max() + 1e-9))


def fade(x, fi=0.004, fo=0.05):
    a, b = int(fi * SR), int(fo * SR)
    x = x.copy()
    if a: x[:a] *= np.linspace(0, 1, a)[:, None]
    if b and b < len(x): x[-b:] *= np.linspace(1, 0, b)[:, None]
    return x


def kit():
    k = {}
    k["boom"] = norm(filt(reverb(pitch(load("hit_0"), 0.45), 2.8, 0.45), "low", 900))
    hit = pitch(load("hit_0"), 0.7); hit1 = load("hit_1")
    m = np.zeros((max(len(hit), len(hit1)), 2)); m[: len(hit)] += hit; m[: len(hit1)] += hit1 * 0.6
    k["impact"] = norm(reverb(m, 1.6, 0.35))
    for i in range(3):
        w = fade(pitch(load(f"whoosh_{i}"), 0.55), 0.06, 0.12)
        k[f"whoosh_{i}"] = norm(reverb(w, 1.2, 0.4))
    grains = np.zeros((int(0.6 * SR), 2))
    for g in range(9):
        src = load("click_3" if g % 2 else "hit_3")
        src = pitch(src, rng.uniform(0.9, 1.6)) * (0.9 ** g)
        o = int(rng.uniform(0, 0.25) * SR)
        e = min(len(grains), o + len(src)); grains[o:e] += src[: e - o]
    k["shatter"] = norm(reverb(grains, 1.0, 0.3))
    k["tick"] = norm(fade(filt(load("click_0"), "high", 1500), 0.002, 0.03))
    sp = pitch(load("click_2"), 1.6); sp2 = pitch(load("click_1"), 2.0)
    m = np.zeros((len(sp) + int(0.09 * SR) + len(sp2), 2)); m[: len(sp)] += sp; o = int(0.09 * SR); m[o:o + len(sp2)] += sp2 * 0.7
    k["sparkle"] = norm(filt(reverb(m, 2.0, 0.6), "high", 2000))
    r = reverb(pitch(load("hit_1"), 0.8), 3.5, 1.0)[::-1]
    k["riser"] = norm(fade(r, 0.3, 0.01))
    return k


def main():
    timing = json.loads((HERE / "timing.json").read_text())
    events = json.loads((HERE / "events.json").read_text())
    dur = timing["duration"]
    n = int(np.ceil(dur * SR))
    K = kit()
    sfx = np.zeros((n, 2))

    def put(name, t, db):
        x = K[name] * 10 ** (db / 20)
        a = int(max(0, t) * SR); b = min(n, a + len(x))
        if b > a: sfx[a:b] += x[: b - a]

    plan = {
        "globe": [("boom", 0, -4)], "crack": [("impact", 0, -3)], "explode": [("whoosh_0", 0, -2), ("boom", 0.05, -6)],
        "tokens": [("whoosh_1", 0, -5)], "claimCard": [("whoosh_2", 0, -7)], "safe": [("sparkle", 0.1, -6)],
        "revenue": [("whoosh_1", 0, -8)], "blocked": [("impact", 0.2, -9)], "card": [("whoosh_0", 0, -7)],
        "shatter": [("shatter", 0, -3), ("impact", 0, -6)], "strikeMark": [("impact", 0.15, -2)], "stumps": [("whoosh_2", 0, -6)],
        "wicket": [("impact", 0.05, -1), ("shatter", 0.08, -8)],
        "threeWickets": [("impact", 0.3, -8), ("impact", 0.52, -7), ("impact", 0.74, -6)], "globeDark": [("boom", 0.1, -3)],
        "warnings": [("impact", 0.2, -8), ("impact", 0.5, -8)], "trash": [("whoosh_0", 0, -7), ("impact", 0.6, -9)],
        "dispute": [("whoosh_1", 0, -7)], "tagToStrike": [("impact", 0.1, -3)], "dm": [("boom", 0.2, -3), ("sparkle", 0.35, -4)],
    }
    dm_t = None
    for e in events["shapes"]:
        for name, off, db in plan.get(e["shape"], []):
            put(name, e["t"] + off, db)
        if e["shape"] == "dm":
            dm_t = e["t"]
    if dm_t is not None:
        put("riser", dm_t + 0.25 - len(K["riser"]) / SR, -6)
    for t in events["text"]:
        put("tick", t + 0.05, -15)

    voice, _ = sf.read(HERE / "voice.wav")
    voice = np.stack([voice, voice], 1)[:n]

    offset = max(0.0, MUSIC_PEAK - (dm_t or dur - 6))
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{offset:.3f}", "-t", f"{dur + 1:.3f}", "-i", str(MUSIC),
                          "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"], check=True, capture_output=True).stdout
    music = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)[:n]
    music = np.pad(music, ((0, n - len(music)), (0, 0)))
    # duck under the voice, open up after the last line
    act = (np.abs(voice[:, 0]) > 0.02).astype(float)
    win = int(0.25 * SR)
    act = np.convolve(act, np.ones(win) / win, "same")
    act = np.convolve(np.clip(act * 4, 0, 1), np.ones(win) / win, "same")
    gain = 10 ** ((-7 * act) / 20)
    music *= gain[:, None]
    fi, fo = int(1.5 * SR), int(2.8 * SR)
    music[:fi] *= np.linspace(0, 1, fi)[:, None]
    music[-fo:] *= np.linspace(1, 0, fo)[:, None]
    music = norm(music, 0.55)

    mix = voice * 1.0 + music * 0.62 + sfx * 0.42
    raw = HERE / "mix.f32"
    raw.write_bytes(np.clip(mix, -1, 1).astype(np.float32).tobytes())
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", str(raw),
                    "-af", "loudnorm=I=-14:TP=-1.2:LRA=11", "-ar", str(SR), str(HERE / "audio.wav")], check=True)
    raw.unlink()
    print(f"mixed {dur:.2f}s, music from {offset:.1f}s of Aphelion, dm at {dm_t}")


if __name__ == "__main__":
    main()
