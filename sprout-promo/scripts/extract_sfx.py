"""Cut the individual sound effects out of the reference promo (video 1).

The reference track is pure sound design (no music bed), so each effect can be
lifted out with a short fade at both ends.

usage: python extract_sfx.py <reference.wav|mp4> <out_dir>
"""
import json
import os
import subprocess
import sys
import tempfile

import numpy as np
import soundfile as sf

SR = 48000

# name: (start, end, fade_in, fade_out) in seconds, read off the reference's
# spectrogram and matched to what is on screen at that moment.
CLIPS = {
    "open_hit":     (0.00, 0.20, 0.002, 0.04),   # glitchy title hit
    "swell_zips":   (0.20, 1.72, 0.010, 0.10),   # air swell + three falling zips (word pops)
    "swell_glitch": (1.72, 3.70, 0.050, 0.12),   # swell with sparkly letter-scatter glitch
    "swell_short":  (3.70, 4.76, 0.050, 0.06),   # short swell (wipe)
    "impact":       (4.76, 5.95, 0.003, 0.15),   # sub boom + zips (product reveal)
    "swell_ticks":  (5.95, 7.95, 0.060, 0.10),   # swell ending in a tick burst (links clinking)
    "swell_zips2":  (7.95, 10.45, 0.040, 0.20),  # swell with word zips
    "pop":          (10.50, 11.30, 0.004, 0.25), # bubbly pop / split
    "pulses":       (11.58, 12.45, 0.003, 0.08), # rhythmic ping pulses (things multiplying)
    "swell_long":   (12.45, 16.55, 0.080, 0.25), # long swell with a ka-ching tone + ticks
    "swell_e":      (16.60, 18.25, 0.060, 0.10), # plain swell
    "ping1":        (18.27, 19.25, 0.003, 0.15), # UI ping (panel swap)
    "ping2":        (19.30, 20.25, 0.003, 0.15),
    "ping3":        (20.27, 21.55, 0.003, 0.20),
    "dclick":       (21.60, 21.86, 0.001, 0.04), # mouse double click
    "ping4":        (22.20, 23.40, 0.003, 0.20),
    "swell_f":      (23.75, 26.00, 0.080, 0.12), # swell with ping + zips
    "swell_g":      (26.00, 28.30, 0.060, 0.20), # swell ending in ticks
    "glitch_hit":   (28.60, 28.86, 0.001, 0.04), # bright digital hit
    "click_ping":   (29.18, 29.75, 0.001, 0.12), # click + short tone
    "rattle":       (30.30, 30.64, 0.001, 0.05), # quick tick rattle
    "dclick2":      (31.10, 31.44, 0.001, 0.08), # double click
    "click_ping2":  (32.33, 32.98, 0.001, 0.12),
    "swell_h":      (33.00, 35.18, 0.080, 0.10),
    "sparkle_zip":  (35.14, 35.40, 0.002, 0.06),
    "swell_pulses": (35.20, 37.50, 0.060, 0.15), # swell with rhythmic counting pulses
    "glitch_j":     (37.50, 38.32, 0.010, 0.15),
    "chime":        (39.04, 39.52, 0.002, 0.08), # multi-tone button chime
    "outro":        (39.50, 43.60, 0.040, 0.60), # logo swell to the end
}


def load(path):
    if path.endswith(".wav"):
        y, sr = sf.read(path, always_2d=True)
        assert sr == SR, sr
        return y
    with tempfile.TemporaryDirectory() as d:
        wav = os.path.join(d, "ref.wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-vn", "-ac", "2",
                        "-ar", str(SR), wav], check=True)
        return sf.read(wav, always_2d=True)[0]


def main():
    src, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    y = load(src)
    meta = {}
    for name, (a, b, fi, fo) in CLIPS.items():
        seg = y[int(a * SR):int(b * SR)].copy()
        n = len(seg)
        env = np.ones(n)
        ni, no = max(1, int(fi * SR)), max(1, int(fo * SR))
        env[:ni] = np.linspace(0, 1, ni) ** 2
        env[n - no:] = np.minimum(env[n - no:], np.linspace(1, 0, no) ** 2)
        seg *= env[:, None]
        sf.write(os.path.join(out, f"{name}.wav"), seg.astype(np.float32), SR, subtype="PCM_16")
        peak = float(np.abs(seg).max())
        meta[name] = {"src_start": a, "src_end": b, "duration": round(b - a, 3),
                      "peak_db": round(20 * np.log10(peak + 1e-9), 1)}
    with open(os.path.join(out, "sfx_index.json"), "w") as f:
        json.dump(meta, f, indent=2)
    print(json.dumps(meta, indent=1))


if __name__ == "__main__":
    main()
