# Assemble the voiceover from the best takes. Times are in the original recording.
import json, sys, wave, numpy as np
SR = 48000
w = wave.open(sys.argv[1]); a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
# (label, [(start,end),...], gap_after_seconds)
PLAN = [
 ("v01_hook",      [(0.95, 3.22)], 0.16),
 ("v02_question",  [(3.52, 3.95), (4.68, 7.38)], 0.22),
 ("v03_break",     [(8.40, 10.16)], 0.24),
 ("v04_step1",     [(11.76, 12.70)], 0.10),
 ("v05_niche",     [(13.04, 13.93)], 0.14),
 ("v06_stop",      [(14.58, 16.06)], 0.14),
 ("v07_pickone",   [(22.62, 26.24)], 0.24),
 ("v08_step2",     [(26.84, 28.99)], 0.16),
 ("v09_without",   [(29.77, 32.54)], 0.14),
 ("v10_shoot",     [(33.13, 38.36)], 0.22),
 ("v11_putall",    [(39.42, 43.16)], 0.10),
 ("v12_drive",     [(46.08, 47.72)], 0.24),
 ("v13_step3",     [(49.32, 51.34)], 0.12),
 ("v14_send",      [(51.70, 54.79), (55.50, 58.40)], 0.18),
 ("v15_template",  [(71.45, 71.86), (72.50, 74.22), (75.06, 78.28)], 0.24),
 ("v16_step4",     [(79.00, 81.10)], 0.10),
 ("v17_because",   [(81.46, 84.57)], 0.10),
 ("v18_communic",  [(84.87, 88.31)], 0.16),
 ("v19_happy",     [(89.40, 92.38), (93.72, 94.70)], 0.24),
 ("v20_step5",     [(95.75, 99.07)], 0.16),
 ("v21_post",      [(99.72, 102.16), (102.40, 103.08), (113.28, 114.74)], 0.14),
 ("v22_longrun",   [(116.84, 120.52)], 0.0),
]
def fade(x, ms=6):
    n = int(SR * ms / 1000); 
    if len(x) > 2 * n:
        r = np.linspace(0, 1, n); x = x.copy(); x[:n] *= r; x[-n:] *= r[::-1]
    return x
out, marks, t = [], [], 0.0
for label, cuts, gap in PLAN:
    start_t = t
    for i, (s, e) in enumerate(cuts):
        seg = fade(a[int(s * SR):int(e * SR)])
        out.append(seg); t += len(seg) / SR
        if i < len(cuts) - 1:
            g = np.zeros(int(SR * 0.07), np.float32); out.append(g); t += len(g) / SR
    marks.append({"label": label, "start": round(start_t, 3), "end": round(t, 3)})
    if gap:
        g = np.zeros(int(SR * gap), np.float32); out.append(g); t += len(g) / SR
y = np.concatenate(out)
wo = wave.open(sys.argv[2], "wb"); wo.setnchannels(1); wo.setsampwidth(2); wo.setframerate(SR)
wo.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes()); wo.close()
json.dump(marks, open(sys.argv[3], "w"), indent=1)
print("raw voice length %.2fs" % t)
