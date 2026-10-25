"""Gig 2 HiFi reel (video only) + SFX cue sheet.

usage: render2.py OUT.mp4 CUES.json [--frames 0,120,...]
30 fps, beat = 14 frames, bar = 56 frames. 16 bars + 36-frame tail = 932 frames (31.1 s).
  0-1   cold open: "Your product," / "up close."
  2-5   UI close-ups with camera moves (one per bar)
  6-7   type card: Feature spots / Product demos / Launch films
  8-13  montage, half-bar cuts with camera moves and whips
  14-15 end card + tail
"""
import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import render as R  # shared drawing helpers and fonts

FPS, W, H = 30, 1920, 1080
BEAT, BAR = 14, 56
TOTAL = 16 * BAR + 36
BG = (14, 15, 12)
LIME = R.LIME
PAPER = R.PAPER
SRC = R.SRC


def b(n):
    return n * BAR


def decode_native(src, t, n):
    """Decode at the source's own resolution (4K stays 4K) so zooms stay sharp."""
    w, h = (3840, 2160) if src in (3, 5) else (1920, 1080)
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(SRC[src]), "-frames:v", str(n),
           "-vf", f"fps={FPS},scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    k = len(raw) // (w * h * 3)
    arr = np.frombuffer(raw[: k * w * h * 3], np.uint8).reshape(k, h, w, 3)
    if k < n:
        arr = np.concatenate([arr, np.repeat(arr[-1:], n - k, 0)], 0)
    return arr


def ease_io(p):
    p = min(max(p, 0.0), 1.0)
    return p * p * (3 - 2 * p)


def camera(img, zoom, cx, cy, dx=0.0, blur=0):
    """Render a 1920x1080 view of img: zoom relative to fitting the frame, centered on (cx, cy) in 0..1."""
    sh, sw = img.shape[:2]
    s = zoom * W / sw
    # keep the view inside the source
    half_w, half_h = W / (2 * s), H / (2 * s)
    px = min(max(cx * sw, half_w), sw - half_w)
    py = min(max(cy * sh, half_h), sh - half_h)
    M = np.array([[s, 0, W / 2 - s * px + dx], [0, s, H / 2 - s * py]], np.float32)
    interp = cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC
    out = cv2.warpAffine(img, M, (W, H), flags=interp, borderMode=cv2.BORDER_REFLECT)
    if blur > 1:
        k = np.full((1, int(blur)), 1.0 / int(blur), np.float32)
        out = cv2.filter2D(out, -1, k, borderType=cv2.BORDER_REFLECT)
    return out


SHOTS = []  # (start, n, src, t, cam=(z0,cx0,cy0,z1,cx1,cy1), opts)


def shot(start, n, src, t, cam, **o):
    SHOTS.append((start, n, src, t, cam, o))


# UI close-ups, bars 2-5
closeups = [
    (5, 27.0, (1.70, 0.47, 0.53, 1.22, 0.52, 0.52), "UI ANIMATION  ·  NANOSYLLABUS"),
    (1, 18.2, (1.30, 0.30, 0.40, 1.08, 0.50, 0.45), "PRODUCT DEMO  ·  COMMAS"),
    (1, 32.5, (1.00, 0.50, 0.50, 1.32, 0.64, 0.44), "DATA UI  ·  COMMAS"),
    (5, 20.4, (1.55, 0.50, 0.50, 1.12, 0.50, 0.50), "FEATURE SPOT  ·  NANOSYLLABUS"),
]
for k, (s, t, cam, label) in enumerate(closeups):
    shot(b(2) + k * BAR, BAR, s, t, cam, label=label, punch=(k == 0), flash=(k == 0))

montage = [
    (4, 58.6, (1.00, 0.5, 0.5, 1.12, 0.48, 0.52)),
    (1, 25.2, (1.20, 0.50, 0.55, 1.05, 0.50, 0.50)),
    (6, 18.8, (1.00, 0.5, 0.5, 1.15, 0.50, 0.55)),
    (5, 45.2, (1.35, 0.45, 0.55, 1.10, 0.50, 0.50)),
    (4, 6.3, (1.00, 0.5, 0.5, 1.10, 0.62, 0.55)),
    (1, 38.2, (1.25, 0.42, 0.55, 1.10, 0.50, 0.52)),
    (6, 22.3, (1.00, 0.5, 0.5, 1.12, 0.50, 0.50)),
    (5, 34.3, (1.40, 0.50, 0.52, 1.15, 0.50, 0.50)),
    (4, 82.0, (1.00, 0.5, 0.5, 1.14, 0.60, 0.50)),
    (2, 3.2, (1.10, 0.50, 0.55, 1.00, 0.5, 0.5)),
    (1, 12.3, (1.00, 0.5, 0.5, 1.12, 0.50, 0.55)),
    (4, 47.0, (1.00, 0.5, 0.5, 1.10, 0.45, 0.45)),
]
whips = {1, 4, 7, 10}
for k, (s, t, cam) in enumerate(montage):
    shot(b(8) + k * 28, 28, s, t, cam, punch=(k == 0), flash=(k == 0), whip_out=(k in whips), whip_in=(k - 1 in whips))

