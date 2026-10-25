"""Render the Aminur showreel (video only) + write the SFX cue sheet.

usage: render.py OUT.mp4 CUES.json [--frames 0,230,700,...]  (frames -> PNG stills only)
Timeline: 30 fps, beat = 14 frames, bar = 56 frames, 1604 frames total.
"""
import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path("/tmp/claude-0/-home-user-velora-media/4a14988d-28db-5a70-b10e-dd2bb40ffc21/scratchpad")
FD = ROOT / "fonts"
FPS, W, H = 30, 1920, 1080
BEAT, BAR = 14, 56
TOTAL = 28 * BAR + 36

SRC = {
    1: ROOT / "dl/v1/5UxnBbskneaPT7WI.mp4",
    2: ROOT / "dl/v2/noor_motion_reel01_v2_16x9.mp4",
    3: ROOT / "dl/v3/CSGOGem_Promo_FINAL_4K.mp4",
    4: ROOT / "dl/v4/FortKnox_Loop_90s_share2.mp4",
    5: ROOT / "dl/v5/NanoSyllabus_Promo_4K_16x9.mp4",
    6: ROOT / "dl/v6/NeuralHive_Presale_Ad_Draft2_16x9.mp4",
}

LIME = (198, 245, 25)
INK = (12, 12, 10)
PAPER = (244, 245, 240)


def font(name, size):
    return ImageFont.truetype(str(FD / f"{name}.ttf"), size)


F_HERO = font("ArchivoExp-ExtraBold", 200)
F_TITLE = font("ArchivoExp-ExtraBold", 86)
F_END = font("ArchivoExp-ExtraBold", 124)
F_SUB = font("Archivo-Medium", 36)
F_MONO = font("PlexMono-Medium", 24)
F_MONO_S = font("PlexMono-Medium", 21)
F_MONO_L = font("PlexMono-Medium", 30)


def ease_out(p):
    p = min(max(p, 0.0), 1.0)
    return 1 - (1 - p) ** 3


def ease_in(p):
    p = min(max(p, 0.0), 1.0)
    return p ** 3


# ---------------------------------------------------------------- drawing

_text_cache = {}


def text_rgba(text, fnt, fill):
    key = (text, id(fnt), fill)
    if key in _text_cache:
        return _text_cache[key]
    asc, desc = fnt.getmetrics()
    w = int(np.ceil(fnt.getlength(text))) + 4
    im = Image.new("RGBA", (w, asc + desc), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((0, asc), text, font=fnt, fill=fill + (255,), anchor="ls")
    arr = np.asarray(im).astype(np.float32) / 255
    _text_cache[key] = arr
    return arr


def paste(frame, rgba, x, y, opacity=1.0, clip=None):
    """Alpha-composite float RGBA (0..1) onto uint8 frame in place."""
    h, w = rgba.shape[:2]
    x, y = int(round(x)), int(round(y))
    x0, y0, x1, y1 = x, y, x + w, y + h
    cx0, cy0, cx1, cy1 = 0, 0, W, H
    if clip:
        cx0, cy0, cx1, cy1 = clip
    ix0, iy0 = max(x0, cx0), max(y0, cy0)
    ix1, iy1 = min(x1, cx1), min(y1, cy1)
    if ix0 >= ix1 or iy0 >= iy1 or opacity <= 0:
        return
    src = rgba[iy0 - y:iy1 - y, ix0 - x:ix1 - x]
    a = src[..., 3:4] * opacity
    dst = frame[iy0:iy1, ix0:ix1].astype(np.float32)
    dst = dst * (1 - a) + src[..., :3] * 255 * a
    frame[iy0:iy1, ix0:ix1] = dst.astype(np.uint8)


def reveal_word(frame, rgba, x, y, f, f_on, dur=7, color_clip=True):
    """Mask slide-up reveal: the word rises into its own line box."""
    if f < f_on:
        return
    p = ease_out((f - f_on) / dur)
    h = rgba.shape[0]
    dy = (1 - p) * h * 0.95
    paste(frame, rgba, x, y + dy, 1.0, clip=(0, int(y), W, int(y + h)))


def rounded_mask(w, h, r):
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255)
    return np.asarray(m).astype(np.float32) / 255


