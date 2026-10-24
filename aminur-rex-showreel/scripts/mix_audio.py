#!/usr/bin/env python3
"""Mix the showreel soundtrack.

Music bed: the reference edit's own track (kept whole, so every hit lands on
the same beat as our matching cuts). On top of it go sound effects cut from
the Drive 1 video (assets/sfx, see cut_sfx.py), placed on our on-screen events.

usage: python3 mix_audio.py <reference.mp4> <sfx_dir> <out.wav>
"""
import os
import subprocess
import sys

import numpy as np

SR = 48000
DURATION = 25.05

# (time_s, sfx name, gain_db). Times are when the clip should START.
EVENTS = [
    # name title
    (0.02, "whoosh_intro", -4),
    (0.24, "tick_4", -10), (0.31, "tick_5", -10), (0.38, "tick_8", -10),
    (1.00, "shimmer", -12),
    (2.03, "click_down", -3), (2.76, "click_up", -4),
    (2.80, "pop_2", -9),
    (3.67, "whoosh_a", -3),
    # X profile card rises, avatar pops, Follow click, whip out
    (4.40, "whoosh_d", -5),
    (4.74, "pop_soft", -6),
    (4.86, "tick_1", -9), (4.93, "tick_2", -9), (5.00, "tick_3", -9), (5.07, "tick_6", -9),
    (5.05, "pop_1", -7), (5.20, "pop_1", -8), (5.35, "pop_1", -7),
    (5.60, "click2_down", -2), (5.68, "click2_up", -3),
    (5.85, "whoosh_c", -4),
    # software
    (6.30, "pop_1", -5), (6.52, "pop_2", -5), (6.86, "pop_1", -4),
    # chat
    (7.30, "whoosh_d", -6),
    (8.35, "pop_2", -6),
    (9.46, "click_down", -2), (9.60, "click_up", -3),
    (9.70, "whoosh_b", -3),
    # grids
    (10.24, "counter", -9),
    (12.94, "whoosh_c", -4), (13.42, "counter", -9),
    (17.20, "whoosh_a", -4), (17.83, "pop_2", -7),
    (21.90, "shimmer", -11),
    # end card
    (22.70, "logo_hit", -2),
    (24.10, "shimmer", -12),
]

# typing ticks while the chat message types out (7.78 -> 8.62, 50 chars)
TYPE_TICKS = ["tick_%d" % i for i in (1, 2, 3, 6, 7, 9, 10, 11, 1, 3, 2, 6, 9, 7, 10, 11, 2, 1, 3, 6, 9, 10, 7, 11)]
for k, name in enumerate(TYPE_TICKS):
    EVENTS.append((7.78 + k * 0.035, name, -11 + (k % 3) * 1.0))


def load(path):
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
        capture_output=True, check=True,
    ).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).copy()


def main():
    ref, sfx_dir, out = sys.argv[1], sys.argv[2], sys.argv[3]
    n = int(DURATION * SR)
    bed = load(ref)[:n]
    mix = np.zeros((n, 2), dtype=np.float32)
    mix[: len(bed)] += bed * 0.92

    cache = {}
    for t, name, db in EVENTS:
        if name not in cache:
            cache[name] = load(os.path.join(sfx_dir, name + ".wav"))
        clip = cache[name] * (10 ** (db / 20))
        a = int(t * SR)
        b = min(n, a + len(clip))
        mix[a:b] += clip[: b - a]

    # gentle fade at the tail, soft-clip safety
    tail = int(0.25 * SR)
    mix[-tail:] *= np.linspace(1, 0, tail)[:, None]
    mix = np.tanh(mix * 1.05) / np.tanh(1.05)

    tmp = out + ".raw.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", tmp],
        input=mix.astype(np.float32).tobytes(), check=True,
    )
    # loudness for social: -14 LUFS integrated, -1 dBTP ceiling
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", tmp, "-af", "loudnorm=I=-14:TP=-1.0:LRA=11", "-ar", str(SR), out],
        check=True,
    )
    os.remove(tmp)
    print("wrote", out, f"({len(EVENTS)} sfx events)")


if __name__ == "__main__":
    main()
