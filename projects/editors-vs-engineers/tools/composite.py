"""Put the matted speaker into the warm room plate and grade them to match.

Per frame: zoom/crop the footage, cut the speaker out with the RVM alpha (plus a
static holdout for foreground props like the can on the table), remove the
purple wall spill from the edges, grade the speaker with the warm look, wrap a
little of the room's light around the edges, then add one shared grain layer so
speaker and room read as one camera.

Usage:
  python3 composite.py FOOTAGE.mp4 ALPHA.mkv PLATE.png OUT.mp4 [--holdout MASK.png]
                       [--zoom 1.15] [--cx 0.5] [--cy 0.45] [--frame N --png OUT.png]
"""
import argparse
import json
import os
import subprocess
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from make_lut import grade  # noqa: E402

W, H = 1080, 1920


def probe(path):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                   "stream=width,height,r_frame_rate", "-of", "json", path])
    s = json.loads(out)["streams"][0]
    return s["width"], s["height"], s["r_frame_rate"]


def zoom(img, z, cx, cy, interp=cv2.INTER_CUBIC):
    """Scale about (cx, cy) in normalised coords and crop back to W x H."""
    m = np.array([[z, 0, (1 - z) * cx * W], [0, z, (1 - z) * cy * H]], np.float32)
    return cv2.warpAffine(img, m, (W, H), flags=interp, borderMode=cv2.BORDER_REPLICATE)


def despill(rgb, a):
    """Pull the magenta wall bounce out of the speaker's edges and shirt."""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    limit = np.minimum(r, g) * 0.35 + g * 0.65     # blue allowed relative to green
    edge = np.clip(1.0 - np.abs(a - 0.5) * 2, 0, 1) * 0.6 + 0.4
    b2 = np.where(b > limit, b - (b - limit) * edge, b)
    m = (r + b2) / 2 - g                             # residual magenta
    r2 = r - np.clip(m, 0, None) * 0.25 * edge
    return np.stack([r2, g, b2], -1)


class Compositor:
    def __init__(self, plate, holdout=None, z=1.15, cx=0.5, cy=0.45, seed=11, sat=0.56, exposure=0.85, warm=1.0):
        self.plate = plate.astype(np.float32) / 255
        self.plate_soft = cv2.GaussianBlur(self.plate, (0, 0), 18)
        self.holdout = None if holdout is None else zoom(holdout.astype(np.float32) / 255, z, cx, cy)
        self.z, self.cx, self.cy = z, cx, cy
        self.sat, self.exposure, self.warm = sat, exposure, warm
        self.rng = np.random.default_rng(seed)

    def speaker(self, frame, alpha):
        """The graded, cut-out speaker in the reel framing: (rgb float 0..1, alpha float 0..1)."""
        f = zoom(frame, self.z, self.cx, self.cy).astype(np.float32) / 255
        a = zoom(alpha, self.z, self.cx, self.cy, cv2.INTER_LINEAR).astype(np.float32) / 255
        if self.holdout is not None:
            a = np.maximum(a, self.holdout)
        # matte edge: tiny choke + soften so hair doesn't fringe
        a = cv2.GaussianBlur(np.clip((a - 0.04) / 0.92, 0, 1), (0, 0), 0.8)
        f = despill(f, a)
        # the phone footage is far more saturated than the reference: calm it before the look
        l = (f @ np.array([0.2126, 0.7152, 0.0722], np.float32))[..., None]
        f = (l + (f - l) * self.sat) * self.exposure
        # grade the speaker into the room's look (only where the speaker is), then warm the key a touch
        g = np.zeros_like(f)
        m = a > 0.004
        px = grade(np.clip(f[m], 0, 1)) * np.array([1.02, 0.99, 0.93], np.float32)
        # the shoot's purple fill light: pull magenta out of the shirt, warm the face's shadow side
        mag = np.clip((px[:, 0] + px[:, 2]) / 2 - px[:, 1], 0, None)[:, None]
        px = px - mag * np.array([0.55, 0.0, 0.65], np.float32)
        lum = (px @ np.array([0.2126, 0.7152, 0.0722], np.float32))[:, None]
        px = px + np.clip(0.55 - lum, 0, None) * np.array([0.09, 0.035, -0.02], np.float32) * self.warm
        g[m] = px
        return g, a

    def __call__(self, frame, alpha):
        g, a = self.speaker(frame, alpha)
        # light wrap: the room's blurred light bleeds over the outer edge of the speaker
        rim = np.clip(a * (1 - cv2.GaussianBlur(a, (0, 0), 6)) * 3, 0, 1)[..., None]
        g = g * (1 - 0.35 * rim) + self.plate_soft * 0.35 * rim
        a3 = a[..., None]
        out = g * a3 + self.plate * (1 - a3)
        # one shared grain pass so plate and speaker match
        n = self.rng.normal(0, 0.010, out.shape[:2]).astype(np.float32)
        out = out + cv2.GaussianBlur(n, (0, 0), 0.6)[..., None]
        return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)


def read_frames(path, w, h, pix, start=0):
    ch = 3 if pix == "rgb24" else 1
    cmd = ["ffmpeg", "-v", "error"]
    p = subprocess.Popen(cmd + ["-i", path, "-f", "rawvideo", "-pix_fmt", pix, "-"], stdout=subprocess.PIPE)
    i = 0
    while True:
        buf = p.stdout.read(w * h * ch)
        if len(buf) < w * h * ch:
            break
        if i >= start:
            a = np.frombuffer(buf, np.uint8).reshape(h, w, ch)
            yield a if ch == 3 else a[..., 0]
        i += 1
    p.stdout.close()
    p.wait()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("footage")
    ap.add_argument("alpha")
    ap.add_argument("plate")
    ap.add_argument("out")
    ap.add_argument("--holdout")
    ap.add_argument("--zoom", type=float, default=1.15)
    ap.add_argument("--cx", type=float, default=0.5)
    ap.add_argument("--cy", type=float, default=0.45)
    ap.add_argument("--frame", type=int, help="render only this frame index to --png")
    ap.add_argument("--png")
    args = ap.parse_args()

    w, h, fps = probe(args.footage)
    plate = cv2.cvtColor(cv2.imread(args.plate), cv2.COLOR_BGR2RGB)
    hold = cv2.imread(args.holdout, cv2.IMREAD_GRAYSCALE) if args.holdout else None
    comp = Compositor(plate, hold, args.zoom, args.cx, args.cy)

    frames = read_frames(args.footage, w, h, "rgb24")
    alphas = read_frames(args.alpha, w, h, "gray")
    if args.frame is not None:
        for i, (f, a) in enumerate(zip(frames, alphas)):
            if i == args.frame:
                cv2.imwrite(args.png, cv2.cvtColor(comp(f, a), cv2.COLOR_RGB2BGR))
                return
        return

    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", fps, "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "14",
                            "-pix_fmt", "yuv420p", args.out], stdin=subprocess.PIPE)
    for f, a in zip(frames, alphas):
        enc.stdin.write(comp(f, a).tobytes())
    enc.stdin.close()
    enc.wait()


if __name__ == "__main__":
    main()
