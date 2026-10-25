"""Cut v1's sound effects and lay them on the music using the render cue sheet.

usage: mix.py V1.wav MUSIC.wav CUES.json OUT.wav
"""
import json
import sys

import numpy as np
from scipy.io import wavfile

SR = 48000

# name: (start, end, peak) seconds inside v1's audio. Whooshes/risers are aligned by their peak.
LIB = {
    "whA": (16.55, 19.02, 17.18),
    "whB": (26.02, 27.97, 26.69),
    "whC": (35.18, 37.30, 36.09),
    "whD": (23.58, 25.84, 24.71),
    "whE": (7.95, 10.81, 8.98),
    "riser_big": (39.10, 42.54, 41.33),
    "riser_med": (32.49, 35.10, 33.82),
    "pop1": (19.25, 20.02, None),
    "pop2": (20.25, 20.99, None),
    "pop3": (22.23, 22.74, None),
    "click1": (32.34, 32.43, None),
    "click2": (21.68, 21.88, None),
    "tick1": (28.66, 28.82, None),
    "tick2": (30.32, 30.54, None),
    "blip1": (11.60, 11.75, None),
    "blip2": (29.23, 29.38, None),
    "swoosh": (15.67, 16.05, None),
}


def load(path):
    sr, x = wavfile.read(path)
    assert sr == SR, (path, sr)
    if x.dtype == np.int16:
        x = x.astype(np.float32) / 32768
    return x.astype(np.float32)


def main():
    v1, music, cues_path, out = sys.argv[1:5]
    src = load(v1)
    mus = load(music)
    meta = json.load(open(cues_path))
    fps = meta["fps"]
    n = len(mus)
    sfx = np.zeros_like(mus)
    for c in meta["cues"]:
        a, b, peak = LIB[c["sfx"]]
        seg = src[int(a * SR):int(b * SR)].copy()
        fi, fo = int(0.004 * SR), int(0.03 * SR)
        seg[:fi] *= np.linspace(0, 1, fi)[:, None]
        seg[-fo:] *= np.linspace(1, 0, fo)[:, None]
        t = c["frame"] / fps
        if peak is not None:
            t -= peak - a
        i0 = int(round(t * SR))
        if i0 < 0:
            seg = seg[-i0:]
            i0 = 0
        m = min(len(seg), n - i0)
        sfx[i0:i0 + m] += seg[:m] * c["gain"]
    # SFX bus +5 dB over its source level, music bed a touch under so hits read clearly
    mix = mus * 0.72 + sfx * float(__import__("os").environ.get("SFX_GAIN", "1.4"))
    peak = np.abs(mix).max()
    mix = mix / peak * 0.95
    wavfile.write(out, SR, mix.astype(np.float32))
    print("cues", len(meta["cues"]), "dur", n / SR, "pre-norm peak", round(float(peak), 3))


if __name__ == "__main__":
    main()