CUES = []


def cue(fr, name, gain=1.0):
    CUES.append({"frame": int(fr), "sfx": name, "gain": gain})


cue(0, "pop1", 0.8); cue(BEAT * 2, "pop3", 0.7)
cue(b(1), "whB", 0.9); cue(b(1) + BEAT * 2, "pop2", 0.7)
cue(b(2), "whA", 1.0)
for k in range(1, 4):
    cue(b(2) + k * BAR, "swoosh", 0.8)
for k in range(4):
    cue(b(2) + k * BAR + 4, "tick2", 0.5)
cue(b(6), "whE", 0.7)
for k, beat in enumerate((0, 3, 6)):
    cue(b(6) + beat * BEAT, "click2" if k < 2 else "pop1", 0.8)
cue(b(8) - 40, "riser_med", 0.5)
cue(b(8), "whD", 1.0)
for st, n, s, t, cam, o in SHOTS:
    if o.get("whip_out"):
        cue(st + n - 2, "swoosh", 0.9)
cue(b(11), "whC", 0.7)
cue(b(14) - 67, "riser_big", 0.45)
cue(b(14), "whA", 1.0)
cue(b(14) + BEAT, "pop1", 0.6); cue(b(14) + 2 * BEAT, "pop2", 0.6); cue(b(15), "click2", 0.8)
cue(b(16), "pop3", 0.6)

# ---------------------------------------------------------------- layers

CUT = Image.open(R.ROOT / "work/aminur_cutout.png").convert("RGBA")
cut_h = 1000
cut_w = round(CUT.width * cut_h / CUT.height)
CUTOUT = np.asarray(CUT.resize((cut_w, cut_h), Image.LANCZOS)).astype(np.float32) / 255

yy, xx = np.mgrid[0:H, 0:W]
GLOW = np.clip(1 - np.sqrt(((xx - 1460) / 620.0) ** 2 + ((yy - 560) / 520.0) ** 2), 0, 1) ** 2 * 0.22
GLOW = GLOW[..., None].astype(np.float32)

F_HERO = R.font("ArchivoExp-ExtraBold", 176)
F_LIST = R.font("ArchivoExp-ExtraBold", 112)
F_END = R.font("ArchivoExp-ExtraBold", 112)


def dark():
    f = np.empty((H, W, 3), np.uint8)
    f[:] = BG
    return f


def corner(frame):
    R.paste(frame, R.text_rgba("AMINUR RAHMAN — HIFI SAAS VIDEOS", R.F_MONO, PAPER), 120, 84, 0.55)
    R.paste(frame, R.text_rgba("@aminur_rex", R.F_MONO, PAPER), W - 120 - 175, 84, 0.55)


def cold_open(f):
    fr = dark()
    R.reveal_word(fr, R.text_rgba("Your product,", F_HERO, PAPER), 120, 330, f, 0, dur=7)
    R.reveal_word(fr, R.text_rgba("up close.", F_HERO, LIME), 120, 540, f, b(1), dur=6)
    corner(fr)
    if b(1) <= f < b(1) + 3:
        a = [0.85, 0.45, 0.15][f - b(1)]
        fr = (fr.astype(np.float32) * (1 - a) + np.array(LIME, np.float32) * a).astype(np.uint8)
    return fr


def type_card(f):
    fr = dark()
    lines = [("Feature spots.", PAPER, 0), ("Product demos.", PAPER, 3), ("Launch films.", LIME, 6)]
    for i, (txt, col, beat) in enumerate(lines):
        R.reveal_word(fr, R.text_rgba(txt, F_LIST, col), 120, 250 + i * 150, f, b(6) + beat * BEAT, dur=6)
    R.paste(fr, R.text_rgba("WHAT WE MAKE", R.F_MONO, PAPER), 120, 200, 0.55)
    corner(fr)
    return fr


