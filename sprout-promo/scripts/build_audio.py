"""Mix the SFX soundtrack from the cue list exported by the page.

usage: python build_audio.py <cues.json> <sfx_dir> <out.wav>
"""
import json
import os
import sys

import numpy as np
import soundfile as sf

SR = 48000


def main():
    cues_path, sfx_dir, out = sys.argv[1:4]
    meta = json.load(open(cues_path))
    n = int(round(meta["duration"] * SR))
    mix = np.zeros((n, 2))
    cache = {}
    for c in meta["cues"]:
        if c["name"] not in cache:
            y, sr = sf.read(os.path.join(sfx_dir, f"{c['name']}.wav"), always_2d=True)
            assert sr == SR, (c["name"], sr)
            cache[c["name"]] = y
        y = cache[c["name"]] * c["gain"]
        a = int(round(max(0.0, c["t"]) * SR))
        skip = int(round(max(0.0, -c["t"]) * SR))
        seg = y[skip:skip + max(0, n - a)]
        mix[a:a + len(seg)] += seg

    # gentle soft-knee limiter, then peak-normalise to -1 dBFS
    peak = np.abs(mix).max()
    mix = mix / peak
    knee = 0.7
    over = np.abs(mix) > knee
    mix[over] = np.sign(mix[over]) * (knee + (1 - knee) * np.tanh((np.abs(mix[over]) - knee) / (1 - knee)))
    mix *= 10 ** (-1 / 20) / np.abs(mix).max()
    # short fade at the very end
    f = int(0.25 * SR)
    mix[-f:] *= np.linspace(1, 0, f)[:, None]
    sf.write(out, mix.astype(np.float32), SR, subtype="PCM_24")
    print(f"mixed {len(meta['cues'])} cues into {out} ({meta['duration']}s)")


if __name__ == "__main__":
    main()
