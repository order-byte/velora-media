#!/usr/bin/env python3
"""Cut individual sound effects out of the Drive 1 SFX track (5UxnBbskneaPT7WI.mp4).

The track has no music bed, so every hit can be lifted cleanly. Times were found
with onset detection on the source audio.

usage: python3 cut_sfx.py <drive1.mp4> <out_dir>
"""
import os
import subprocess
import sys

# name: (start_s, duration_s, fade_out_s)
CUTS = {
    # mouse clicks (down / up pairs)
    "click_down": (21.695, 0.110, 0.02),
    "click_up": (21.823, 0.120, 0.03),
    "click2_down": (31.161, 0.120, 0.03),
    "click2_up": (31.289, 0.120, 0.03),
    # soft UI ticks used for typing / text reveals
    "tick_1": (7.312, 0.044, 0.01),
    "tick_2": (7.354, 0.050, 0.01),
    "tick_3": (7.406, 0.058, 0.01),
    "tick_4": (7.464, 0.090, 0.02),
    "tick_5": (7.566, 0.088, 0.02),
    "tick_6": (7.654, 0.050, 0.01),
    "tick_7": (7.704, 0.036, 0.01),
    "tick_8": (7.736, 0.080, 0.02),
    "tick_9": (30.346, 0.044, 0.01),
    "tick_10": (30.388, 0.054, 0.01),
    "tick_11": (30.440, 0.060, 0.01),
    "tick_12": (30.498, 0.080, 0.02),
    # bubble pops
    "pop_1": (11.620, 0.160, 0.05),
    "pop_2": (11.788, 0.120, 0.04),
    "pop_soft": (29.254, 0.220, 0.08),
    "pop_burst": (11.600, 1.050, 0.25),
    # whooshes / transitions
    "whoosh_intro": (0.200, 0.950, 0.15),
    "whoosh_a": (16.600, 1.650, 0.35),
    "whoosh_b": (33.300, 1.500, 0.35),
    "whoosh_c": (26.300, 1.300, 0.30),
    "whoosh_d": (24.300, 0.750, 0.15),
    # textures
    "shimmer": (37.400, 0.900, 0.30),
    "swell": (22.200, 1.200, 0.30),
    "counter": (12.900, 0.600, 0.10),
    # end-card logo reveal
    "logo_hit": (40.850, 1.840, 0.50),
}


def main():
    src, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    for name, (start, dur, fade) in CUTS.items():
        af = f"afade=t=in:d=0.003,afade=t=out:st={max(0.0, dur - fade):.3f}:d={fade:.3f}"
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-ss", f"{start:.3f}", "-t", f"{dur:.3f}",
             "-i", src, "-vn", "-af", af, "-ar", "48000", "-ac", "2",
             os.path.join(out, f"{name}.wav")],
            check=True,
        )
    print(f"wrote {len(CUTS)} clips to {out}")


if __name__ == "__main__":
    main()
