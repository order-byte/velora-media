"""Original soundtrack for the showreel: a 120 BPM electronic track with an immediate
hook, plus sound design cued to the picture (whooshes on transitions, pops on bubbles
and stickers, key clicks while text types, taps, counter ticks, impacts), in the way
the reference videos use them. Everything is synthesised here, so it is license-free.

writes out/audio/mix.wav, music.wav, sfx.wav (48 kHz stereo) and mix.m4a
"""
import os
import numpy as np
from scipy import signal
import soundfile as sf

SR = 48000
DUR = 30.6
N = int(SR * DUR)
BPM = 120
BEAT = 60 / BPM
STEP = BEAT / 4          # 16th
BAR = BEAT * 4           # 2 s
rng = np.random.default_rng(11)
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'out', 'audio')
os.makedirs(OUT, exist_ok=True)


def buf():
    return np.zeros((2, N))


def place(bus, x, t, gain=1.0, pan=0.0):
    """add mono or stereo x into bus at time t (seconds)."""
    i = int(round(t * SR))
    if i >= N:
        return
    if x.ndim == 1:
        l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        x = np.vstack([x * l * 1.414, x * r * 1.414])
    j = min(N, i + x.shape[1])
    if i < 0:
        x = x[:, -i:]; j = min(N, x.shape[1]); i = 0
    bus[:, i:j] += gain * x[:, : j - i]


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def env_adsr(n, a=0.005, d=0.1, s=0.6, r=0.1, hold=None):
    t = np.arange(n) / SR
    hold = hold if hold is not None else n / SR - r
    e = np.where(t < a, t / max(a, 1e-6), 1.0)
    dd = (t - a) / max(d, 1e-6)
    e = np.where((t >= a) & (t < a + d), 1 - (1 - s) * dd, e)
    e = np.where((t >= a + d), s, e)
    rel = np.clip((t - hold) / max(r, 1e-6), 0, 1)
    return e * (1 - rel)


def saw(f, n, cutoff=None, detune_phase=0.0, max_harm=60, square=False):
    """band-limited saw (or square) by additive synthesis with an optional per-sample
    low-pass cutoff (array or float) applied as a per-harmonic gain."""
    t = np.arange(n) / SR
    out = np.zeros(n)
    kmax = int(min(max_harm, (SR / 2 - 500) / f))
    for k in range(1, kmax + 1):
        if square and k % 2 == 0:
            continue
        g = 1.0 / k
        if cutoff is not None:
            g = g / np.sqrt(1 + (k * f / cutoff) ** 4)
        out += g * np.sin(2 * np.pi * k * f * t + detune_phase * k)
    return out * (2 / np.pi)


def noise(n):
    return rng.standard_normal(n)


def bp(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], btype='band', fs=SR, output='sos')
    return signal.sosfilt(sos, x)


def hp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, btype='high', fs=SR, output='sos'), x)


def lp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, btype='low', fs=SR, output='sos'), x)


def sweep_bp(x, f0, f1, q=2.0, curve='exp'):
    """band-pass whose centre moves from f0 to f1 across x (block-wise)."""
    n = len(x); out = np.zeros(n); blk = 256
    zi = None
    for s in range(0, n, blk):
        k = s / max(1, n - 1)
        fc = f0 * (f1 / f0) ** k if curve == 'exp' else f0 + (f1 - f0) * k
        fc = min(fc, SR / 2 * 0.9)
        b, a = signal.iirpeak(fc, q, fs=SR)
        if zi is None:
            zi = signal.lfilter_zi(b, a) * 0
        y, zi = signal.lfilter(b, a, x[s:s + blk], zi=zi)
        out[s:s + blk] = y
    return out


