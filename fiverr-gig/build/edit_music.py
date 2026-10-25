"""Cut a produced track to the reel's 28-bar structure at 128.5714 BPM.

usage: edit_music.py TRACK.mp3 OUT.wav REPORT.json

Reel bars (0-based): 0-3 intro/build into drop A, 4-11 drop A, 12-15 breakdown, 16-23 drop B,
24-27 outro, then a 1.2 s tail. Cuts land on downbeats with short crossfades.
"""
import json
import subprocess
import sys

import numpy as np
from scipy import signal

SR = 48000
TARGET_BPM = 1800 / 14  # 14 frames per beat at 30 fps
BAR_T = 4 * 60 / TARGET_BPM
N_BARS = 28
TAIL = 1.2
OUT_DUR = N_BARS * BAR_T + TAIL


def decode(path, extra=()):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), *extra, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()


def onset_env(mono, sr, hop):
    f, t, Z = signal.stft(mono, sr, nperseg=2048, noverlap=2048 - hop)
    mag = np.log1p(np.abs(Z) * 100)
    low = mag[f < 200]
    flux = np.maximum(0, np.diff(mag, axis=1)).sum(0)
    lflux = np.maximum(0, np.diff(low, axis=1)).sum(0)
    return np.concatenate([[0], flux]), np.concatenate([[0], lflux])


def refine_tempo(env, fps, bpm0):
    best = (0, bpm0, 0)
    n = len(env)
    for bpm in np.arange(bpm0 * 0.97, bpm0 * 1.03, 0.01):
        period = 60 / bpm * fps
        k = np.arange(0, n / period - 1)
        scores = []
        for ph in np.linspace(0, period, 48, endpoint=False):
            idx = np.round(ph + k * period).astype(int)
            idx = idx[idx < n]
            scores.append(env[idx].mean())
        j = int(np.argmax(scores))
        if scores[j] > best[0]:
            best = (scores[j], bpm, np.linspace(0, period, 48, endpoint=False)[j] / fps)
    return best[1], best[2]