def end_card(f):
    lf = f - b(14)
    fr = (dark().astype(np.float32) + GLOW * np.array(LIME, np.float32)).clip(0, 255).astype(np.uint8)
    p = R.ease_out(lf / 14)
    R.paste(fr, CUTOUT, W - cut_w + 40, H - cut_h + (1 - p) * 160, min(1, lf / 6))
    x = 120
    if lf >= 2:
        pa = R.ease_out((lf - 2) / 8)
        R.paste(fr, R.text_rgba("AMINUR RAHMAN — ANIMATION STUDIO, KOLKATA", R.F_MONO, PAPER), x - 20 * (1 - pa), 300, pa * 0.7)
    R.reveal_word(fr, R.text_rgba("HiFi SaaS", F_END, PAPER), x, 350, f, b(14) + BEAT, dur=7)
    R.reveal_word(fr, R.text_rgba("videos.", F_END, LIME), x, 480, f, b(14) + 2 * BEAT, dur=7)
    if f >= b(15):
        pa = R.ease_out((f - b(15)) / 8)
        btn = R.pill("MESSAGE ME BEFORE YOU ORDER", R.F_MONO_L, BG, LIME, 1.0, pad=34, h=80)
        sc = 0.88 + 0.12 * pa
        bh, bw = btn.shape[:2]
        btn_s = cv2.resize(btn, (int(bw * sc), int(bh * sc)), interpolation=cv2.INTER_AREA)
        R.paste(fr, btn_s, x, 660 + (bh - btn_s.shape[0]) / 2, pa)
    R.paste(fr, R.text_rgba("@aminur_rex", R.F_MONO, PAPER), x, H - 84 - 34, 0.6)
    return fr


MARK = R.pill("@aminur_rex", R.F_MONO_S, PAPER, R.INK, 0.55)


def clip_frame(img, lf, n, cam, o):
    p = ease_io(lf / max(n - 1, 1))
    z0, x0, y0, z1, x1, y1 = cam
    z = z0 + (z1 - z0) * p
    cx = x0 + (x1 - x0) * p
    cy = y0 + (y1 - y0) * p
    if o.get("punch") and lf < 8:
        z *= 1.10 - 0.10 * R.ease_out(lf / 8)
    dx, blur = 0.0, 0
    if o.get("whip_out") and lf >= n - 3:
        j = lf - (n - 3)
        dx, blur = -[0.10, 0.28, 0.55][j] * W, [40, 110, 190][j]
    if o.get("whip_in") and lf < 3:
        dx, blur = [0.42, 0.14, 0.03][lf] * W, [170, 80, 22][lf]
    out = camera(img, z, cx, cy, dx, blur)
    R.paste(out, MARK, W - 64 - MARK.shape[1], H - 96 - MARK.shape[0], 1.0)
    if o.get("label") and lf >= 3:
        pa = R.ease_out((lf - 3) / 7)
        lab = R.pill(o["label"], R.F_MONO_S, PAPER, R.INK, 0.62, dot=LIME)
        R.paste(out, lab, 64 - 30 * (1 - pa), H - 96 - lab.shape[0], pa)
    if o.get("flash") and lf < 3:
        a = [0.9, 0.5, 0.18][lf]
        out = (out.astype(np.float32) * (1 - a) + np.array(LIME, np.float32) * a).astype(np.uint8)
    return out


def frames_iter(only=None):
    want = set(only) if only is not None else None

    def need(lo, hi):
        return want is None or any(lo <= x < hi for x in want)

    for f in range(0, b(2)):
        if want is None or f in want:
            yield f, cold_open(f)
    for st, n, s, t, cam, o in [x for x in SHOTS if x[0] < b(6)]:
        if need(st, st + n):
            clip = decode_native(s, t, n)
            for lf in range(n):
                if want is None or st + lf in want:
                    yield st + lf, clip_frame(clip[lf], lf, n, cam, o)
    for f in range(b(6), b(8)):
        if want is None or f in want:
            yield f, type_card(f)
    for st, n, s, t, cam, o in [x for x in SHOTS if x[0] >= b(8)]:
        if need(st, st + n):
            clip = decode_native(s, t, n)
            for lf in range(n):
                if want is None or st + lf in want:
                    yield st + lf, clip_frame(clip[lf], lf, n, cam, o)
    for f in range(b(14), TOTAL):
        if want is None or f in want:
            yield f, end_card(f)


def main():
    out = Path(sys.argv[1])
    Path(sys.argv[2]).write_text(json.dumps({"fps": FPS, "total": TOTAL, "cues": CUES}, indent=1))
    if "--frames" in sys.argv:
        idx = [int(x) for x in sys.argv[sys.argv.index("--frames") + 1].split(",")]
        out.mkdir(parents=True, exist_ok=True)
        for f, fr in frames_iter(idx):
            Image.fromarray(fr).save(out / f"f{f:04d}.jpg", quality=90)
        return
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "14",
                            "-pix_fmt", "yuv420p", str(out)], stdin=subprocess.PIPE)
    expect = 0
    for f, fr in frames_iter():
        assert f == expect, (f, expect)
        enc.stdin.write(np.ascontiguousarray(fr).tobytes())
        expect += 1
        if f % 100 == 0:
            print("frame", f, flush=True)
    enc.stdin.close()
    enc.wait()
    assert expect == TOTAL, expect
    print("done", expect, "frames")


if __name__ == "__main__":
    main()