def make_ir(sec=1.8, damp=6000, seed=3):
    r = np.random.default_rng(seed)
    n = int(sec * SR)
    t = np.arange(n) / SR
    ir = r.standard_normal((2, n)) * np.exp(-t * 6.9 / sec)
    ir = np.vstack([lp(ir[0], damp), lp(ir[1], damp)])
    ir[:, : int(0.012 * SR)] *= np.linspace(0, 1, int(0.012 * SR))
    return ir / np.sqrt((ir ** 2).sum() / 2)


IR_HALL = make_ir(2.2, 7000)
IR_ROOM = make_ir(0.7, 9000, 5)


def reverb(bus, ir, wet):
    out = np.vstack([signal.fftconvolve(bus[0], ir[0])[:N], signal.fftconvolve(bus[1], ir[1])[:N]])
    return out * wet


# ------------------------------------------------------------------ instruments
def kick():
    n = int(0.45 * SR); t = np.arange(n) / SR
    f = 46 + 110 * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t * 7.5)
    click = hp(noise(n), 3000) * np.exp(-t * 400) * 0.35
    return np.tanh((body + click) * 1.6) * 0.9


def clap():
    n = int(0.35 * SR); t = np.arange(n) / SR
    e = np.zeros(n)
    for off in (0, 0.009, 0.018):
        i = int(off * SR); e[i:] += np.exp(-(t[: n - i]) * 180)
    e += np.exp(-t * 18) * 0.35
    return bp(noise(n), 900, 3200) * e * 0.9


def snare(vel=1.0):
    n = int(0.22 * SR); t = np.arange(n) / SR
    tone = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 30) * 0.6
    nz = bp(noise(n), 1500, 7500) * np.exp(-t * 22)
    return (tone + nz) * 0.6 * vel


def hat(open_=False):
    n = int((0.22 if open_ else 0.05) * SR); t = np.arange(n) / SR
    return hp(noise(n), 7500, 4) * np.exp(-t * (14 if open_ else 90)) * 0.35


def pluck(m, dur, bright=1.0, vel=1.0):
    f = mtof(m); n = int((dur + 0.35) * SR); t = np.arange(n) / SR
    cut = 900 + 5200 * bright * np.exp(-t * 9)
    x = saw(f, n, cut, 0.0) * 0.6 + saw(f * 1.004, n, cut, 1.3) * 0.4 + saw(f * 2, n, cut * 1.2, 0.7, 30, square=True) * 0.15
    e = np.exp(-t * 5.5) * np.clip(t / 0.003, 0, 1)
    rel = np.clip((t - dur) / 0.25, 0, 1)
    return x * e * (1 - rel) * vel


def supersaw(m, dur, cutoff=3200, attack=0.006, release=0.2, voices=5, spread=0.012):
    f = mtof(m); n = int((dur + release) * SR)
    out = np.zeros(n)
    for v in range(voices):
        d = 1 + spread * (v - (voices - 1) / 2) / ((voices - 1) / 2)
        out += saw(f * d, n, cutoff, rng.uniform(0, 6.28), 40)
    out /= voices
    return out * env_adsr(n, attack, 0.15, 0.75, release, hold=dur)


def bass_note(m, dur, cutoff=700):
    f = mtof(m); n = int((dur + 0.05) * SR); t = np.arange(n) / SR
    sub = np.sin(2 * np.pi * f * t)
    top = saw(f * 2, n, cutoff, 0, 20) * 0.35
    e = np.clip(t / 0.004, 0, 1) * np.clip((dur + 0.05 - t) / 0.05, 0, 1) * (0.75 + 0.25 * np.exp(-t * 12))
    return np.tanh((sub + top) * 1.3) * e * 0.8


def riser(sec):
    n = int(sec * SR); t = np.arange(n) / SR; k = t / sec
    nz = sweep_bp(noise(n), 400, 9000, 1.4) * (k ** 2.2) * 0.9
    f = 180 * 2 ** (k * 2.5)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * (k ** 3) * 0.18
    return nz + tone


