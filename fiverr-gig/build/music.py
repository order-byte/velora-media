"""Original 128.6 BPM track for the Aminur showreel.

Beat = 14 video frames at 30 fps, so every cut can land on a beat.
Arrangement (0-based bars):
  0-1  cold open   pad + ticks, impact on bar 1
  2-3  build       kick, clap, filter opening, snare roll, riser
  4-11 drop 1      full groove, offbeat bass
  12-15 breakdown  pad + arp, no kick in 12-13, roll in 15
  16-23 drop 2     full groove, rolling bass, lead arp
  24-27 outro      groove without lead, filters down; final stab at bar 28
"""
import sys
import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 48000
BEAT = 14 / 30
BAR = 4 * BEAT
STEP = BEAT / 4
N_BARS = 28
TAIL = 1.2
DUR = N_BARS * BAR + TAIL
N = int(DUR * SR) + SR
rng = np.random.default_rng(7)


def t_of(bar, beat=0.0):
    return bar * BAR + beat * BEAT


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def buf():
    return np.zeros((N, 2), np.float32)


def add(dst, sig, t0, gain=1.0, pan=0.0):
    i0 = int(round(t0 * SR))
    if sig.ndim == 1:
        l = np.cos((pan + 1) * np.pi / 4)
        r = np.sin((pan + 1) * np.pi / 4)
        sig = np.stack([sig * l * 1.414, sig * r * 1.414], 1)
    if i0 < 0:
        sig = sig[-i0:]
        i0 = 0
    n = min(len(sig), N - i0)
    dst[i0:i0 + n] += sig[:n] * gain


def sos_filter(x, kind, f, order=2):
    wn = np.asarray(f, float) / (SR / 2)
    if wn.size == 1:
        wn = float(wn)
    sos = signal.butter(order, wn, btype=kind, output="sos")
    return signal.sosfilt(sos, x, axis=0)


def sweep_lowpass(x, cutoff_fn, block=256):
    """Time-varying 2-pole lowpass; cutoff_fn(t_seconds_array) -> Hz."""
    out = np.zeros_like(x)
    zi = None
    for s in range(0, len(x), block):
        fc = float(np.clip(cutoff_fn(s / SR), 40, SR * 0.45))
        sos = signal.butter(2, fc / (SR / 2), output="sos")
        if zi is None:
            zi = np.zeros((sos.shape[0], 2, x.shape[1]))
        seg, zi = signal.sosfilt(sos, x[s:s + block], axis=0, zi=zi)
        out[s:s + block] = seg
    return out


def polyblep_saw(freq, n, phase0=0.0):
    dt = freq / SR
    ph = (phase0 + dt * np.arange(n)) % 1.0
    y = 2 * ph - 1
    m = ph < dt
    x = ph[m] / dt
    y[m] -= x + x - x * x - 1
    m = ph > 1 - dt
    x = (ph[m] - 1) / dt
    y[m] -= x * x + x + x + 1
    return y


def env_adsr(n, a=0.005, r=0.03, hold_level=1.0):
    e = np.full(n, hold_level, np.float32)
    na = max(1, int(a * SR))
    nr = max(1, int(r * SR))
    e[:na] *= np.linspace(0, 1, na)
    e[-nr:] *= np.linspace(1, 0, nr)
    return e


# ---------- instruments ----------

def kick():
    n = int(0.42 * SR)
    t = np.arange(n) / SR
    f = 47 + 125 * np.exp(-t / 0.032)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.19)
    body[: int(0.001 * SR)] *= np.linspace(0, 1, int(0.001 * SR))
    click = sos_filter(rng.standard_normal(n), "bandpass", [2500, 9000]) * np.exp(-t / 0.004) * 0.55
    y = np.tanh(1.8 * (body + click)) / np.tanh(1.8)
    return y.astype(np.float32)


def clap():
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    noise = sos_filter(rng.standard_normal(n), "bandpass", [900, 3200])
    e = np.zeros(n)
    for k, d in enumerate([0, 0.010, 0.021]):
        tt = np.clip(t - d, 0, None)
        e += (t >= d) * np.exp(-tt / 0.0045) * (0.8 + 0.1 * k)
    tail = (t >= 0.03) * np.exp(-np.clip(t - 0.03, 0, None) / 0.11)
    y = noise * (e + 0.7 * tail)
    return (y / np.abs(y).max()).astype(np.float32)


def hat(open_=False):
    n = int((0.35 if open_ else 0.08) * SR)
    t = np.arange(n) / SR
    noise = sos_filter(rng.standard_normal(n), "highpass", 6500 if open_ else 8000, order=4)
    y = noise * np.exp(-t / (0.11 if open_ else 0.022))
    return (y / np.abs(y).max()).astype(np.float32)


