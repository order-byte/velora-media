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


def decontaminate(f, a):
    """Unmix the shoot's wall colour out of semi-transparent edge pixels (hair, shoulders).

    The wall behind each edge pixel is estimated by a normalised blur of the
    fully-background pixels around it; the foreground colour then follows from
    I = a*F + (1-a)*B.
    """
    small = (W // 8, H // 8)
    bgw = cv2.resize(np.clip(1 - a * 1.6, 0, 1), small, interpolation=cv2.INTER_AREA)
    num = cv2.GaussianBlur(cv2.resize(f, small, interpolation=cv2.INTER_AREA) * bgw[..., None], (0, 0), 6)
    den = cv2.GaussianBlur(bgw, (0, 0), 6)[..., None]
    bg = cv2.resize(num / np.maximum(den, 1e-4), (W, H), interpolation=cv2.INTER_LINEAR)
    edge = (a > 0.03) & (a < 0.97)
    a3 = np.maximum(a, 0.03)[..., None]
    fg = np.clip((f - (1 - a3) * bg) / a3, 0, 1)
    return np.where(edge[..., None], fg, f)


# reel 2's on-camera skin (OpenCV float Lab: L 0-100, a/b around 0)
SKIN_TARGET = np.array([66.0, 14.0, 27.0], np.float32)   # reel 2 measured 60.3/10.6/26.3; brighter, a touch rosier


def skin_mask(raw, a):
    """Skin in the original footage: both the orange-lit side and the purple-filled side
    of the face, plus neck and hands; not hair, beard, shirt or the wall."""
    u8 = (np.clip(raw, 0, 1) * 255).astype(np.uint8)
    ycc = cv2.cvtColor(u8, cv2.COLOR_RGB2YCrCb).astype(np.float32)
    y, cr, cb = ycc[..., 0], ycc[..., 1], ycc[..., 2]
    # the orange key light pushes the lit cheek to Cr ~190 / Cb ~40, the purple fill side sits near Cr 138
    m = (np.clip((cr - 132) / 7, 0, 1) * np.clip((205 - cr) / 8, 0, 1) *
         np.clip((128 - cb) / 6, 0, 1) * np.clip((y - 38) / 15, 0, 1))
    m *= np.clip(a * 1.5 - 0.4, 0, 1)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    return cv2.GaussianBlur(m, (0, 0), 3)


def shirt_mask(raw, a, skin, holdout=None):
    """The light t-shirt in the original footage: the speaker below the chin, minus the
    strongly orange skin of hands and arms, dark bits and the can."""
    u8 = (np.clip(raw, 0, 1) * 255).astype(np.uint8)
    ycc = cv2.cvtColor(u8, cv2.COLOR_RGB2YCrCb).astype(np.float32)
    y, cr, cb = ycc[..., 0], ycc[..., 1], ycc[..., 2]
    rows = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    below_chin = np.clip((rows - 0.585) / 0.02, 0, 1)
    strong_skin = np.clip((cr - 150) / 8, 0, 1) * np.clip((104 - cb) / 8, 0, 1)
    m = np.clip((y - 90) / 20, 0, 1) * (1 - strong_skin) * below_chin * np.clip(a * 1.5 - 0.4, 0, 1)
    if holdout is not None:
        m *= 1 - np.clip(holdout * 2, 0, 1)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
    return cv2.GaussianBlur(m, (0, 0), 4)


def skin_match(g, w):
    """Give the skin reel 2's look: one warm tone across the face, brighter, softer light."""
    if w.sum() < 50:
        return g
    lab = cv2.cvtColor(np.clip(g, 0, 1), cv2.COLOR_RGB2LAB)
    small = (W // 6, H // 6)
    ws = cv2.resize(w, small, interpolation=cv2.INTER_AREA)
    den = np.maximum(cv2.GaussianBlur(ws, (0, 0), 5), 1e-4)

    def low(ch):
        x = cv2.GaussianBlur(cv2.resize(ch, small, interpolation=cv2.INTER_AREA) * ws, (0, 0), 5) / den
        return cv2.resize(x, (W, H), interpolation=cv2.INTER_LINEAR)

    out = []
    # per channel: how much of the large-scale light shape to keep, and how much to lift the
    # fine detail (lips, cheeks, brows) so the face keeps its life after the tone shift
    for c, keep, detail, tgt in ((0, 0.55, 1.0, SKIN_TARGET[0]), (1, 0.35, 2.0, SKIN_TARGET[1]),
                                 (2, 0.35, 1.5, SKIN_TARGET[2])):
        ch = lab[..., c]
        lo = low(ch)
        mean_lo = float((lo * w).sum() / w.sum())
        new = (ch - lo) * detail + tgt + (lo - mean_lo) * keep
        out.append(ch * (1 - w) + new * w)
    L = out[0]
    Lb = cv2.bilateralFilter(L.astype(np.float32), 9, 6, 5)          # gentle skin smoothing
    out[0] = L * (1 - 0.2 * w) + Lb * 0.2 * w
    return np.clip(cv2.cvtColor(np.stack(out, -1).astype(np.float32), cv2.COLOR_LAB2RGB), 0, 1)


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
        f = decontaminate(f, a)
        skin = skin_mask(f, a)
        shirt = shirt_mask(f, a, skin, self.holdout)
        raw = f.copy()
        f = despill(f, a)
        # iPhone footage is crisper than the room plate's lens: take the edge off so they match
        f = cv2.GaussianBlur(f, (0, 0), 0.7)
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
        g = skin_match(g, skin)
        # the t-shirt keeps the colour it has in the raw footage
        return g * (1 - shirt[..., None]) + raw * shirt[..., None], a

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