def impact(big=1.0):
    n = int(2.2 * SR); t = np.arange(n) / SR
    f = 34 + 70 * np.exp(-t * 9)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.2)
    crack = lp(noise(n), 4000) * np.exp(-t * 14) * 0.5
    return np.tanh((boom * 1.2 + crack) * big) * 0.9


def reverse_cymbal(sec=1.0):
    n = int(sec * SR); t = np.arange(n) / SR
    return hp(noise(n), 5000) * (t / sec) ** 3 * 0.45


# ------------------------------------------------------------------ sfx
def whoosh(sec=0.5, f0=300, f1=3200, gain=1.0):
    n = int(sec * SR); t = np.arange(n) / SR; k = t / sec
    shape = np.sin(np.pi * np.clip(k, 0, 1)) ** 1.6
    x = sweep_bp(noise(n), f0, f1, 1.2) * shape
    x += lp(noise(n), 260) * shape * 0.6
    pan = np.linspace(-0.7, 0.7, n)
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    return np.vstack([x * l, x * r]) * 1.6 * gain


def swoosh(gain=1.0):
    return whoosh(0.28, 900, 6000, 0.7 * gain)


def pop(f0=420, f1=1100, gain=1.0):
    n = int(0.12 * SR); t = np.arange(n) / SR
    f = f0 + (f1 - f0) * (1 - np.exp(-t * 90))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 38)
    x += hp(noise(n), 4000) * np.exp(-t * 400) * 0.25
    return x * 0.8 * gain


def keyclick(gain=1.0):
    n = int(0.03 * SR); t = np.arange(n) / SR
    f = rng.uniform(1800, 3200)
    x = bp(noise(n), 2000, 9000) * np.exp(-t * 420) * 0.8 + np.sin(2 * np.pi * f * t) * np.exp(-t * 300) * 0.25
    return x * gain * rng.uniform(0.6, 1.0)


def tap(gain=1.0):
    n = int(0.08 * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * 1400 * t) * np.exp(-t * 160) + np.sin(2 * np.pi * 2650 * t) * np.exp(-t * 220) * 0.6
    x += bp(noise(n), 3000, 9000) * np.exp(-t * 600) * 0.5
    return x * 0.9 * gain


def tick(gain=1.0, f=3200):
    n = int(0.025 * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * t) * np.exp(-t * 350) + hp(noise(n), 6000) * np.exp(-t * 900) * 0.4) * 0.6 * gain


def chime(notes=(88, 95), gap=0.07, gain=1.0):
    n = int(1.2 * SR); out = np.zeros(n)
    for i, m in enumerate(notes):
        f = mtof(m); off = int(i * gap * SR); t = np.arange(n - off) / SR
        x = sum(np.sin(2 * np.pi * f * r * t) * a * np.exp(-t * d) for r, a, d in [(1, 1, 5), (2.76, 0.35, 9), (5.4, 0.15, 14)])
        out[off:] += x
    return out * 0.35 * gain


def shimmer(sec=1.6, gain=1.0):
    """glassy chime cluster + airy sparkle, for the glass moments."""
    n = int(sec * SR); out = np.zeros(n)
    for i, m in enumerate([96, 100, 103, 107, 108, 103, 112]):
        f = mtof(m); off = int(i * 0.045 * SR); t = np.arange(n - off) / SR
        x = sum(np.sin(2 * np.pi * f * r * t + rng.uniform(0, 6)) * a * np.exp(-t * d)
                for r, a, d in [(1, 1, 3.2), (2.76, 0.4, 6), (5.4, 0.18, 10), (8.93, 0.08, 14)])
        out[off:] += x * (0.9 ** i)
    t = np.arange(n) / SR
    out += hp(noise(n), 9000) * np.exp(-t * 3) * 0.25
    return out * 0.18 * gain


def flick(gain=1.0):
    n = int(0.11 * SR); t = np.arange(n) / SR
    return bp(noise(n), 1800, 6500) * (np.clip(t / 0.004, 0, 1) * np.exp(-t * 45)) * 0.9 * gain