def pill(text, fnt, fg, bg, bg_alpha, dot=None, pad=18, h=46):
    t = text_rgba(text, fnt, fg)
    dot_w = 22 if dot else 0
    w = t.shape[1] + pad * 2 + dot_w
    m = rounded_mask(w, h, h // 2)
    out = np.zeros((h, w, 4), np.float32)
    out[..., :3] = np.array(bg) / 255
    out[..., 3] = m * bg_alpha
    if dot:
        cy, cx = h // 2, pad + 6
        yy, xx = np.mgrid[0:h, 0:w]
        d = np.clip(6.5 - np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2), 0, 1)
        out[..., :3] = out[..., :3] * (1 - d[..., None]) + np.array(dot) / 255 * d[..., None]
        out[..., 3] = np.maximum(out[..., 3], d)
    ty = (h - t.shape[0]) // 2 + 1
    tx = pad + dot_w
    sub = out[ty:ty + t.shape[0], tx:tx + t.shape[1]]
    a = t[..., 3:4]
    sub[..., :3] = sub[..., :3] * (1 - a) + t[..., :3] * a
    sub[..., 3:4] = np.maximum(sub[..., 3:4], a)
    return out


# ---------------------------------------------------------------- footage

def decode(src, t, n):
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(SRC[src]), "-frames:v", str(n),
           "-vf", f"fps={FPS},scale={W}:{H}:flags=lanczos", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    k = len(raw) // (W * H * 3)
    arr = np.frombuffer(raw[: k * W * H * 3], np.uint8).reshape(k, H, W, 3)
    if k < n:
        arr = np.concatenate([arr, np.repeat(arr[-1:], n - k, 0)], 0)
    return arr


def transform(img, scale=1.0, dx=0.0, blur=0):
    if scale != 1.0 or dx:
        M = np.array([[scale, 0, (1 - scale) * W / 2 + dx], [0, scale, (1 - scale) * H / 2]], np.float32)
        img = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    if blur > 1:
        k = np.zeros((1, int(blur)), np.float32)
        k[:] = 1.0 / int(blur)
        img = cv2.filter2D(img, -1, k, borderType=cv2.BORDER_REFLECT)
    if not img.flags.writeable:
        img = img.copy()
    return img


def solid(color):
    f = np.empty((H, W, 3), np.uint8)
    f[:] = color
    return f


# ---------------------------------------------------------------- timeline

def b(n):
    return n * BAR


SHOTS = []  # (start, length, src, t, opts)


def shot(start, length, src, t, **o):
    SHOTS.append((start, length, src, t, o))


# build: bars 2-3
for k, (s, t) in enumerate([(4, 0.3), (1, 5.0), (5, 17.4), (6, 2.2)]):
    shot(b(2) + k * 28, 28, s, t, push=0.05, ramp_out=(k == 3))

# drop 1: bars 4-11
d1 = [(4, 6.0, 56, "OfflineIQ  ·  Product film"), (1, 17.0, 56, "Commas  ·  SaaS launch"),
      (5, 19.8, 56, "NanoSyllabus  ·  Ed-tech promo"), (6, 13.0, 56, "Neural Hive  ·  Launch ad"),
      (4, 22.0, 28, None), (4, 12.3, 28, None), (1, 12.0, 56, None),
      (2, 4.0, 56, "Noor Motion  ·  Studio reel"), (5, 39.2, 56, None)]
f = b(4)
for k, (s, t, n, label) in enumerate(d1):
    shot(f, n, s, t, push=0.06, label=label, punch=(k == 0), flash=(k == 0), mark=True)
    f += n
assert f == b(12)

# drop 2: bars 16-23
d2_half = [(6, 22.0), (4, 28.5), (1, 13.0), (5, 24.0), (4, 46.5), (6, 18.6),
           (1, 38.0), (4, 59.5), (5, 45.0), (2, 3.0), (4, 66.5), (1, 7.0)]
