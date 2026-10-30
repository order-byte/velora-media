"""Splits the clip into harmonic (music) and percussive (hits, clicks, swooshes) parts,
then lists the strongest isolated percussive events as candidate sound effects."""
import subprocess, json
import numpy as np
from scipy.ndimage import median_filter
from scipy.signal import stft, istft
import soundfile as sf

SR = 48000
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", "src1.wav", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
x = np.frombuffer(raw, np.float32).reshape(-1, 2).T
nper, hop = 2048, 512
perc = []
for ch in x:
    f, t, Z = stft(ch, SR, nperseg=nper, noverlap=nper - hop)
    M = np.abs(Z)
    H = median_filter(M, size=(1, 31))      # smooth across time  -> sustained tones
    P = median_filter(M, size=(31, 1))      # smooth across freq  -> broadband hits
    mask = P ** 2 / (H ** 2 + P ** 2 + 1e-12)
    _, y = istft(Z * mask ** 2, SR, nperseg=nper, noverlap=nper - hop)
    perc.append(y[: ch.size])
perc = np.array(perc)
sf.write("perc.wav", perc.T, SR)
mono = perc.mean(0)
# event strength = short-time energy above 3 kHz (music kicks/bass sit lower)
f, t, Z = stft(mono, SR, nperseg=1024, noverlap=1024 - 240)
hi = (np.abs(Z[f > 3000]) ** 2).sum(0)
env = 10 * np.log10(hi + 1e-12)
dt = t[1] - t[0]
order = np.argsort(env)[::-1]
picked = []
for i in order:
    if len(picked) >= 14: break
    if all(abs(t[i] - p) > 0.45 for p in picked): picked.append(float(t[i]))
picked.sort()
json.dump(picked, open("events.json", "w"))
for p in picked:
    i = int(p / dt)
    print(f"event at {p:5.2f}s  hi-band {env[i]:5.1f} dB")