# ------------------------------------------------------------------ music
music = buf(); drums = buf(); lead_bus = buf(); fx_bus = buf()
CHORDS = [  # Am, F, C, G (root midi, chord tones)
    (45, [57, 60, 64, 69]), (41, [57, 60, 65, 69]), (48, [55, 60, 64, 67]), (43, [55, 59, 62, 67]),
]
HOOK = [  # per chord: (16th step, midi, length in steps)
    [(0, 76, 2), (2, 74, 1), (3, 72, 2), (6, 69, 2), (8, 72, 1), (9, 74, 1), (10, 76, 3), (14, 79, 2)],
    [(0, 77, 2), (2, 76, 1), (3, 74, 2), (6, 72, 2), (8, 74, 1), (9, 76, 1), (10, 72, 4)],
    [(0, 76, 2), (2, 74, 1), (3, 72, 2), (6, 67, 2), (8, 72, 1), (9, 74, 1), (10, 76, 3), (14, 79, 2)],
    [(0, 79, 2), (2, 77, 1), (3, 76, 2), (6, 74, 4), (10, 71, 2), (12, 74, 2), (14, 76, 2)],
]
# energy per bar (2 s each): what plays where
#            0   1    2    3    4     5    6    7    8    9    10   11   12    13   14
SECTION = ['intro', 'build', 'drop', 'drop', 'break', 'drop', 'drop', 'drop', 'drop', 'drop2', 'drop2', 'build2', 'half', 'final', 'outro']
kick_times = []