whips = {2, 5, 8, 10}
f = b(16)
for k, (s, t) in enumerate(d2_half):
    shot(f, 28, s, t, push=0.04, punch=(k == 0), flash=(k == 0), mark=True,
         whip_out=(k in whips), whip_in=(k - 1 in whips))
    f += 28
for s, t in [(6, 8.8), (5, 34.2), (4, 36.0), (1, 21.0), (6, 16.5), (5, 41.5), (4, 79.0), (1, 16.0)]:
    shot(f, 14, s, t, push=0.03, mark=True)
    f += 14
assert f == b(24)

SERVICES = [
    (("SaaS", "explainers"), 1, 25.0, "Commas  ·  Affiliate Center"),
    (("Product", "demos"), 1, 31.6, "Commas  ·  Dashboard walkthrough"),
    (("UI", "animation"), 5, 27.0, "NanoSyllabus  ·  Teacher view"),
    (("Launch", "films & ads"), 4, 81.5, "OfflineIQ  ·  Fort Knox"),
]

CUES = []  # (frame, sfx, gain)


def cue(fr, name, gain=1.0):
    CUES.append({"frame": int(fr), "sfx": name, "gain": gain})


# ---- sound cues tied to picture
cue(0, "pop1", 0.9); cue(14, "pop3", 0.8); cue(28, "pop2", 0.9)
cue(56, "whA", 1.0); cue(70, "click1", 0.9); cue(84, "pop1", 0.8)
for k in range(4):
    cue(b(2) + k * 28, "tick1" if k % 2 == 0 else "blip1", 0.7)
cue(b(4) - 40, "riser_med", 0.55)
cue(b(4), "whB", 1.15)
for st, n, s, t, o in SHOTS:
    if o.get("label"):
        cue(st + 3, "tick2", 0.55)
cue(b(8), "whC", 0.8)
for k in range(4):
    cue(b(12) + k * BAR, "click2" if k else "whE", 0.8 if k else 0.7)
    cue(b(12) + k * BAR + 7, "pop3", 0.6)
cue(b(16), "whD", 0.95)
for st, n, s, t, o in SHOTS:
    if o.get("whip_out"):
        cue(st + n - 2, "swoosh", 0.9)
for k in range(8):
    if k % 2 == 1:
        cue(b(23) + k * 14, "blip2", 0.5)
cue(b(24) - 67, "riser_big", 0.5)
cue(b(24), "whA", 1.1)
cue(b(24) + 14, "pop1", 0.7); cue(b(24) + 28, "pop2", 0.7)
cue(b(25), "tick1", 0.6); cue(b(26), "click2", 0.9)
cue(b(28), "pop3", 0.6)


# ---------------------------------------------------------------- static layers

PHOTO = Image.open(ROOT.parent / "images/1.webp").convert("RGB")
ph_h = H
ph_w = round(PHOTO.width * ph_h / PHOTO.height)
photo = np.asarray(PHOTO.resize((ph_w, ph_h), Image.LANCZOS)).astype(np.float32) / 255
ph_a = np.ones((ph_h, ph_w), np.float32)
ramp = 60
ph_a[:, :ramp] *= np.linspace(0, 1, ramp)[None, :]
ph_a[:ramp, :] *= np.linspace(0, 1, ramp)[:, None]
PHOTO_RGBA = np.dstack([photo, ph_a])
PHOTO_BG = tuple(int(v) for v in np.median(np.asarray(PHOTO)[:150, :300].reshape(-1, 3), 0))

MARK = pill("@aminur_rex", F_MONO_S, PAPER, INK, 0.55)

FRAME_W, FRAME_H, FRAME_X, FRAME_Y = 940, 529, 860, 250
FRAME_MASK = rounded_mask(FRAME_W, FRAME_H, 18)
_sh = Image.new("L", (FRAME_W + 160, FRAME_H + 160), 0)
ImageDraw.Draw(_sh).rounded_rectangle((80, 100, FRAME_W + 80, FRAME_H + 100), 18, fill=90)
SHADOW = np.asarray(_sh.filter(ImageFilter.GaussianBlur(28))).astype(np.float32) / 255
SHADOW_RGBA = np.dstack([np.zeros(SHADOW.shape + (3,), np.float32), SHADOW])


