"""Cuts individual sound effects out of the percussive layer of the clip and sorts them
into clicks, hits and whooshes, keeping the ones that sound least like the music."""
import json, os
import numpy as np
import soundfile as sf
from scipy.signal import stft, butter, sosfiltfilt

SR = 48000
perc, _ = sf.read("perc.wav")              # stereo, percussive layer
mono = perc.mean(1)
hop = 240
f, t, Z = stft(mono, SR, nperseg=1024, noverlap=1024 - hop)
M = np.abs(Z)
flux = np.maximum(0, np.diff(np.log1p(M * 50), axis=1)).sum(0)
flux = np.concatenate([[0], flux])
thr = np.median(flux) + 1.8 * flux.std()
on = [i for i in range(1, len(flux) - 1) if flux[i] > thr and flux[i] >= flux[i - 1] and flux[i] >= flux[i + 1]]
ons, last = [], -999
for i in on:
    if i - last > 12:
        ons.append(i); last = i
rms = np.sqrt((M ** 2).mean(0))
db = 20 * np.log10(rms + 1e-9)
sos = butter(4, 140, 'hp', fs=SR, output='sos')
os.makedirs("lib", exist_ok=True)
cands = []
for k, i in enumerate(ons):
    t0 = t[i]
    nxt = t[ons[k + 1]] if k + 1 < len(ons) else t[-1]
    peak_i = i + int(np.argmax(db[i:i + 20]))
    pk = db[peak_i]
    j = peak_i
    while j < len(db) - 1 and db[j] > pk - 28 and t[j] - t0 < 0.9:
        j += 1
    end = min(t[j], nxt + 0.05)
    dur = end - t0
    if dur < 0.04:
        continue
    seg = M[:, i:j + 1]
    band = (f > 200) & (f < 15000)
    spec = seg[band].mean(1) + 1e-9
    flat = float(np.exp(np.log(spec).mean()) / spec.mean())
    low = float((seg[f < 250] ** 2).sum() / ((seg ** 2).sum() + 1e-12))
    around = db[max(0, i - 80): i - 4]
    contrast = float(pk - (np.median(around) if around.size else pk))
    attack = float(t[peak_i] - t0)
    kind = "click" if dur < 0.14 else ("whoosh" if attack > 0.05 and dur > 0.22 else "hit")
    cands.append(dict(t=float(t0), dur=float(dur), flat=flat, low=low, contrast=contrast, attack=attack, peak=float(pk), kind=kind))

def score(c):
    return c["flat"] * 4 + c["contrast"] / 10 + (0.3 if c["kind"] == "whoosh" else 0)

out = {}
for kind, n in (("click", 4), ("hit", 4), ("whoosh", 4)):
    best = sorted([c for c in cands if c["kind"] == kind], key=score, reverse=True)[:n]
    for m, c in enumerate(best):
        a = max(0, int((c["t"] - 0.008) * SR)); b = int((c["t"] + c["dur"]) * SR)
        x = sosfiltfilt(sos, perc[a:b], axis=0)
        fi, fo = int(0.003 * SR), min(int(0.04 * SR), (b - a) // 3)
        x[:fi] *= np.linspace(0, 1, fi)[:, None]
        x[-fo:] *= np.linspace(1, 0, fo)[:, None]
        x /= np.abs(x).max() + 1e-9
        name = f"{kind}_{m}"
        sf.write(f"lib/{name}.wav", (x * 0.9).astype(np.float32), SR)
        out[name] = c
        print(f"{name:9s} at {c['t']:5.2f}s dur {c['dur']:.2f} flat {c['flat']:.2f} contrast {c['contrast']:4.1f} attack {c['attack']:.3f} low {c['low']:.2f}")
json.dump(out, open("lib/index.json", "w"), indent=1)
print(len(cands), "candidates")