for b, sec in enumerate(SECTION):
    t0 = b * BAR
    root, tones = CHORDS[b % 4]
    full = sec in ('drop', 'drop2', 'final')
    # --- drums
    if full or sec in ('build2',):
        for q in range(4):
            place(drums, kick(), t0 + q * BEAT, 1.0); kick_times.append(t0 + q * BEAT)
        for q in (1, 3):
            place(drums, clap(), t0 + q * BEAT, 0.8)
        for s in range(16):
            place(drums, hat(), t0 + s * STEP, 0.55 if s % 2 else 0.3, pan=0.25 if s % 2 else -0.15)
        for q in range(4):
            place(drums, hat(True), t0 + q * BEAT + BEAT / 2, 0.45, pan=0.1)
    if sec == 'half':
        for q in (0, 2):
            place(drums, kick(), t0 + q * BEAT, 1.0); kick_times.append(t0 + q * BEAT)
        place(drums, clap(), t0 + 2 * BEAT, 0.8)
        for s in range(0, 16, 2):
            place(drums, hat(), t0 + s * STEP, 0.35)
    if sec == 'build':
        for s in range(16):
            place(drums, hat(), t0 + s * STEP, 0.25 + 0.02 * s)
        for s in range(8, 16):  # snare roll into the drop
            place(drums, snare(0.35 + 0.05 * (s - 8)), t0 + s * STEP, 1.0)
        for s in range(14, 16):
            place(drums, snare(0.8), t0 + s * STEP + STEP / 2, 1.0)
    if sec == 'break':
        for s in range(0, 16, 2):
            place(drums, snare(0.25 + 0.03 * s), t0 + s * STEP, 1.0)
        for s in range(8, 16):
            place(drums, snare(0.5 + 0.05 * (s - 8)), t0 + s * STEP + STEP / 2, 1.0)
    if sec == 'build2':
        for s in range(8, 16):
            place(drums, snare(0.4 + 0.06 * (s - 8)), t0 + s * STEP, 1.0)
    if sec == 'intro':
        # punchy from the first frame: half-time kick, clap on 3, 8th hats
        for q in (0, 2):
            place(drums, kick(), t0 + q * BEAT, 0.9); kick_times.append(t0 + q * BEAT)
        place(drums, clap(), t0 + 3 * BEAT, 0.6)
        for s in range(2, 16, 2):
            place(drums, hat(), t0 + s * STEP, 0.3)
    if sec == 'build':
        for q in range(4):
            place(drums, kick(), t0 + q * BEAT, 0.85 if q < 3 else 0.6); kick_times.append(t0 + q * BEAT)

    # --- bass
    if full or sec in ('build2', 'half'):
        pattern = range(0, 16, 2) if sec != 'drop2' else [0, 3, 6, 8, 10, 11, 14]
        for s in pattern:
            m = root if s % 4 else root
            place(music, bass_note(m - 12 + 12, STEP * 1.6), t0 + s * STEP, 0.55)
    if sec in ('break', 'intro', 'build'):
        place(music, bass_note(root, BAR * 0.95, 300), t0, 0.3 if sec == 'break' else 0.16)

    # --- chords
    if full or sec == 'build2':
        for s in (0, 3, 6, 10, 12) if sec != 'final' else (0, 3, 6, 8, 10, 12, 14):
            for m in tones:
                place(music, supersaw(m, STEP * 1.2, 3600, release=0.12), t0 + s * STEP, 0.10)
    if sec in ('intro', 'build', 'break', 'half', 'outro'):
        for m in tones:
            place(music, supersaw(m, BAR * (0.98 if sec != 'outro' else 1.3), 1400 if sec != 'half' else 2200, attack=0.25, release=0.9), t0, 0.075)

    # --- lead hook (bright pluck), an octave up in drop2/final
    if sec in ('intro', 'build', 'drop', 'drop2', 'final', 'half', 'build2'):
        up = 12 if sec in ('drop2', 'final') else 0
        bright = {'intro': 0.85, 'build': 0.9, 'half': 0.6}.get(sec, 1.0)
        for s, m, L in HOOK[b % 4]:
            place(lead_bus, pluck(m + up, L * STEP, bright), t0 + s * STEP, 0.32, pan=0.0)
            if sec in ('drop', 'drop2', 'final'):
                place(lead_bus, pluck(m + up - 12, L * STEP, bright * 0.7), t0 + s * STEP, 0.16, pan=0.0)
    if sec == 'break':
        for s in range(0, 16, 2):
            m = tones[(s // 2) % 4] + 12
            place(lead_bus, pluck(m, STEP * 1.5, 0.35), t0 + s * STEP, 0.18, pan=-0.3 if s % 4 else 0.3)
    if sec == 'outro':
        for i, m in enumerate([69, 72, 76, 81]):
            place(lead_bus, pluck(m, 0.5, 0.5), t0 + i * STEP * 2, 0.2, pan=-0.4 + i * 0.25)

# risers / impacts that belong to the music
place(fx_bus, riser(1.6), 2.4, 0.5)
place(fx_bus, reverse_cymbal(1.0), 3.0, 0.6)
place(fx_bus, riser(1.8), 8.2, 0.55)
place(fx_bus, reverse_cymbal(0.8), 9.2, 0.6)
place(fx_bus, riser(1.6), 22.4, 0.45)
place(fx_bus, reverse_cymbal(0.8), 25.2, 0.5)
for t_imp, g in [(0.0, 0.8), (4.0, 0.7), (10.0, 0.85), (26.0, 1.0)]:
    place(fx_bus, impact(g), t_imp, 0.6)

# sidechain: duck bass/chords under each kick
duck = np.ones(N)
for kt in kick_times:
    i = int(kt * SR); n = min(N - i, int(0.3 * SR))
    if n <= 0:
        continue
    tt = np.arange(n) / SR
    duck[i:i + n] = np.minimum(duck[i:i + n], 1 - 0.65 * np.exp(-tt * 14))
music *= duck

# lead: ping-pong 3/16 delay + reverb
d = int(STEP * 3 * SR)
delayed = np.zeros_like(lead_bus)
delayed[0, d:] += lead_bus[1, :-d] * 0.32 + lead_bus[0, :-d] * 0.05
delayed[1, 2 * d:] += lead_bus[0, :-2 * d] * 0.22
lead_mix = lead_bus + delayed * (duck * 0.6 + 0.4)
music_mix = music + lead_mix + drums + fx_bus
music_mix += reverb(lead_bus + music * 0.5 + drums * 0.12, IR_HALL, 0.22)

# outro fade
fade = np.ones(N)
fs, fe = int(28.2 * SR), int(30.4 * SR)
fade[fs:fe] = np.linspace(1, 0, fe - fs) ** 1.5
fade[fe:] = 0
music_mix *= fade

# ------------------------------------------------------------------ sfx cues (times match the scene scripts)
sfx = buf()


def typing(start, nchars, cps, gain=0.5, every=1):
    for i in range(0, nchars, every):
        place(sfx, keyclick(gain), start + i / cps + rng.uniform(-0.004, 0.004), 1.0, pan=rng.uniform(-0.25, 0.25))


# S1 glass hook
place(sfx, shimmer(1.8, 1.2), 0.0, 1.0)
place(sfx, whoosh(1.3, 200, 1800, 0.55), 0.2, 1.0)
place(sfx, swoosh(1.0), 0.9, 1.0)
place(sfx, pop(380, 900, 0.5), 1.18, 1.0, pan=-0.4)
place(sfx, pop(480, 1200, 0.5), 1.28, 1.0, pan=0.4)
typing(1.38, 35, 30, 0.5)
place(sfx, tap(1.0), 2.6, 1.0, pan=0.35)
place(sfx, swoosh(0.9), 2.84, 1.0)
place(sfx, whoosh(0.62, 200, 4200, 1.0), 3.28, 1.0)
# S2 chat
for bt, sk in [(3.84, 4.78), (4.82, None), (5.82, 6.5), (6.72, None)]:
    place(sfx, pop(360, 980, 0.9), bt, 1.0, pan=-0.3)
    if sk:
        place(sfx, pop(600, 1500, 0.8), sk, 1.0, pan=0.3)
        place(sfx, chime((96, 103), 0.05, 0.35), sk + 0.02, 1.0)
typing(3.94, 33, 46, 0.38, 2)
typing(4.92, 43, 56, 0.38, 2)
typing(5.92, 22, 40, 0.38, 2)
typing(6.82, 13, 30, 0.38)
place(sfx, whoosh(0.5, 300, 2500, 0.8), 7.55, 1.0)
# S3 prompt
place(sfx, swoosh(0.8), 7.92, 1.0)
typing(8.32, 36, 34, 0.5)
place(sfx, tap(1.1), 9.29, 1.0, pan=0.4)
place(sfx, pop(250, 700, 0.7), 9.36, 1.0, pan=0.4)
place(sfx, whoosh(0.4, 400, 6000, 0.9), 9.66, 1.0)
# S4 gradient
place(sfx, swoosh(0.9), 10.16, 1.0)
place(sfx, whoosh(0.5, 250, 3000, 0.85), 11.48, 1.0)
place(sfx, pop(300, 900, 1.0), 11.9, 1.0)
place(sfx, swoosh(0.8), 12.02, 1.0)
place(sfx, whoosh(0.35, 500, 5000, 0.85), 12.82, 1.0)
for i in range(5):
    place(sfx, tick(0.9, 2600 + i * 180), 13.08 + i * 0.19, 1.0)
# S5 showcase
place(sfx, swoosh(0.7), 14.02, 1.0)
for i in range(7):
    place(sfx, flick(0.9), 14.18 + i * 0.25, 1.0, pan=(-0.3 if i % 2 else 0.3))
place(sfx, whoosh(0.55, 200, 3500, 1.0), 15.9, 1.0)
for i in range(4):
    place(sfx, swoosh(0.55), 16.12 + i * 0.45, 1.0)
place(sfx, whoosh(0.4, 400, 5000, 0.9), 17.75, 1.0)
# S6 grid
for i in range(4):
    place(sfx, whoosh(0.35, 400, 4000, 0.55), 18.0 + i * 0.06, 1.0, pan=[-0.6, 0.6, -0.4, 0.4][i])
for i in range(4):
    place(sfx, pop(500, 1300, 0.35), 18.55 + i * 0.08, 1.0, pan=[-0.5, 0.5, -0.5, 0.5][i])
for i in range(4):
    place(sfx, flick(0.8), 20.0 + i * 0.07, 1.0, pan=[-0.5, 0.5, -0.5, 0.5][i])
place(sfx, whoosh(0.4, 300, 3000, 0.6), 20.0, 1.0)
place(sfx, whoosh(0.62, 150, 3000, 1.0), 21.44, 1.0)
# S7 services
place(sfx, whoosh(0.4, 300, 5000, 0.9), 21.95, 1.0)
place(sfx, pop(260, 800, 0.9), 22.38, 1.0)
prev = -1
for k in range(400):
    tt = 22.45 + k * 0.002
    v = int(1000 * (1 - 2 ** (-10 * min(1, (tt - 22.45) / 0.8))))
    if v // 50 != prev:
        prev = v // 50
        place(sfx, tick(0.45, 3800), tt, 1.0)
place(sfx, chime((88, 95), 0.06, 0.9), 23.2, 1.0)
place(sfx, whoosh(0.45, 300, 4500, 0.9), 23.62, 1.0)
# S8 profile
place(sfx, shimmer(1.4, 0.8), 24.0, 1.0)
place(sfx, swoosh(0.8), 24.05, 1.0)
place(sfx, pop(350, 1000, 0.7), 24.25, 1.0)
place(sfx, swoosh(0.5), 24.9, 1.0)
place(sfx, tap(1.1), 25.3, 1.0, pan=-0.2)
place(sfx, chime((91, 98), 0.07, 0.8), 25.34, 1.0)
place(sfx, whoosh(0.4, 300, 4000, 0.8), 25.72, 1.0)
# S9 logo
place(sfx, shimmer(2.2, 1.1), 26.0, 1.0)
place(sfx, pop(260, 760, 1.0), 26.1, 1.0)
place(sfx, swoosh(0.7), 26.3, 1.0)
place(sfx, swoosh(0.5), 27.0, 1.0)
place(sfx, pop(420, 1100, 0.7), 27.55, 1.0)

sfx_mix = sfx + reverb(sfx, IR_ROOM, 0.18)


# ------------------------------------------------------------------ master
def limiter(x, ceiling=0.89):
    # look-ahead-free soft limiter: smooth gain from the peak envelope
    peak = np.max(np.abs(x), axis=0)
    win = int(0.004 * SR)
    env = np.maximum.accumulate(peak[::-1])[::-1] if False else signal.convolve(peak, np.ones(win) / win, mode='same')
    env = np.maximum(env, peak)
    g = np.minimum(1.0, ceiling / np.maximum(env, 1e-9))
    g = signal.sosfiltfilt(signal.butter(1, 30, fs=SR, output='sos'), g)
    return np.clip(x * np.minimum(g, 1.0), -0.98, 0.98)


def rms_db(x):
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)


music_mix *= 10 ** ((-17.5 - rms_db(music_mix)) / 20)
sfx_mix *= 10 ** ((-20.5 - rms_db(sfx_mix)) / 20)
mix = limiter(np.tanh((music_mix + sfx_mix) * 1.25) / 1.25 * 1.15)
music_only = limiter(music_mix * 1.1)
sfx_only = limiter(sfx_mix * 1.6)
end = int(30.0 * SR)
for name, x in [('mix', mix), ('music', music_only), ('sfx', sfx_only)]:
    sf.write(os.path.join(OUT, f'{name}.wav'), x[:, :end].T, SR, subtype='PCM_24')
print('mix rms', round(rms_db(mix), 1), 'dBFS  peak', round(20 * np.log10(np.abs(mix).max()), 2), 'dBFS')