def corner_texts(frame, on_dark):
    col = PAPER if on_dark else INK
    a = 0.62 if on_dark else 0.72
    paste(frame, text_rgba("AMINUR RAHMAN — SHOWREEL 2026", F_MONO, col), 120, 84, a)
    paste(frame, text_rgba("EXPLAINERS · PRODUCT ANIMATION · VIDEO ADS", F_MONO, col), 120, H - 84 - 34, a)
    paste(frame, text_rgba("KOLKATA, IN", F_MONO, col), W - 120 - 175, 84, a)


# ---------------------------------------------------------------- frame builders

def cold_open(f):
    dark = f < BAR
    fr = solid(INK if dark else LIME)
    col = PAPER if dark else INK
    lines = (("Hard", "to"), ("explain?",)) if dark else (("Easy", "to"), ("watch.",))
    base = 0 if dark else BAR
    x0, y_top, lh = 120, 300, 228
    k = 0
    for li, words in enumerate(lines):
        x = x0
        for w in words:
            t = text_rgba(w, F_HERO, col)
            reveal_word(fr, t, x, y_top + li * lh, f, base + k * BEAT, dur=6)
            x += t.shape[1] + 36
            k += 1
    corner_texts(fr, dark)
    if not dark and f < BAR + 3:
        # impact flash into the lime card
        a = [1.0, 0.6, 0.25][f - BAR]
        fr = (fr.astype(np.float32) * (1 - a) + 255 * a).astype(np.uint8)
    return fr


def services_frame(f, clip_frames):
    k = (f - b(12)) // BAR
    lf = (f - b(12)) % BAR
    words, src, t, tag = SERVICES[k]
    fr = solid(LIME)
    paste(fr, text_rgba("WHAT WE MAKE", F_MONO, INK), 120, 286, 0.75)
    paste(fr, text_rgba(f"{k + 1:02d} / 04", F_MONO, INK), 120 + 230, 286, 0.45)
    for li, w in enumerate(words):
        tr = text_rgba(w, F_TITLE, INK)
        reveal_word(fr, tr, 120, 366 + li * 100, f, b(12) + k * BAR + li * 3, dur=7)
    clip = clip_frames[k][lf]
    # zoom-through on the last card
    zt = 0.0
    if k == 3 and lf >= BAR - 12:
        zt = ease_in((lf - (BAR - 12)) / 11)
    fx = FRAME_X * (1 - zt)
    fy = FRAME_Y * (1 - zt)
    fw = FRAME_W + (W - FRAME_W) * zt
    fh = FRAME_H + (H - FRAME_H) * zt
    if zt < 0.02:
        paste(fr, SHADOW_RGBA, FRAME_X - 80, FRAME_Y - 80, 1.0)
    small = cv2.resize(clip, (int(round(fw)), int(round(fh))), interpolation=cv2.INTER_AREA)
    m = rounded_mask(small.shape[1], small.shape[0], int(18 * (1 - zt)) + 1) if zt > 0 else FRAME_MASK
    rgba = np.dstack([small.astype(np.float32) / 255, m])
    paste(fr, rgba, fx, fy)
    if zt < 0.02:
        paste(fr, text_rgba(tag, F_MONO_S, INK), FRAME_X, FRAME_Y + FRAME_H + 22, 0.7)
    return fr


