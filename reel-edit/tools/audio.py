#!/usr/bin/env python3
"""Synthesised SFX + voice mix for the reel.  usage: audio.py events.json voice.wav cta_clip.mp4 OUT.wav TOTAL"""
import json, sys, subprocess, wave
import numpy as np
from scipy import signal

SR = 48000
rng = np.random.default_rng(42)


def env(n, a=0.005, r=0.2, curve=3.0):
    t = np.arange(n) / SR
    e = np.minimum(1.0, t / max(a, 1e-4)) * np.exp(-t / max(r, 1e-4) * 1.0)
    return e


def bandnoise(n, lo, hi):
    x = rng.normal(0, 1, n)
    b, a = signal.butter(2, [lo / (SR / 2), min(hi, SR / 2 - 100) / (SR / 2)], "band")
    return signal.lfilter(b, a, x)


def whoosh(d=0.42):
    n = int(SR * d)
    x = rng.normal(0, 1, n)
    out = np.zeros(n)
    # sweeping band-pass, processed in blocks
    blk = 512
    for i in range(0, n, blk):
        p = i / n
        fc = 300 + 4200 * np.sin(np.pi * p) ** 1.5
        b, a = signal.butter(2, [max(80, fc * 0.5) / (SR / 2), min(fc * 1.6, 20000) / (SR / 2)], "band")
        out[i:i + blk] = signal.lfilter(b, a, x[i:i + blk])
    e = np.sin(np.pi * np.linspace(0, 1, n)) ** 2
    return out * e * 0.9


def impact(d=1.1, strong=True):
    n = int(SR * d); t = np.arange(n) / SR
    sub = np.sin(2 * np.pi * (48 + 40 * np.exp(-t * 18)) * t) * np.exp(-t * 3.2)
    thump = bandnoise(n, 60, 400) * np.exp(-t * 22) * 0.8
    crack = bandnoise(n, 2000, 9000) * np.exp(-t * 45) * 0.35
    tail = bandnoise(n, 200, 2500) * np.exp(-t * 4.5) * 0.08
    x = sub * (1.0 if strong else 0.55) + thump + crack + tail
    return np.tanh(x * 1.6) * (0.95 if strong else 0.6)


def pop(d=0.09, f0=950):
    n = int(SR * d); t = np.arange(n) / SR
    f = f0 * np.exp(-t * 18)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 45) * 0.55


def click(d=0.04):
    n = int(SR * d); t = np.arange(n) / SR
    return (bandnoise(n, 1500, 9000) * np.exp(-t * 160) + np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 120) * 0.4) * 0.5


def typing(d=1.6):
    n = int(SR * d); out = np.zeros(n)
    t = 0.0
    while t < d - 0.06:
        c = click(0.035) * rng.uniform(0.35, 0.7)
        i = int(t * SR); out[i:i + len(c)] += c[: max(0, n - i)]
        t += rng.uniform(0.06, 0.13)
    return out


def shimmer(d=1.2):
    n = int(SR * d); t = np.arange(n) / SR
    x = np.zeros(n)
    for f in (2093, 2637, 3136, 4186, 5274):
        x += np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * (0.5 + 0.5 * np.sin(2 * np.pi * rng.uniform(6, 11) * t))
    return x / 5 * np.minimum(1, t / 0.05) * np.exp(-t * 2.4) * 0.45


def riser(d=1.4):
    n = int(SR * d); t = np.arange(n) / SR
    p = t / d
    f = 200 + 1600 * p ** 2
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.25
    noise = bandnoise(n, 800, 8000) * 0.5
    return (tone + noise) * p ** 2.2 * 0.7


def ding(d=1.2):
    n = int(SR * d); t = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * f * t) * a for f, a in ((1568, 1), (3136, .4), (4704, .2)))
    return x * np.exp(-t * 3.5) * 0.35


def shutter():
    return np.concatenate([click(0.05) * 1.2, np.zeros(int(SR * 0.06)), click(0.06) * 0.9])


def bubble():
    return pop(0.07, f0=rng.uniform(700, 1300)) * 0.5


SFX = {
    "whoosh": (lambda: whoosh(0.42), 0.55, -0.21),
    "hit": (lambda: impact(0.9, False), 0.6, 0.0),
    "impact": (lambda: impact(1.2, True), 0.75, 0.0),
    "impact_s": (lambda: impact(0.8, False), 0.5, 0.0),
    "pop": (lambda: pop(), 0.35, 0.0),
    "click": (lambda: click(), 0.5, 0.0),
    "typing": (lambda: typing(2.0), 0.45, 0.0),
    "shimmer": (lambda: shimmer(1.3), 0.6, 0.0),
    "riser": (lambda: riser(1.0), 0.4, -0.2),
    "riser_long": (lambda: riser(1.9), 0.55, 0.0),
    "ding": (lambda: ding(), 0.5, 0.0),
    "shutter": (lambda: shutter(), 0.6, 0.0),
    "bubble": (lambda: bubble(), 0.35, 0.0),
}


def read_wav(path):
    w = wave.open(path)
    x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768.0
    if w.getnchannels() == 2:
        x = x.reshape(-1, 2).mean(1)
    assert w.getframerate() == SR, w.getframerate()
    return x


def main():
    events, voice, cta_clip, out, total = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], float(sys.argv[5])
    n = int(SR * total)
    vox = np.zeros(n, np.float32); fxbus = np.zeros(n, np.float32)
    v = read_wav(voice); vox[: min(n, len(v))] += v[: n]
    # closing selfie: its own audio, cleaned with the same chain as the voiceover (no speed-up)
    cta = out + ".cta.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "0.25", "-t", "5.75", "-i", cta_clip, "-vn", "-ac", "1", "-ar", str(SR),
                    "-af", "highpass=f=90,afftdn=nf=-30:nr=12,equalizer=f=250:t=q:w=1.2:g=-3,equalizer=f=3800:t=q:w=1:g=3,"
                           "deesser=i=0.35,acompressor=threshold=-20dB:ratio=3.2:attack=4:release=90:makeup=2.5,loudnorm=I=-14:TP=-1.5:LRA=6,"
                           "afade=t=out:st=5.55:d=0.2", cta], check=True)
    c = read_wav(cta); i0 = int(62.10 * SR)
    vox[i0:i0 + len(c)] += c[: max(0, n - i0)]
    for name, t in json.load(open(events)):
        if name not in SFX:
            continue
        gen, gain, off = SFX[name]
        x = gen().astype(np.float32) * gain
        i = int((t + off) * SR)
        if i < 0:
            x = x[-i:]; i = 0
        if i >= n:
            continue
        m = min(len(x), n - i); fxbus[i:i + m] += x[:m]
    # duck SFX a little under the voice
    venv = np.abs(signal.lfilter([1], [1, -0.9995], np.abs(vox))) * (1 - 0.9995)
    venv = venv / (venv.max() + 1e-9)
    duck = 1.0 - 0.35 * np.clip(venv * 4, 0, 1)
    mix = vox + fxbus * 0.8 * duck
    stereo = np.stack([mix, mix], 1)
    tmp = out + ".raw.wav"
    w = wave.open(tmp, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(stereo, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af", "loudnorm=I=-14:TP=-1.0:LRA=9", "-ar", str(SR), out], check=True)
    print("audio ok", out)


if __name__ == "__main__":
    main()
