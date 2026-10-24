#!/usr/bin/env python3
"""Extract the portfolio segments that play inside the showreel's glass cards.

Each segment becomes a folder of 30 fps JPEG frames (1120x630). The vertical
NeuralHive ad is centred over a blurred, darkened copy of itself so it fills a
16:9 card without cropping its text.

usage: python3 prepare_clips.py <sources.json> <out_dir>

sources.json maps the work ids below to video paths, e.g.
  {"commas": ".../5UxnBbskneaPT7WI.mp4", "nano": ".../NanoSyllabus_Promo_Draft1_16x9.mp4",
   "fortknox": ".../FortKnox_Loop_90s_share2.mp4", "neural": ".../NeuralHive_Presale_Ad_9x16.mp4"}
"""
import json
import os
import subprocess
import sys

W, H, FPS, DUR = 1120, 630, 30, 5.4

# clip id: (work id, start seconds)
SEGMENTS = {
    # grid 1 - PRODUCT VIDEOS
    "g1_commas": ("commas", 4.9),
    "g1_fortknox": ("fortknox", 81.0),
    "g1_neural": ("neural", 25.4),
    "g1_nano": ("nano", 16.2),
    # grid 2 - UI ANIMATION
    "g2_nano": ("nano", 21.0),
    "g2_commas": ("commas", 30.0),
    "g2_fortknox": ("fortknox", 57.5),
    "g2_neural": ("neural", 9.0),
    # grid 3 - EXPLAINERS
    "g3_fortknox": ("fortknox", 19.5),
    "g3_neural": ("neural", 15.5),
    "g3_commas": ("commas", 10.8),
    "g3_nano": ("nano", 38.5),
}

VERTICAL = {"neural"}


def vf_for(work):
    if work in VERTICAL:
        return (
            f"[0:v]fps={FPS},split[a][b];"
            f"[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
            f"gblur=sigma=26,eq=brightness=0.03:saturation=1.5[bg];"
            f"[b]scale=-2:{H}[fg];[bg][fg]overlay=(W-w)/2:0[v]"
        )
    return f"[0:v]fps={FPS},scale={W}:{H}:flags=lanczos[v]"


def main():
    sources = json.load(open(sys.argv[1]))
    out = sys.argv[2]
    for clip, (work, start) in SEGMENTS.items():
        d = os.path.join(out, clip)
        os.makedirs(d, exist_ok=True)
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-ss", f"{start}", "-t", f"{DUR}", "-i", sources[work],
             "-filter_complex", vf_for(work), "-map", "[v]", "-q:v", "2",
             os.path.join(d, "%04d.jpg")],
            check=True,
        )
        print(clip, len(os.listdir(d)), "frames")


if __name__ == "__main__":
    main()