def end_frame(f):
    lf = f - b(24)
    fr = solid(PHOTO_BG)
    p = ease_out(lf / 14)
    paste(fr, PHOTO_RGBA, W - ph_w + 10, (1 - p) * 140, min(1, lf / 6))
    x = 120
    if lf >= 3:
        pa = ease_out((lf - 3) / 8)
        paste(fr, text_rgba("AMINUR RAHMAN — ANIMATION STUDIO, KOLKATA", F_MONO, INK), x - 20 * (1 - pa), 276, pa * 0.8)
    reveal_word(fr, text_rgba("Let's make", F_END, INK), x, 330, f, b(24) + BEAT, dur=7)
    reveal_word(fr, text_rgba("your video.", F_END, INK), x, 470, f, b(24) + 2 * BEAT, dur=7)
    if f >= b(25):
        pa = ease_out((f - b(25)) / 9)
        paste(fr, text_rgba("Explainers · Product demos · UI animation · Video ads", F_SUB, INK), x, 650 + 16 * (1 - pa), pa)
    if f >= b(26):
        pa = ease_out((f - b(26)) / 8)
        btn = pill("MESSAGE ME BEFORE YOU ORDER", F_MONO_L, LIME, INK, 1.0, pad=34, h=80)
        sc = 0.88 + 0.12 * pa
        bh, bw = btn.shape[:2]
        btn_s = cv2.resize(btn, (int(bw * sc), int(bh * sc)), interpolation=cv2.INTER_AREA)
        paste(fr, btn_s, x, 752 + (bh - btn_s.shape[0]) / 2, pa)
    paste(fr, text_rgba("@aminur_rex", F_MONO, INK), x, H - 84 - 34, 0.7)
    return fr


def clip_frame(img, lf, n, o):
    s = 1.0 + o.get("push", 0) * (lf / max(n - 1, 1))
    dx, blur = 0.0, 0
    if o.get("punch") and lf < 8:
        s *= 1.10 - 0.10 * ease_out(lf / 8)
    if o.get("ramp_out") and lf >= n - 14:
        q = ease_in((lf - (n - 14)) / 13)
        s *= 1 + 0.35 * q
    if o.get("whip_out") and lf >= n - 3:
        j = lf - (n - 3)
        dx, blur = -[0.10, 0.28, 0.55][j] * W, [40, 110, 190][j]
    if o.get("whip_in") and lf < 3:
        dx, blur = [0.42, 0.14, 0.03][lf] * W, [170, 80, 22][lf]
    out = transform(img, s, dx, blur)
    if o.get("ramp_out") and lf >= n - 6:
        out = cv2.GaussianBlur(out, (0, 0), 1 + (lf - (n - 6)) * 1.4)
    if o.get("mark"):
        paste(out, MARK, W - 64 - MARK.shape[1], H - 96 - MARK.shape[0], 1.0)
    if o.get("label") and lf >= 3:
        pa = ease_out((lf - 3) / 7)
        lab = pill(o["label"], F_MONO_S, PAPER, INK, 0.62, dot=LIME)
        paste(out, lab, 64 - 30 * (1 - pa), H - 96 - lab.shape[0], pa)
    if o.get("flash") and lf < 3:
        a = [1.0, 0.55, 0.2][lf]
        out = (out.astype(np.float32) * (1 - a) + np.array(LIME, np.float32) * a).astype(np.uint8)
    return out


# ---------------------------------------------------------------- driver

def frames_iter(only=None):
    want = set(only) if only is not None else None

    def need(lo, hi):
        return want is None or any(lo <= x < hi for x in want)

    # cold open
    for f in range(0, b(2)):
        if want is None or f in want:
            yield f, cold_open(f)
    # build + drop 1
    for st, n, s, t, o in [x for x in SHOTS if x[0] < b(12)]:
        if not need(st, st + n):
            continue
        clip = decode(s, t, n)
        for lf in range(n):
            if want is None or st + lf in want:
                yield st + lf, clip_frame(clip[lf], lf, n, o)
    # services
    if need(b(12), b(16)):
        clips = [decode(s, t, BAR) for _, s, t, _ in SERVICES]
        for f in range(b(12), b(16)):
            if want is None or f in want:
                yield f, services_frame(f, clips)
    # drop 2
    for st, n, s, t, o in [x for x in SHOTS if x[0] >= b(16)]:
        if not need(st, st + n):
            continue
        clip = decode(s, t, n)
        for lf in range(n):
            if want is None or st + lf in want:
                yield st + lf, clip_frame(clip[lf], lf, n, o)
    # end card
    for f in range(b(24), TOTAL):
        if want is None or f in want:
            yield f, end_frame(f)


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
        enc.stdin.write(fr.tobytes())
        expect += 1
        if f % 100 == 0:
            print("frame", f, flush=True)
    enc.stdin.close()
    enc.wait()
    assert expect == TOTAL, expect
    print("done", expect, "frames")


if __name__ == "__main__":
    main()