def main():
    src, out, rep = sys.argv[1:4]
    x = decode(src)
    mono = x.mean(1)
    sr2, hop = 22050, 256
    m2 = signal.resample_poly(mono, 147, 320)
    env, lenv = onset_env(m2, sr2, hop)
    fps = sr2 / hop
    # coarse tempo by autocorrelation
    e = env - env.mean()
    ac = np.correlate(e, e, "full")[len(e) - 1:]
    lags = np.arange(1, len(ac))
    bpms = 60 * fps / lags
    sel = (bpms > 100) & (bpms < 150)
    bpm0 = bpms[sel][np.argmax(ac[1:][sel])]
    bpm, _ = refine_tempo(env, fps, bpm0)
    # snap to a whole or half BPM when it's that close (DAW-made tracks)
    for snap in (round(bpm), round(bpm * 2) / 2):
        if abs(snap - bpm) < 0.12:
            bpm = float(snap)
            break
    period = 60 / bpm * fps
    # beat phase from low-band (kick) onsets
    k = np.arange(0, len(lenv) / period - 1)
    phs = np.linspace(0, period, 96, endpoint=False)
    sc = [lenv[np.minimum(np.round(p + k * period).astype(int), len(lenv) - 1)].mean() for p in phs]
    phase = phs[int(np.argmax(sc))] / fps
    beat = 60 / bpm
    # beat-level energy to find the downbeat (section changes land on bar 1)
    nb = int((len(mono) / SR - phase) / beat)
    be = np.array([np.sqrt((mono[int((phase + i * beat) * SR):int((phase + (i + 1) * beat) * SR)] ** 2).mean() + 1e-12) for i in range(nb)])
    bdb = 20 * np.log10(be)
    jumps = np.abs(np.diff(bdb))
    dsc = [jumps[(np.arange(len(jumps)) % 4) == (r - 1) % 4].sum() for r in range(4)]
    down = int(np.argmax(dsc))
    t0 = phase + down * beat  # first downbeat in source time

    # stretch to target tempo, pitch unchanged
    ratio = TARGET_BPM / bpm
    y = decode(src, ["-af", f"rubberband=tempo={ratio:.6f}:pitch=1:transients=crisp:window=standard"])
    t0s = t0 / ratio
    nbar = int((len(y) / SR - t0s) / BAR_T)

    def bar_slice(i, n=1):
        a = int(round((t0s + i * BAR_T) * SR))
        return a, a + int(round(n * BAR_T * SR))

    # per-bar loudness (low+mid) in stretched audio
    ymono = y.mean(1)
    sos = signal.butter(2, [40 / (SR / 2), 4000 / (SR / 2)], "bandpass", output="sos")
    yb = signal.sosfilt(sos, ymono)
    E = np.array([20 * np.log10(np.sqrt((yb[slice(*bar_slice(i))] ** 2).mean()) + 1e-9) for i in range(nbar)])
    lowE = []
    sosl = signal.butter(2, 120 / (SR / 2), "lowpass", output="sos")
    yl = signal.sosfilt(sosl, ymono)
    for i in range(nbar):
        lowE.append(20 * np.log10(np.sqrt((yl[slice(*bar_slice(i))] ** 2).mean()) + 1e-9))
    lowE = np.array(lowE)

    # drops: biggest rise in 4-bar mean energy, on 4-bar phrase lines
    cand = []
    for i in range(4, nbar - 8):
        rise = E[i:i + 4].mean() - E[i - 4:i].mean()
        level = E[i:i + 8].mean() - np.median(E)
        cand.append((rise + 0.25 * (lowE[i:i + 4].mean() - lowE[i - 4:i].mean()) + 0.6 * level, i))
    cand.sort(reverse=True)
    phrase = cand[0][1] % 4
    drops = []
    for r, i in cand:
        if i % 4 != phrase:
            continue
        if all(abs(i - d) >= 12 for d in drops) and i + 8 <= nbar - 4:
            drops.append(i)
        if len(drops) == 2:
            break
    drops.sort()
    hi_level = np.percentile(E, 80)
    d1 = drops[0]
    d2 = drops[1] if len(drops) > 1 else d1
    # if only one drop, take drop B from the next 8 loud bars after drop A
    if d2 == d1 and d1 + 16 <= nbar - 4 and E[d1 + 8:d1 + 16].mean() > hi_level - 3:
        d2 = d1 + 8
    plan = {"intro_build": (d1 - 4, 4), "drop_a": (d1, 8), "breakdown": (d2 - 4, 4), "drop_b": (d2, 8)}
    # outro: last 4 loud bars before the track's ending, plus its natural tail
    import os
    if os.environ.get("PLAN_OVERRIDE"):
        plan.update({k: tuple(v) for k, v in json.loads(os.environ["PLAN_OVERRIDE"]).items()})
    loud_bars = [i for i in range(nbar) if E[i] > hi_level - 6]
    end_bar = min(loud_bars[-1] + 1, nbar)
    plan["outro"] = (end_bar - 4, 4)

    sosk = signal.butter(2, 150 / (SR / 2), "lowpass", output="sos")
    ylo = signal.sosfilt(sosk, ymono)
    khop = 240
    kenv = np.sqrt(np.convolve(ylo ** 2, np.ones(khop) / khop, "same")[::khop])
    kfl = np.maximum(0, np.diff(kenv, prepend=0))
    kfps = SR / khop
    beat_t = BAR_T / 4

    def seg_offset(b0, n):
        t0 = t0s + b0 * BAR_T
        lim = float(__import__("os").environ.get("OFFSET_LIM", "0.08"))
        offs = np.arange(-lim, lim + 0.0001, 0.002)
        sc = []
        for o in offs:
            bt = t0 + o + np.arange(0, n * 4) * beat_t
            idx = np.round(bt * kfps).astype(int)
            idx = idx[(idx >= 0) & (idx < len(kfl))]
            sc.append(kfl[idx].sum())
        sc = np.array(sc)
        if sc.max() < 2.0 * np.median(sc):  # no clear kick: keep the grid as is
            return 0.0
        return float(offs[int(np.argmax(sc))]) - 0.004  # 4 ms = measured bias of an on-grid kick

    order = ["intro_build", "drop_a", "breakdown", "drop_b", "outro"]
    offsets = {nm: seg_offset(*plan[nm]) for nm in order}
    out_n = int(round(OUT_DUR * SR))
    res = np.zeros((out_n, 2), np.float32)
    xf = int(0.012 * SR)
    pos_bar = 0
    for nm in order:
        b0, n = plan[nm]
        a, b = bar_slice(b0, n)
        sh = int(round(offsets[nm] * SR))
        a, b = a + sh, b + sh
        pre = int(0.006 * SR)
        a -= pre
        if nm == "outro":
            b = min(len(y), b + int(TAIL * SR) + xf)
            natural = end_bar + 2 > nbar or E[min(end_bar + 1, nbar - 1)] < hi_level - 15
        seg = y[max(a, 0):b].copy()
        if a < 0:
            seg = np.concatenate([np.zeros((-a, 2), np.float32), seg])
        dst = int(round(pos_bar * BAR_T * SR)) - pre
        seg[:xf] *= np.linspace(0, 1, xf)[:, None] if dst > 0 else 1
        if nm != "outro":
            seg[-xf:] *= np.linspace(1, 0, xf)[:, None]
        if dst < 0:
            seg = seg[-dst:]
            dst = 0
        m = min(len(seg), out_n - dst)
        if nm == "outro" and not natural:
            # final hit: first beat of the outro's last bar, ringing out under a reverb tail
            ha, _ = bar_slice(b0 + n - 1, 1)
            ha += sh
            hit = y[ha:ha + int(TAIL * SR) + int(0.3 * SR)].copy()
            tt = np.arange(len(hit)) / SR
            env = np.where(tt < 0.14, 1.0, np.exp(-(tt - 0.14) / 0.22))
            hit *= env[:, None]
            ir_n = int(1.6 * SR)
            rng = np.random.default_rng(3)
            ir = rng.standard_normal((ir_n, 2)) * np.exp(-np.arange(ir_n) / SR / 0.35)[:, None]
            ir = signal.sosfilt(signal.butter(2, 5000 / (SR / 2), output="sos"), ir, axis=0)
            ir /= np.sqrt((ir ** 2).sum(0))
            wet = np.stack([signal.fftconvolve(hit[:int(0.3 * SR), c], ir[:, c]) for c in range(2)], 1)[: len(hit)]
            if len(wet) < len(hit):
                wet = np.concatenate([wet, np.zeros((len(hit) - len(wet), 2))])
            hit = hit + wet * 0.35
            end_i = int(round(N_BARS * BAR_T * SR)) - pre
            seg = seg[: max(0, end_i - dst)]
            seg[-xf:] *= np.linspace(1, 0, xf)[:, None]
            m = min(len(seg), out_n - dst)
            res[dst:dst + m] += seg[:m]
            m2 = min(len(hit), out_n - end_i)
            hit[:xf] *= np.linspace(0, 1, xf)[:, None]
            res[end_i:end_i + m2] += hit[:m2]
            pos_bar += n
            continue
        res[dst:dst + m] += seg[:m]
        pos_bar += n
    if os.environ.get("FILTER_BREAKDOWN"):
        b12, b16 = int(round(12 * BAR_T * SR)), int(round(16 * BAR_T * SR))
        seg = res[b12:b16].astype(np.float64)
        outseg = np.zeros_like(seg)
        zi = None
        blk = 256
        for s0 in range(0, len(seg), blk):
            p = s0 / len(seg)
            fc = 700.0 if p < 0.5 else 700.0 * (16000 / 700.0) ** ((p - 0.5) / 0.5)
            sos = signal.butter(2, min(fc, SR * 0.45) / (SR / 2), output="sos")
            if zi is None:
                zi = np.zeros((sos.shape[0], 2, 2))
            outseg[s0:s0 + blk], zi = signal.sosfilt(sos, seg[s0:s0 + blk], axis=0, zi=zi)
        res[b12:b16] = outseg * 1.25
    # finish: fade the last 0.35 s
    f = int(0.35 * SR)
    res[-f:] *= np.linspace(1, 0, f)[:, None] ** 1.5
    res /= max(np.abs(res).max(), 1e-9) / 0.95
    from scipy.io import wavfile
    wavfile.write(out, SR, res)
    report = {"offsets_ms": {k: round(v * 1000, 1) for k, v in offsets.items()}, "natural_end": bool(natural), "src": src, "bpm": bpm, "stretch_pct": round((ratio - 1) * 100, 2), "first_downbeat_s": round(t0, 3),
              "bars": nbar, "drops": drops, "plan": plan, "bar_energy_db": [round(float(v), 1) for v in E]}
    json.dump(report, open(rep, "w"), indent=1)
    print(json.dumps({k: v for k, v in report.items() if k != "bar_energy_db"}))


if __name__ == "__main__":
    main()