def crash():
    n = int(2.6 * SR)
    t = np.arange(n) / SR
    noise = sos_filter(rng.standard_normal((n, 2)), "highpass", 3800, order=4)
    ring = sum(np.sin(2 * np.pi * f * t + rng.random() * 6) for f in [3120, 4410, 5230, 6720, 7900]) * 0.05
    y = (noise + ring[:, None]) * np.exp(-t / 0.85)[:, None]
    return (y / np.abs(y).max()).astype(np.float32)


def snare():
    n = int(0.25 * SR)
    t = np.arange(n) / SR
    noise = sos_filter(rng.standard_normal(n), "bandpass", [1400, 7000]) * np.exp(-t / 0.07)
    tone = np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.045) * 0.6
    y = noise + tone
    return (y / np.abs(y).max()).astype(np.float32)


def boom():
    n = int(2.2 * SR)
    t = np.arange(n) / SR
    f = 36 + 30 * np.exp(-t / 0.12)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.55)
    thump = sos_filter(rng.standard_normal(n), "lowpass", 220) * np.exp(-t / 0.08) * 1.5
    y = np.tanh(1.5 * (sub + thump))
    return (y / np.abs(y).max()).astype(np.float32)


def riser(length):
    n = int(length * SR)
    t = np.arange(n) / SR
    x = rng.standard_normal((n, 2))
    out = np.zeros_like(x)
    block = 256
    zi = None
    for s in range(0, n, block):
        p = s / n
        fc = 350 * (9500 / 350) ** p
        sos = signal.butter(2, [fc * 0.7 / (SR / 2), min(fc * 1.4, SR * 0.45) / (SR / 2)], btype="bandpass", output="sos")
        if zi is None:
            zi = np.zeros((sos.shape[0], 2, 2))
        out[s:s + block], zi = signal.sosfilt(sos, x[s:s + block], axis=0, zi=zi)
    amp = (t / length) ** 2.2
    tone_f = 180 * (720 / 180) ** (t / length)
    ph = np.cumsum(tone_f) / SR
    tone = (2 * (ph % 1) - 1) * 0.18
    tone = sos_filter(tone, "lowpass", 2500)
    y = out / (np.abs(out).max() + 1e-9) + tone[:, None]
    return (y * amp[:, None]).astype(np.float32)


def supersaw_chord(notes, length, detune_cents=(-17, -7, 0, 7, 17)):
    n = int(length * SR)
    y = np.zeros((n, 2))
    for note in notes:
        for k, c in enumerate(detune_cents):
            f = hz(note) * 2 ** (c / 1200)
            s = polyblep_saw(f, n, rng.random())
            pan = (k - 2) / 2.2
            l = np.cos((pan + 1) * np.pi / 4)
            r = np.sin((pan + 1) * np.pi / 4)
            y[:, 0] += s * l
            y[:, 1] += s * r
    return y / (len(notes) * len(detune_cents)) * 2.2


def pluck(note, length=0.22):
    n = int(length * SR)
    t = np.arange(n) / SR
    s = 0.6 * polyblep_saw(hz(note), n) + 0.4 * np.sign(np.sin(2 * np.pi * hz(note) * t))
    fc = 600 + 4200 * np.exp(-t / 0.06)
    out = np.zeros(n)
    zi = np.zeros((1, 2))
    for b in range(0, n, 128):
        sos = signal.butter(2, min(fc[b], 20000) / (SR / 2), output="sos")
        out[b:b + 128], zi = signal.sosfilt(sos, s[b:b + 128], zi=zi)
    return (out * np.exp(-t / 0.16) * env_adsr(n, 0.002, 0.02)).astype(np.float32)


def bass_note(note, length):
    n = int(length * SR)
    t = np.arange(n) / SR
    s = 0.55 * polyblep_saw(hz(note), n) + 0.8 * np.sin(2 * np.pi * hz(note) * t)
    s = sos_filter(s, "lowpass", 380)  # warm, round
    return (np.tanh(1.6 * s) * env_adsr(n, 0.003, 0.025)).astype(np.float32)


# ---------- arrangement ----------
CHORDS = [[60, 65, 68], [61, 65, 68], [60, 63, 68], [58, 63, 67]]  # Fm Db Ab Eb
ROOTS = [41, 37, 44, 39]
ARP = [[65, 68, 72, 77], [65, 68, 73, 77], [63, 68, 72, 75], [63, 67, 70, 75]]

DROPS = list(range(4, 12)) + list(range(16, 24))
KICK_BARS = [1, 2, 3] + DROPS + [14, 15, 24, 25, 26]
CLAP_BARS = [3] + DROPS + [12, 13, 14, 15, 24, 25, 26]


