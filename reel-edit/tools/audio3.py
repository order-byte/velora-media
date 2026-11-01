#!/usr/bin/env python3
"""v3 mix: reference music+SFX bed (vocals removed) + retimed voice + closing-selfie audio.
usage: audio3.py bed48.wav voice2_final.wav IMG_4985.mp4 OUT.wav TOTAL CTA_START"""
import sys, subprocess, wave
import numpy as np
SR = 48000


def read(path):
    w = wave.open(path); n = w.getnchannels()
    x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768.0
    return x.reshape(-1, n) if n > 1 else x[:, None]


bed_p, voice_p, cta_p, out, total, cta_t = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], float(sys.argv[5]), float(sys.argv[6])
N = int(SR * (total + 0.2))
bed = read(bed_p)
if bed.shape[1] == 1: bed = np.repeat(bed, 2, 1)
# extend the bed: repeat the last 8 beats (128 bpm) with a short crossfade, then fade out
beat = 60 / 128.0
end = min(int(61.10 * SR), len(bed)); loop0 = end - int(8 * beat * SR)
ext = bed[loop0:end].copy()
xf = int(0.06 * SR)
out_bed = np.zeros((N, 2), np.float32)
out_bed[:min(N, end)] = bed[:min(N, end)]
r = np.linspace(0, 1, xf)[:, None]
pos = end - xf
seg = ext.copy(); seg[:xf] *= r
out_bed[pos:pos + xf] *= (1 - r)
m = min(len(seg), N - pos); out_bed[pos:pos + m] += seg[:m]
fade_len = int(1.3 * SR); fe = N - int(0.2 * SR)
out_bed[fe - fade_len:fe] *= np.linspace(1, 0, fade_len)[:, None]; out_bed[fe:] = 0
# voice
v = read(voice_p)[:, 0]
vox = np.zeros(N, np.float32); vox[:min(N, len(v))] = v[:N]
# closing selfie audio, same cleanup chain as the voice (no speed change)
tmp = out + ".cta.wav"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "0.25", "-t", "5.70", "-i", cta_p, "-vn", "-ac", "1", "-ar", str(SR), "-af",
                "highpass=f=90,afftdn=nf=-30:nr=12,equalizer=f=250:t=q:w=1.2:g=-3,equalizer=f=3800:t=q:w=1:g=3,deesser=i=0.35,"
                "acompressor=threshold=-20dB:ratio=3.2:attack=4:release=90:makeup=2.5,loudnorm=I=-14:TP=-1.5:LRA=6,afade=t=out:st=5.5:d=0.2", tmp], check=True)
c = read(tmp)[:, 0]; i0 = int(cta_t * SR)
vox[i0:i0 + len(c)] += c[:max(0, N - i0)]
mix = out_bed + vox[:, None]
raw = out + ".raw.wav"
w = wave.open(raw, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", "loudnorm=I=-14:TP=-1.0:LRA=9", "-ar", str(SR), out], check=True)
print("mix ok", out)
