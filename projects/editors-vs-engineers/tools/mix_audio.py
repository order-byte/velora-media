"""Mix the reel: our voice over reel 1's music + sound-effects bed, re-cut to the new timing.

Each reel-1 segment's slice of the bed (vocals removed with demucs) is placed
under the matching new segment, so a transition whoosh still lands on its cut.
A segment that got longer is extended by looping its own middle with
crossfades; one that got shorter is trimmed. Seams get short crossfades. The
voice sits at the same level against the bed as the original voice did.

Usage: python3 mix_audio.py CONFIG.json NO_VOCALS.wav VOCALS.wav VOICE.wav OUT.wav
"""
import json
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "edit"))
import plan  # noqa: E402
from timeline import Timeline  # noqa: E402

SR = 48000
# voice polish: warmth, less 3 kHz harshness, clarity + air, de-ess, even level
VOICE_CHAIN = ",".join([
    "highpass=f=70:poles=2",
    "afftdn=nr=6:nf=-55:tn=1",
    "equalizer=f=130:t=q:w=0.8:g=3",
    "equalizer=f=280:t=q:w=1.0:g=-3",
    "equalizer=f=1800:t=q:w=1.0:g=2",
    "equalizer=f=3200:t=q:w=1.0:g=-3",
    "equalizer=f=5500:t=q:w=1.2:g=1.5",
    "treble=g=3:f=9000",
    "deesser=i=0.25:m=0.5:f=0.5",
    "acompressor=threshold=-21dB:ratio=3:attack=4:release=70:knee=4:makeup=2",
    "alimiter=limit=0.89:attack=3:release=40",
])
# reel 1's cut list: segment k of the plan is reel-1 [CUTS[k], CUTS[k+1]]
CUTS = [0.0, 2.17, 6.05, 9.84, 11.22, 13.72, 16.06, 18.23, 22.90, 25.57, 27.70, 29.53, 31.99, 37.58]


def load(path, ch, af=None):
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", path] + (["-af", af] if af else []) +
                                  ["-f", "f32le", "-ac", str(ch), "-ar", str(SR), "-"])
    return np.frombuffer(raw, np.float32).reshape(-1, ch).copy()


def xfade_join(a, b, n):
    if n == 0 or len(a) < n or len(b) < n:
        return np.concatenate([a, b])
    k = np.linspace(0, 1, n, dtype=np.float32)[:, None]
    mid = a[-n:] * np.cos(k * np.pi / 2) + b[:n] * np.sin(k * np.pi / 2)
    return np.concatenate([a[:-n], mid, b[n:]])


def fit(src, length):
    """Trim or loop-extend a slice of bed to exactly `length` samples."""
    if length <= len(src):
        return src[:length]
    out = src.copy()
    loop = src[int(0.25 * len(src)):int(0.85 * len(src))]
    xf = int(0.08 * SR)
    while len(out) < length + xf:
        out = xfade_join(out, loop, xf)
    return out[:length]


def win_rms(x, win=0.05):
    n = int(win * SR)
    k = len(x) // n
    return np.sqrt((x[:k * n].reshape(k, n) ** 2).mean(1) + 1e-10)


def talking(x):
    return 20 * np.log10(win_rms(x)) > -32


def main():
    cfg_path, bed_path, voc_path, voice_path, out = sys.argv[1:6]
    cfg = json.load(open(cfg_path))
    tl = Timeline(cfg["edl"], cfg["selects_map"])
    segs, _, end = plan.build(tl)
    bed = load(bed_path, 2)
    voc = load(voc_path, 2)
    voice = load(voice_path, 1, VOICE_CHAIN)[:, 0]

    # bed, segment by segment
    xf = int(0.04 * SR)
    track = np.zeros((0, 2), np.float32)
    for k, s in enumerate(segs):
        a, b = int(CUTS[k] * SR), int(CUTS[k + 1] * SR)
        length = int(round((s["t"][1] - s["t"][0]) * SR))
        piece = fit(bed[a:min(b + xf, len(bed))], length + (xf if k else 0))
        track = xfade_join(track, piece, xf) if len(track) else piece
    n = int(round(end * SR))
    track = np.pad(track, ((0, max(n - len(track), 0)), (0, 0)))[:n]
    fade = int(0.7 * SR)
    track[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)[:, None]

    # voice level: same voice-to-bed ratio as the original, measured in 50 ms windows where someone talks
    ratio = np.median(win_rms(voc.mean(1))[talking(voc.mean(1))] / win_rms(bed.mean(1))[talking(voc.mean(1))])
    m = min(len(voice), len(track))
    vt = talking(voice[:m])
    ours = np.median(win_rms(voice[:m])[vt] / win_rms(track.mean(1)[:m])[vt])
    gain = ratio / max(ours, 1e-6)
    print(f"original voice/bed ratio {20 * np.log10(ratio):.1f} dB, voice gain {20 * np.log10(gain):.1f} dB")
    v = np.zeros(n, np.float32)
    v[:min(len(voice), n)] = voice[:n] * gain
    mix = track + v[:, None]

    tmp = out + ".pre.wav"
    with open(tmp + ".raw", "wb") as f:
        f.write(mix.astype(np.float32).tobytes())
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", tmp + ".raw", tmp],
                   check=True)
    os.remove(tmp + ".raw")
    # Instagram-friendly loudness
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af",
                    "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", str(SR), out], check=True)
    os.remove(tmp)


if __name__ == "__main__":
    main()
