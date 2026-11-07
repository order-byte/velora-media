#!/usr/bin/env python3
"""Remove a static corner logo from a video and re-encode it at higher quality.

The logo region is filled per frame with a smooth surface interpolated from the
pixels just outside the region (a Coons patch over the four edges, then a few
Laplace relaxation passes), working directly on the YUV 4:2:0 planes so no
colour conversion is introduced. The cleaned frames are then upscaled to
1920x1080 with Lanczos, lightly deblocked and sharpened, and encoded with x264
at a high-quality CRF. Frame rate, duration and audio are kept as in the input.

Usage:
    python3 scripts/remove_logo.py INPUT.mp4 OUTPUT.mp4 [--box X0 Y0 X1 Y1]
"""

import argparse
import json
import subprocess
import sys

import numpy as np

# Logo box (inclusive pixel coords) for the 1138x640 source, with a small
# margin around the badge and its drop shadow.
DEFAULT_BOX = (14, 14, 141, 70)
BAND = 3          # width of the edge band averaged for boundary values
EDGE_SMOOTH = 7   # 1-D smoothing along each edge to suppress codec noise
RELAX_ITERS = 60  # Laplace relaxation passes after the Coons patch


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,r_frame_rate",
         "-of", "json", path],
        check=True, capture_output=True, text=True).stdout
    s = json.loads(out)["streams"][0]
    return s["width"], s["height"], s["r_frame_rate"]


def smooth1d(v, k):
    if k <= 1:
        return v
    pad = k // 2
    vp = np.pad(v, pad, mode="edge")
    kern = np.ones(k) / k
    return np.convolve(vp, kern, mode="valid")


def fill_region(plane, x0, y0, x1, y1, band):
    """Replace plane[y0:y1+1, x0:x1+1] with a smooth interpolation of its border."""
    p = plane.astype(np.float32)
    w = x1 - x0 + 1
    h = y1 - y0 + 1
    # Boundary values: mean of a band just outside each edge.
    top = p[max(y0 - band, 0):y0, x0:x1 + 1].mean(0)
    bot = p[y1 + 1:y1 + 1 + band, x0:x1 + 1].mean(0)
    lef = p[y0:y1 + 1, max(x0 - band, 0):x0].mean(1)
    rig = p[y0:y1 + 1, x1 + 1:x1 + 1 + band].mean(1)
    top, bot = smooth1d(top, EDGE_SMOOTH), smooth1d(bot, EDGE_SMOOTH)
    lef, rig = smooth1d(lef, EDGE_SMOOTH), smooth1d(rig, EDGE_SMOOTH)
    # Corners from the diagonal neighbours.
    c00 = p[y0 - 1, x0 - 1]
    c01 = p[y0 - 1, x1 + 1]
    c10 = p[y1 + 1, x0 - 1]
    c11 = p[y1 + 1, x1 + 1]

    # Coons patch with the region's surrounding ring as boundary.
    u = (np.arange(w) + 1) / (w + 1)
    v = (np.arange(h) + 1) / (h + 1)
    U, V = np.meshgrid(u, v)
    ruled = (1 - V) * top[None, :] + V * bot[None, :] \
        + (1 - U) * lef[:, None] + U * rig[:, None]
    bilin = (1 - U) * (1 - V) * c00 + U * (1 - V) * c01 \
        + (1 - U) * V * c10 + U * V * c11
    f = ruled - bilin

    # Laplace relaxation with fixed boundary ring for an extra-smooth result.
    g = np.empty((h + 2, w + 2), np.float32)
    g[0, 1:-1], g[-1, 1:-1] = top, bot
    g[1:-1, 0], g[1:-1, -1] = lef, rig
    g[0, 0], g[0, -1], g[-1, 0], g[-1, -1] = c00, c01, c10, c11
    g[1:-1, 1:-1] = f
    for _ in range(RELAX_ITERS):
        g[1:-1, 1:-1] = 0.25 * (g[:-2, 1:-1] + g[2:, 1:-1]
                                + g[1:-1, :-2] + g[1:-1, 2:])
    plane[y0:y1 + 1, x0:x1 + 1] = np.clip(np.rint(g[1:-1, 1:-1]), 0, 255)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--box", type=int, nargs=4, default=DEFAULT_BOX,
                    metavar=("X0", "Y0", "X1", "Y1"))
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--crf", type=int, default=15)
    args = ap.parse_args()

    W, H, fps = probe(args.input)
    x0, y0, x1, y1 = args.box
    cw, ch = W // 2, H // 2
    ysz, csz = W * H, cw * ch
    fsz = ysz + 2 * csz

    dec = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-i", args.input,
         "-f", "rawvideo", "-pix_fmt", "yuv420p", "-"],
        stdout=subprocess.PIPE)

    vf = (f"hqdn3d=1.2:1.0:2.5:2.0,"
          f"scale={args.width}:{args.height}:flags=lanczos+accurate_rnd+full_chroma_int,"
          f"cas=0.35,format=yuv420p")
    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y",
         "-f", "rawvideo", "-pix_fmt", "yuv420p", "-s", f"{W}x{H}",
         "-r", fps, "-i", "-",
         "-i", args.input,
         "-map", "0:v:0", "-map", "1:a:0?",
         "-vf", vf,
         "-c:v", "libx264", "-preset", "slow", "-crf", str(args.crf),
         "-profile:v", "high", "-tune", "animation",
         "-colorspace", "bt709", "-color_primaries", "bt709",
         "-color_trc", "bt709",
         "-c:a", "copy",
         "-movflags", "+faststart",
         args.output],
        stdin=subprocess.PIPE)

    n = 0
    while True:
        buf = dec.stdout.read(fsz)
        if len(buf) < fsz:
            break
        frame = np.frombuffer(buf, np.uint8).copy()
        Y = frame[:ysz].reshape(H, W)
        U = frame[ysz:ysz + csz].reshape(ch, cw)
        V = frame[ysz + csz:].reshape(ch, cw)
        fill_region(Y, x0, y0, x1, y1, BAND)
        cx0, cy0, cx1, cy1 = x0 // 2, y0 // 2, (x1 + 1) // 2, (y1 + 1) // 2
        fill_region(U, cx0, cy0, cx1, cy1, max(BAND // 2, 2))
        fill_region(V, cx0, cy0, cx1, cy1, max(BAND // 2, 2))
        enc.stdin.write(frame.tobytes())
        n += 1
        if n % 300 == 0:
            print(f"{n} frames", file=sys.stderr)

    enc.stdin.close()
    dec.wait()
    rc = enc.wait()
    print(f"done: {n} frames", file=sys.stderr)
    sys.exit(rc)


if __name__ == "__main__":
    main()