def build():
    drums = buf()
    synths = buf()
    bass = buf()
    fx = buf()
    rev_send = buf()

    K, C, HC, HO, CR, SN, BM = kick(), clap(), hat(), hat(True), crash(), snare(), boom()

    # kicks (skip the pre-drop last half beat)
    for b in KICK_BARS:
        for beat in range(4):
            if b in (3, 15) and beat == 3:
                continue
            add(drums, K, t_of(b, beat), 0.55)
    # claps on 2 and 4
    for b in CLAP_BARS:
        for beat in (1, 3):
            if b in (3, 15) and beat == 3:
                continue
            g = 0.32 if b in (12, 13) else 0.42
            add(drums, C, t_of(b, beat), g)
            add(rev_send, C, t_of(b, beat), g * 0.5)
    # hats
    for b in range(N_BARS):
        for st in range(16):
            tt = t_of(b, st / 4)
            if b in (0, 1):
                if st % 2 == 0:
                    add(drums, HC, tt, 0.05 + 0.03 * (st % 4 == 2), pan=0.25)
            elif b in DROPS or b in (24, 25):
                v = 0.2 if st % 4 == 2 else 0.11 + 0.04 * rng.random()
                add(drums, HC, tt, v, pan=0.3)
                if st % 4 == 2:
                    add(drums, HO, tt, 0.17, pan=-0.2)
            elif b in (2, 3, 14, 15):
                if st % 2 == 0:
                    add(drums, HC, tt, 0.07, pan=0.3)
    shaker = buf()
    sh_n = int(0.06 * SR)
    sh_t = np.arange(sh_n) / SR
    for b in DROPS + [24, 25]:
        for st in range(16):
            sh = sos_filter(rng.standard_normal(sh_n), "bandpass", [5000, 14000]) * np.exp(-sh_t / 0.018) * np.minimum(1, sh_t / 0.004)
            add(shaker, sh / np.abs(sh).max(), t_of(b, st / 4) + 0.004, 0.09 if st % 2 else 0.05, pan=-0.45)
    # crashes + booms on section hits
    for b in (4, 8, 16, 20, 24):
        add(fx, CR, t_of(b), 0.16)
        add(rev_send, CR, t_of(b), 0.05)
    for b in (1, 4, 16, 24):
        add(fx, BM, t_of(b), 0.55 if b != 1 else 0.45)
    # reverse crash into drops
    rc = CR[: int(BEAT * 1.0 * SR)][::-1]
    for b in (4, 16):
        add(fx, rc, t_of(b) - len(rc) / SR, 0.2)
    # snare rolls in bars 3 and 15
    for b in (3, 15):
        hits = [0, 0.5, 1, 1.5, 2, 2.25, 2.5, 2.75] + [3 + k / 8 for k in range(4)]
        for k, beat in enumerate(hits):
            add(drums, SN, t_of(b, beat), 0.10 + 0.30 * (k / len(hits)) ** 1.5)
            add(rev_send, SN, t_of(b, beat), 0.08)
    # risers
    for b in (2, 14):
        r = riser(2 * BAR - BEAT * 0.5)
        add(fx, r, t_of(b), 0.22)
        add(rev_send, r, t_of(b), 0.08)

    # chords: one per bar from bar 0, cutoff automated
    for b in range(N_BARS + 1):
        if b == N_BARS:
            ch = supersaw_chord(CHORDS[0], 1.3)
            ch *= np.exp(-np.arange(len(ch)) / SR / 0.35)[:, None]
            add(synths, ch * env_adsr(len(ch), 0.002, 0.2)[:, None], t_of(b), 0.55)
            add(rev_send, ch, t_of(b), 0.35)
            continue
        ch = supersaw_chord(CHORDS[b % 4], BAR + 0.05)
        e = env_adsr(len(ch), 0.25 if b in (0, 12) else 0.006, 0.06)
        add(synths, ch * e[:, None], t_of(b), 0.34)
        add(rev_send, ch * e[:, None], t_of(b), 0.12)

    def cutoff(t):
        bar = t / BAR
        if bar < 2:
            return 650
        if bar < 4:
            return 650 * (12000 / 650) ** ((bar - 2) / 2)
        if bar < 12:
            return 12000
        if bar < 14:
            return 2200
        if bar < 16:
            return 2200 * (13000 / 2200) ** ((bar - 14) / 2)
        if bar < 24:
            return 13000
        if bar < 26:
            return 9000
        if bar < 28:
            return 9000 * (500 / 9000) ** ((bar - 26) / 2)
        return 3500
    synths = sweep_lowpass(synths, cutoff)
    synths = sos_filter(synths, "highpass", 200)

    # arp: drop 1 second half, breakdown, drop 2
    arp = buf()
    for b in list(range(8, 12)) + list(range(12, 16)) + list(range(16, 24)):
        pat = ARP[b % 4]
        for st in range(16):
            note = pat[[0, 1, 2, 3, 2, 1, 2, 3][st % 8]] + (12 if (b >= 16 and st % 8 in (3, 7)) else 0)
            g = 0.16 if b >= 16 else 0.12
            p = pluck(note)
            add(arp, p, t_of(b, st / 4), g, pan=(0.35 if st % 2 else -0.35))
    # dotted-eighth echo on the arp
    d = int(0.75 * BEAT * SR)
    echo = np.zeros_like(arp)
    for k in range(1, 4):
        sh = np.zeros_like(arp)
        sh[d * k:] = arp[:-d * k] * (0.38 ** k)
        echo += sh[:, ::-1] if k % 2 else sh
    arp = arp + sos_filter(echo, "lowpass", 4500)
    add(rev_send, arp[:N], 0, 0.25)

    # bass
    for b in range(1, 28):
        if b in (12, 13):
            continue
        root = ROOTS[b % 4]
        if b in range(16, 24):
            steps = [1, 2, 3, 5, 6, 7, 9, 10, 11, 13, 14, 15]
            for st in steps:
                n_ = root + (12 if st in (7, 15) else 0)
                add(bass, bass_note(n_, STEP * 0.85), t_of(b, st / 4), 0.36)
        else:
            if b in (3, 15):
                offs = [0.5, 1.5, 2.5]
            elif b == 27:
                offs = [0.5, 1.5]
            else:
                offs = [0.5, 1.5, 2.5, 3.5]
            for o in offs:
                add(bass, bass_note(root, BEAT * 0.42), t_of(b, o), 0.38)
        if b in (1, 4, 8, 16, 20, 24):
            add(bass, bass_note(root - 12, BEAT * 0.9), t_of(b), 0.3)

    # sidechain from kick positions
    sc = np.ones(N, np.float32)
    shape_n = int(0.24 * SR)
    shape = 1 - 0.78 * (1 - np.arange(shape_n) / shape_n) ** 2
    for b in KICK_BARS:
        for beat in range(4):
            if b in (3, 15) and beat == 3:
                continue
            i0 = int(t_of(b, beat) * SR)
            sc[i0:i0 + shape_n] = np.minimum(sc[i0:i0 + shape_n], shape[: len(sc[i0:i0 + shape_n])])
    synths *= sc[:, None]
    bass *= np.minimum(1, sc * 1.15)[:, None]
    arp *= (0.5 + 0.5 * sc)[:, None]

    # reverb
    ir_n = int(2.2 * SR)
    t = np.arange(ir_n) / SR
    ir = rng.standard_normal((ir_n, 2)) * np.exp(-t / 0.42)[:, None]
    ir = sos_filter(ir, "lowpass", 6000)
    ir[: int(0.018 * SR)] = 0
    ir /= np.sqrt((ir ** 2).sum(0))
    wet = np.stack([signal.fftconvolve(rev_send[:, c], ir[:, c])[:N] for c in range(2)], 1)
    wet = sos_filter(wet, "highpass", 250)

    import os
    if os.environ.get('STEMS'):
        for nm, v in [('drums',drums),('synths',synths),('bass',bass),('arp',arp),('fx',fx),('wet',wet*0.55)]:
            print(f'{nm:7s} peak={np.abs(v).max():.3f} rms={np.sqrt((v**2).mean()):.4f}')
    mix = drums * 1.0 + synths * 3.2 + bass * 0.62 + arp * 3.4 + fx * 0.8 + wet * 1.0 + shaker * 1.0
    mix = mix + 0.7 * sos_filter(mix, "highpass", 3000)
    mix = sos_filter(mix, "highpass", 28)
    mix = sos_filter(mix, "lowpass", 15000)
    # gentle bus glue + soft clip
    if os.environ.get('STEMS'): print('premix peak', np.abs(mix).max(), 'rms', np.sqrt((mix**2).mean()))
    mix = mix / (np.abs(mix).max() + 1e-9) * 1.1
    mix = np.tanh(mix * 1.0)
    end = int(DUR * SR)
    mix = mix[:end]
    fade = int(0.25 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
    mix /= np.abs(mix).max() / 0.89
    return mix.astype(np.float32)


if __name__ == "__main__":
    out = sys.argv[1]
    m = build()
    wavfile.write(out, SR, m)
    print("wrote", out, m.shape, "dur", len(m) / SR)
