#!/usr/bin/env python3
"""Version 3 renderer: landscape 1440x1014 like the reference reel; shots, text and timing rebuilt from it.

Vertical sources (1440x2560) are framed by a camera that puts a chosen source point at a chosen output point.
usage: render3.py OUT.mp4 [--from T --to T] [--stills DIR --every S] [--crf N]
"""
import argparse, math, os, subprocess, sys, time
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
WORK = os.environ.get("REEL_WORK", os.path.join(ROOT, "work"))
os.environ.setdefault("REEL_FONTS", os.path.join(WORK, "fonts"))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "tools"))
import fx
from fx import clamp, ease_out, ease_in_out, ease_back
from seg import Segmenter

W, H, FPS = 1440, 1014, 30          # output (reference aspect 1020x718)
SW, SH = 1440, 2560                 # vertical source size
fx.W, fx.H = W, H
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
fx._vig_base = np.clip(np.sqrt(((_xx - W / 2) / (W * 0.62)) ** 2 + ((_yy - H / 2) / (H * 0.72)) ** 2), 0, 1.4) ** 2.2
AI_DIR = os.path.join(WORK, "ai")

BLUE = (46, 92, 255); BLUE_GLOW = (60, 140, 255)
CYAN = (110, 205, 255); CYAN_GLOW = (30, 150, 255)
CACHE = {}


def src_path(name):
    p14 = os.path.join(WORK, "proxy14", name + ".mp4")
    return p14 if os.path.exists(p14) else os.path.join(WORK, "proxy", name + ".mp4")


class Clip:
    def __init__(self, src, sin, speed, nframes):
        vf = f"setpts=PTS/{speed},fps={FPS},scale={SW}:{SH}:flags=lanczos,format=rgb24"
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{max(0, sin):.3f}", "-i", src_path(src), "-vf", vf,
                                   "-frames:v", str(nframes + 2), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                                  stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=SW * SH * 3 * 2)
        self.last = np.zeros((SH, SW, 3), np.uint8)

    def next(self):
        b = self.p.stdout.read(SW * SH * 3)
        if len(b) == SW * SH * 3:
            self.last = np.frombuffer(b, np.uint8).reshape(SH, SW, 3).copy()
        return self.last

    def close(self):
        try: self.p.stdout.close(); self.p.kill()
        except Exception: pass


# ================================================================ text
STYLES = {
    "W": dict(fname="anton", fill=(246, 246, 250)),
    "B": dict(fname="anton", fill=BLUE, glow=BLUE_GLOW),
    "BP": dict(fname="anton", fill=BLUE, shadow=False),
    "C": dict(fname="anton", fill=CYAN, glow=CYAN_GLOW),
    "BI": dict(fname="monti", fill=BLUE, glow=BLUE_GLOW),
    "WI": dict(fname="monti", fill=(246, 246, 250)),
    "P": dict(fname="anton", fill=(92, 80, 235), shadow=False),
    "S": dict(fname="mont8", fill=(246, 246, 250)),
}


def glyph(ch, style, size, extrude=0):
    k = ("g", ch, style, size, extrude)
    if k not in CACHE:
        CACHE[k] = fx.text_layer(ch, size=size, extrude=extrude, pad=40, **STYLES[style])
    return CACHE[k]


def word_layer(s, style, size, extrude=0, tracking=0):
    k = ("w", s, style, size, extrude, tracking)
    if k not in CACHE:
        CACHE[k] = fx.text_layer(s, size=size, extrude=extrude, tracking=tracking, **STYLES[style])
    return CACHE[k]


def letters_canvas(s, style, size, t, t0, stagger, extrude=0, tracking=0):
    f = fx.font(STYLES[style]["fname"], size)
    adv = [f.getlength(c) + tracking for c in s]
    pad = 40 + extrude
    asc, desc = f.getmetrics()
    cw = int(sum(adv) + pad * 2 + 40); chh = int(asc + desc + pad * 2 + 40)
    canvas = np.zeros((chh, cw, 4), np.uint8)
    x = pad + 20
    for i, c in enumerate(s):
        ti = t0 + i * stagger
        if c != " " and t >= ti:
            p = clamp((t - ti) / 0.2)
            g = glyph(c, style, size, extrude)
            gg = fx.transform_rgba(g, 1.8 - 0.8 * ease_out(p))
            gx = int(x + adv[i] / 2 - gg.shape[1] / 2)
            gy = int(chh / 2 - gg.shape[0] / 2 - 0.25 * size * (1 - ease_out(p)))
            a = clamp((t - ti) / 0.08)
            if a < 1:
                gg = gg.copy(); gg[..., 3] = (gg[..., 3] * a).astype(np.uint8)
            fx.over_rgba(canvas, gg, gx, gy)
        x += adv[i]
    return canvas


def lw(s, t0, t, size, style="W", extrude=0, stagger=0.04, tracking=0):
    if t - t0 > len(s) * stagger + 0.25:
        return word_layer(s, style, size, extrude, tracking)
    return letters_canvas(s, style, size, t, t0, stagger, extrude, tracking)


def T(t0, s, style="W", size=160, x=720, y=507, anim="pop", t1=None, behind=False, world=False, rot=0.0, persp=None,
      extrude=0, tracking=0, stagger=0.04, out=None, alpha=1.0, drift=0.02):
    return dict(kind="text", t0=t0, t1=t1, s=s, style=style, size=size, x=x, y=y, anim=anim, behind=behind, world=world,
                rot=rot, persp=persp, extrude=extrude, tracking=tracking, stagger=stagger, out=out, alpha=alpha, drift=drift)


def draw_text(frame, it, t, seg_t1, ctx):
    t1 = it["t1"] if it["t1"] is not None else seg_t1
    if t < it["t0"] or t >= t1:
        return
    dt = t - it["t0"]
    a, sc, dx, dy = it["alpha"], 1.0, 0.0, 0.0
    if it["anim"] == "letters":
        lay = lw(it["s"], it["t0"], t, it["size"], it["style"], it["extrude"], it["stagger"], it["tracking"])
    else:
        lay = word_layer(it["s"], it["style"], it["size"], it["extrude"], it["tracking"])
        if it["anim"] == "pop":
            p = clamp(dt / 0.2); sc = 1.35 - 0.35 * ease_back(p); a *= clamp(dt / 0.07)
        elif it["anim"] == "slam":
            p = clamp(dt / 0.16); sc = 2.0 - 1.0 * ease_out(p); a *= clamp(dt / 0.05)
        elif it["anim"] == "left":
            p = clamp(dt / 0.25); dx = -220 * (1 - ease_out(p)); a *= clamp(dt / 0.12)
        elif it["anim"] == "right":
            p = clamp(dt / 0.25); dx = 220 * (1 - ease_out(p)); a *= clamp(dt / 0.12)
        elif it["anim"] == "fade":
            a *= clamp(dt / 0.2)
    if it["persp"]:
        k = ("p", id(lay)) if it["anim"] == "letters" else ("p", it["s"], it["style"], it["size"], it["extrude"], it["persp"])
        if it["anim"] == "letters" and lay is not word_layer(it["s"], it["style"], it["size"], it["extrude"], it["tracking"]):
            lay = fx.perspective(lay, *it["persp"])
        else:
            if k not in CACHE:
                CACHE[k] = fx.perspective(lay, *it["persp"])
            lay = CACHE[k]
    x, y = it["x"], it["y"]
    if it["world"]:  # position given in source pixels: follow the camera
        M = ctx["M"]
        x = M[0, 0] * it["x"] + M[0, 1] * it["y"] + M[0, 2]
        y = M[1, 0] * it["x"] + M[1, 1] * it["y"] + M[1, 2]
        sc *= ctx["z"] / ctx["z0"]
    sc *= 1.0 + it["drift"] * dt
    if it["out"] == "down" and t1 - t < 0.3:
        dy += 500 * ease_in_out(1 - (t1 - t) / 0.3)
    elif t1 - t < 0.05:
        a *= clamp((t1 - t) / 0.05)
    fx.place_center(frame, lay, x + dx, y + dy, a, sc, it["rot"])


# ================================================================ graphics
def C(name, behind=False, **kw):
    return dict(kind="custom", name=name, behind=behind, world=False, kw=kw)


def _bubble(rng, scale, avatar=False):
    w = int(rng.integers(130, 220) * scale); h = int(42 * scale)
    color = (88, 200, 120, 245) if avatar else [(255, 255, 255, 235), (88, 200, 120, 240), (70, 140, 255, 240)][int(rng.integers(0, 3))]
    pad = 14; ax = int(54 * scale) if avatar else 0
    img = Image.new("RGBA", (w + pad * 2 + ax, h + pad * 2), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    x0 = pad + ax
    d.rounded_rectangle([x0, pad, x0 + w, pad + h], int(11 * scale), fill=color)
    if avatar:
        r = int(20 * scale); cy = pad + h // 2
        d.ellipse([pad, cy - r, pad + 2 * r, cy + r], fill=tuple(int(c) for c in rng.integers(120, 230, 3)) + (255,), outline=(255, 255, 255, 255), width=3)
    line = (60, 70, 90, 200) if color[0] > 200 else (255, 255, 255, 220)
    d.rounded_rectangle([x0 + 10 * scale, pad + 10 * scale, x0 + w * 0.8, pad + 17 * scale], 4, fill=line)
    d.rounded_rectangle([x0 + 10 * scale, pad + 24 * scale, x0 + w * 0.55, pad + 31 * scale], 4, fill=line)
    return np.array(img)


def g_burst(frame, t, seg, ctx, ox=900, oy=600, t0=0.55, n=72):
    """Chat bubbles bursting out of the laptop (positions follow the camera)."""
    k = ("burst", n)
    if k not in CACHE:
        rng = np.random.default_rng(9)
        CACHE[k] = [dict(img=fx.motion_blur(_bubble(rng, rng.uniform(0.8, 1.3)), 3, 0), ang=rng.uniform(-math.pi, math.pi),
                         dist=rng.uniform(200, 900), delay=rng.uniform(0, 0.8), drift=rng.uniform(10, 30), rot=rng.uniform(-12, 12))
                    for _ in range(n)]
    M, zr = ctx["M"], ctx["z"] / ctx["z0"]
    for b in CACHE[k]:
        dt = t - t0 - b["delay"]
        if dt < 0:
            continue
        p = ease_out(clamp(dt / 0.45))
        sx = ox + math.cos(b["ang"]) * b["dist"] * p * 1.4; sy = oy + math.sin(b["ang"]) * b["dist"] * p * 0.75 - b["drift"] * dt
        x = M[0, 0] * sx + M[0, 1] * sy + M[0, 2]; y = M[1, 0] * sx + M[1, 1] * sy + M[1, 2]
        fx.place_center(frame, b["img"], x, y, clamp(dt / 0.1) * 0.95, (0.4 + 0.6 * p) * zr * 0.8, b["rot"])


def g_dm_bubbles(frame, t, seg, ctx, t0=28.6):
    if "dmb" not in CACHE:
        rng = np.random.default_rng(21)
        spots = [(150, 240), (1290, 230), (130, 470), (1300, 470), (170, 700), (1280, 700), (400, 860), (1060, 860), (250, 120)]
        CACHE["dmb"] = [dict(img=_bubble(rng, 1.25, avatar=True), x=x, y=y, d=i * 0.07) for i, (x, y) in enumerate(spots)]
    for b in CACHE["dmb"]:
        dt = t - t0 - b["d"]
        if dt < 0:
            continue
        fx.place_center(frame, b["img"], b["x"], b["y"] - 12 * dt, clamp(dt / 0.1), 0.5 + 0.5 * ease_back(clamp(dt / 0.25)))


def _icon(kind, size=110):
    k = ("icon", kind, size)
    if k in CACHE:
        return CACHE[k]
    im = Image.new("RGBA", (size + 40, size + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    o = 20; s = size
    if kind == "heart":
        d.rounded_rectangle([o, o, o + s, o + s], int(s * .24), fill=(255, 70, 110, 255))
        cx, cy, r = o + s / 2, o + s / 2, s * 0.17
        d.ellipse([cx - 2 * r, cy - 1.6 * r, cx, cy + 0.4 * r], fill="white"); d.ellipse([cx, cy - 1.6 * r, cx + 2 * r, cy + 0.4 * r], fill="white")
        d.polygon([(cx - 1.95 * r, cy - 0.3 * r), (cx + 1.95 * r, cy - 0.3 * r), (cx, cy + 1.9 * r)], fill="white")
    elif kind == "chat":
        d.rounded_rectangle([o, o, o + s, o + s], int(s * .24), fill=(70, 130, 255, 255))
        d.rounded_rectangle([o + s * .2, o + s * .25, o + s * .8, o + s * .65], int(s * .1), fill="white")
        d.polygon([(o + s * .3, o + s * .62), (o + s * .3, o + s * .8), (o + s * .45, o + s * .62)], fill="white")
    elif kind == "plane":
        d.rounded_rectangle([o, o, o + s, o + s], int(s * .24), fill=(150, 90, 255, 255))
        d.polygon([(o + s * .2, o + s * .5), (o + s * .82, o + s * .22), (o + s * .6, o + s * .8), (o + s * .48, o + s * .56)], fill="white")
    elif kind == "user":
        d.rounded_rectangle([o, o, o + s, o + s], int(s * .24), fill=(255, 170, 60, 255))
        d.ellipse([o + s * .36, o + s * .2, o + s * .64, o + s * .48], fill="white")
        d.pieslice([o + s * .22, o + s * .5, o + s * .78, o + s * 1.0], 180, 360, fill="white")
    elif kind == "clapper":
        d.rounded_rectangle([o, o + s * .3, o + s, o + s], int(s * .1), fill=(70, 100, 245, 255))
        d.polygon([(o, o + s * .3), (o + s * .05, o + s * .05), (o + s, o + s * .05), (o + s, o + s * .3)], fill=(235, 240, 255, 255))
        for i in range(4):
            x = o + s * (0.1 + i * 0.22)
            d.polygon([(x, o + s * .28), (x + s * .1, o + s * .08), (x + s * .18, o + s * .08), (x + s * .08, o + s * .28)], fill=(40, 60, 200, 255))
        d.rounded_rectangle([o + s * .12, o + s * .45, o + s * .88, o + s * .55], 6, fill=(200, 215, 255, 255))
        d.rounded_rectangle([o + s * .12, o + s * .65, o + s * .6, o + s * .75], 6, fill=(200, 215, 255, 255))
    elif kind == "scissors":
        d.ellipse([o, o + s * .55, o + s * .4, o + s * .95], outline="white", width=max(4, s // 12))
        d.ellipse([o + s * .6, o + s * .55, o + s, o + s * .95], outline="white", width=max(4, s // 12))
        d.line([(o + s * .3, o + s * .62), (o + s * .85, o)], fill="white", width=max(5, s // 10))
        d.line([(o + s * .7, o + s * .62), (o + s * .15, o)], fill="white", width=max(5, s // 10))
    arr = np.array(im)
    sh = cv2.GaussianBlur(arr[..., 3].astype(np.float32), (0, 0), 6)
    base = np.zeros_like(arr); base[..., 3] = (sh * 0.5).astype(np.uint8)
    fx.over_rgba(base, arr, 0, 4)
    CACHE[k] = base
    return base


def g_screen_icons(frame, t, seg, ctx, t0=5.5, ox=1100, oy=380):
    rng = np.random.default_rng(4)
    for i, kd in enumerate(["heart", "chat", "plane", "user", "heart", "chat", "heart", "plane", "user", "heart", "chat", "heart"]):
        d0 = t - t0 - i * 0.05
        if d0 < 0:
            continue
        ang = rng.uniform(-math.pi, math.pi); dist = rng.uniform(80, 300)
        p = ease_out(clamp(d0 / 0.4))
        fx.place_center(frame, _icon(kd, 70), ox + math.cos(ang) * dist * p * 1.3, oy + math.sin(ang) * dist * p * 0.6, clamp(d0 / 0.08), 0.3 + 0.7 * p, rng.uniform(-15, 15))


def g_icon_pop(frame, t, seg, ctx, kind="clapper", t0=8.8, x=1150, y=300, size=200, spin=True):
    if t < t0:
        return
    dt = t - t0
    rot = (1 - ease_out(clamp(dt / 0.4))) * 200 if spin else 0
    fx.place_center(frame, _icon(kind, size), x, y + 8 * math.sin(dt * 4), clamp(dt / 0.08), 0.3 + 0.7 * ease_back(clamp(dt / 0.35)), rot - 10)


def _cube_obj():
    if "cube" in CACHE:
        return CACHE["cube"]
    im = Image.new("RGBA", (420, 420), (0, 0, 0, 0)); d = ImageDraw.Draw(im)

    def cube(cx, cy, s, top, left, right):
        d.polygon([(cx, cy - s), (cx + s * .87, cy - s * .5), (cx, cy), (cx - s * .87, cy - s * .5)], fill=top)
        d.polygon([(cx - s * .87, cy - s * .5), (cx, cy), (cx, cy + s), (cx - s * .87, cy + s * .5)], fill=left)
        d.polygon([(cx + s * .87, cy - s * .5), (cx, cy), (cx, cy + s), (cx + s * .87, cy + s * .5)], fill=right)
    for (cx, cy) in [(210, 150), (150, 235), (270, 235), (210, 300)]:
        cube(cx, cy, 70, (250, 190, 140, 255), (70, 110, 230, 255), (40, 70, 190, 255))
    CACHE["cube"] = np.array(im.filter(ImageFilter.GaussianBlur(0.6)))
    return CACHE["cube"]


def g_niche(frame, t, seg, ctx):
    items = [("1) AI VFX", "EDITS", "01_ai_robot_head.png", 10.66), ("2) REAL ESTATE", "", "02_luxury_villa_pool.png", 11.00),
             ("3) EVENT", "EDITS", "03_art_gallery_event.png", 11.33), ("4) AUTOMOBILE", "EDITS", "04_red_sports_car.png", 11.66),
             ("5) MOTION", "GRAPHICS", None, 12.00)]
    for i, (a, b, png, ts) in enumerate(items):
        te = items[i + 1][3] if i + 1 < len(items) else 12.30
        if not (ts <= t < te):
            continue
        dt = t - ts
        k = ("obj", i)
        if k not in CACHE:
            if png:
                im = Image.open(os.path.join(AI_DIR, png)).convert("RGBA"); im.thumbnail((330, 330)); CACHE[k] = np.array(im)
            else:
                CACHE[k] = fx.transform_rgba(_cube_obj(), 0.8)
        fx.place_center(frame, CACHE[k], 700, 470 - 20 * dt, clamp(dt / 0.06), 0.55 + 0.45 * ease_back(clamp(dt / 0.22)))
        fx.place_center(frame, word_layer(a, "W", 120), 820, 760, clamp(dt / 0.05), 1.0, 38)
        if b:
            fx.place_center(frame, word_layer(b, "W", 80), 990, 745, clamp(dt / 0.05), 1.0, 38)


def g_holo(frame, t, seg, ctx, t0=14.55):
    if t < t0:
        return
    dt = t - t0
    if "holo" not in CACHE:
        w, h = 1110, 640
        im = Image.new("RGBA", (w + 80, h + 80), (0, 0, 0, 0)); d = ImageDraw.Draw(im); o = 40
        d.rounded_rectangle([o, o, o + w, o + h], 50, fill=(130, 190, 255, 34))
        for gx in range(o + 60, o + w, 60): d.line([(gx, o + 10), (gx, o + h - 10)], fill=(170, 220, 255, 36), width=1)
        for gy in range(o + 60, o + h, 60): d.line([(o + 10, gy), (o + w - 10, gy)], fill=(170, 220, 255, 36), width=1)
        c = (190, 235, 255, 255); L = 150
        for (x, y, sx, sy) in [(o, o, 1, 1), (o + w, o, -1, 1), (o, o + h, 1, -1), (o + w, o + h, -1, -1)]:
            d.line([(x, y + sy * L), (x, y + sy * 40), (x + sx * 40, y), (x + sx * L, y)], fill=c, width=8, joint="curve")
        gx0, gy0, gx1, gy1 = o + 120, o + 70, o + w - 220, o + h - 110
        d.line([(gx0, gy0), (gx1, gy0)], fill=(90, 255, 120, 220), width=4); d.line([(gx0, gy1), (gx1, gy1)], fill=(90, 255, 120, 220), width=4)
        d.line([(gx0, gy0), (gx0, gy1)], fill=(90, 255, 120, 220), width=4); d.line([(gx1, gy0), (gx1, gy1)], fill=(90, 255, 120, 220), width=4)
        for (x, y) in [(gx0, gy0), (gx1, gy0), (gx0, gy1), (gx1, gy1)]:
            d.rectangle([x - 14, y - 14, x + 14, y + 14], fill=(90, 255, 120, 255))
        CACHE["holo"] = np.array(Image.alpha_composite(im.filter(ImageFilter.GaussianBlur(14)), im))
        tb = Image.new("RGBA", (760, 110), (0, 0, 0, 0)); d = ImageDraw.Draw(tb)
        d.rounded_rectangle([10, 10, 750, 100], 30, fill=(18, 24, 44, 230), outline=(110, 150, 255, 255), width=3)
        d.rounded_rectangle([30, 26, 90, 84], 14, fill=(60, 110, 255, 255))
        for i in range(9): x = 130 + i * 68; d.ellipse([x, 42, x + 26, 68], outline=(200, 215, 255, 255), width=4)
        CACHE["holo_tb"] = np.array(tb)
        sm = Image.new("RGBA", (330, 230), (0, 0, 0, 0)); d = ImageDraw.Draw(sm)
        d.rounded_rectangle([10, 10, 320, 220], 22, fill=(18, 24, 44, 230), outline=(110, 150, 255, 200), width=3)
        for i, s in enumerate(["Social Media", "Thumbnail", "UI Design"]):
            d.rounded_rectangle([30, 34 + i * 62, 60, 64 + i * 62], 6, outline=(200, 215, 255, 255), width=3)
            d.text((76, 34 + i * 62), s, font=fx.font("inter", 28), fill=(225, 232, 255, 255))
        CACHE["holo_sm"] = np.array(sm)
        ec = Image.new("RGBA", (330, 150), (0, 0, 0, 0)); d = ImageDraw.Draw(ec)
        d.rounded_rectangle([10, 10, 320, 140], 22, fill=(18, 24, 44, 230), outline=(110, 150, 255, 200), width=3)
        d.text((34, 30), "2025 Edition", font=fx.font("mont8", 28), fill="white"); d.ellipse([250, 70, 300, 120], fill=(70, 130, 255, 255))
        CACHE["holo_ec"] = np.array(ec)
    fx.place_center(frame, CACHE["holo"], 738, 497, clamp(dt / 0.1), 0.5 + 0.5 * ease_back(clamp(dt / 0.3)))
    if t >= 14.74: fx.place_center(frame, lw("PORT", 14.74, t, 260, extrude=6), 640, 360)
    if t >= 14.95: fx.place_center(frame, lw("FOLIO", 14.95, t, 260, extrude=6), 700, 590)
    if t >= 14.9:
        d2 = t - 14.9; q = ease_out(clamp(d2 / 0.25))
        fx.place_center(frame, CACHE["holo_tb"], 760, 904 + 200 * (1 - q), clamp(d2 / 0.1))
        fx.place_center(frame, CACHE["holo_sm"], 1160 + 200 * (1 - q), 230, clamp(d2 / 0.1))
        fx.place_center(frame, CACHE["holo_ec"], 360 - 200 * (1 - q), 730, clamp(d2 / 0.1))


def g_light_streaks(frame, t, seg, ctx, t0=14.2, t1=14.75, pts=((560, 820), (900, 860), (760, 700))):
    if not (t0 <= t < t1):
        return
    k = 1 - abs((t - t0) / (t1 - t0) - 0.5) * 2
    lay = np.zeros((H, W, 4), np.uint8)
    for i in range(len(pts) - 1):
        cv2.line(lay, pts[i], pts[i + 1], (150, 220, 255, int(255 * k)), 6, cv2.LINE_AA)
    for p in pts:
        cv2.circle(lay, p, 16, (220, 245, 255, int(255 * k)), -1, cv2.LINE_AA)
    glow = cv2.GaussianBlur(lay, (0, 0), 14); fx.over_rgba(glow, lay, 0, 0); fx.over(frame, glow, 0, 0)


def _thumbs():
    if "thumbs" not in CACHE:
        out = []
        for src, tt in [("AI_06a_film", 1.0), ("IMG_4962", 15.0), ("AI_hp_work", 4.0), ("IMG_4966", 9.0), ("AI_13_talk", 2.0),
                        ("AI_kb_edit", 5.0), ("IMG_4967", 8.0), ("AI_06b_phone", 2.0)]:
            cap = cv2.VideoCapture(src_path(src)); cap.set(cv2.CAP_PROP_POS_MSEC, tt * 1000); ok, fr = cap.read(); cap.release()
            fr = cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)
            th = cv2.resize(fr, (180, 320), interpolation=cv2.INTER_AREA)
            card = Image.new("RGBA", (204, 344), (0, 0, 0, 0))
            m = Image.new("L", (180, 320), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, 180, 320], 18, fill=255)
            card.paste(Image.fromarray(th), (12, 12), m)
            ImageDraw.Draw(card).rounded_rectangle([12, 12, 192, 332], 18, outline=(255, 255, 255, 255), width=5)
            out.append(np.array(card))
        CACHE["thumbs"] = out
    return CACHE["thumbs"]


def _glass_folder():
    if "gfolder" in CACHE:
        return CACHE["gfolder"]
    w, h = 460, 330
    im = Image.new("RGBA", (w + 80, h + 80), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([40, 70, 40 + w, 40 + h], 28, fill=(150, 170, 255, 120), outline=(210, 220, 255, 230), width=4)
    d.rounded_rectangle([40, 40, 220, 105], 20, fill=(150, 170, 255, 120))
    base = np.array(im)
    for i, c in enumerate(_thumbs()[:3]):
        fx.over_rgba(base, fx.transform_rgba(c, 0.6, (i - 1) * -9), 100 + i * 110, 50)
    front = Image.new("RGBA", base.shape[1::-1], (0, 0, 0, 0))
    ImageDraw.Draw(front).rounded_rectangle([40, 190, 40 + w, 40 + h], 28, fill=(170, 190, 255, 150), outline=(230, 236, 255, 230), width=4)
    fx.over_rgba(base, np.array(front), 0, 0)
    glow = cv2.GaussianBlur(base, (0, 0), 12); fx.over_rgba(glow, base, 0, 0)
    CACHE["gfolder"] = fx.perspective(glow, 0.12, "right")
    return CACHE["gfolder"]


def g_folder_fly(frame, t, seg, ctx, t0=16.15, x1=1110, y1=450):
    if t < t0:
        return
    dt = t - t0; p = ease_out(clamp(dt / 0.55))
    lay = _glass_folder()
    if p < 0.9:
        lay = fx.motion_blur(lay, 4 + 30 * (1 - p), 0)
    fx.place_center(frame, lay, 1700 + (x1 - 1700) * p, y1 + 120 * (1 - p) + 10 * math.sin(dt * 3), clamp(dt / 0.1), 0.6 + 0.4 * p, -6 * (1 - p))


def g_board(frame, t, seg, ctx):
    """Portfolio board on a light background (reference 22.5-26.1)."""
    t0 = seg["t0"]; dt = t - t0
    if "pf_bg" not in CACHE:
        bg = np.zeros((H, W, 3), np.float32)
        top, bot = np.array([246, 246, 252], np.float32), np.array([230, 232, 246], np.float32)
        for y in range(H): bg[y] = top + (bot - top) * (y / H)
        CACHE["pf_bg"] = bg.astype(np.uint8)
        fb = Image.new("RGBA", (560, 420), (0, 0, 0, 0)); d = ImageDraw.Draw(fb)
        d.rounded_rectangle([20, 50, 540, 400], 34, fill=(178, 168, 246, 255)); d.rounded_rectangle([20, 20, 230, 100], 26, fill=(178, 168, 246, 255))
        CACHE["pf_back"] = np.array(fb)
        ff = Image.new("RGBA", (600, 320), (0, 0, 0, 0))
        ImageDraw.Draw(ff).rounded_rectangle([20, 20, 580, 300], 34, fill=(202, 194, 252, 236), outline=(255, 255, 255, 220), width=4)
        CACHE["pf_front"] = np.array(ff)
        lab = Image.fromarray(fx.rounded_panel(330, 170, 20, (255, 255, 255, 246))); d = ImageDraw.Draw(lab)
        d.text((60, 58), "Video Editor & VFX Artist:", font=fx.font("mont8", 20), fill=(30, 34, 60, 255))
        d.text((60, 88), "\"5 signs you need a", font=fx.font("inter", 19), fill=(70, 76, 110, 255))
        d.text((60, 112), "reboot\" club content, etc.", font=fx.font("inter", 19), fill=(70, 76, 110, 255))
        d.rounded_rectangle([60, 150, 330, 178], 14, outline=(180, 186, 210, 255), width=3)
        CACHE["pf_label"] = np.array(lab)
        for nm, col in (("Ae", (40, 20, 90)), ("Pr", (30, 10, 70))):
            ic = Image.new("RGBA", (150, 150), (0, 0, 0, 0)); d = ImageDraw.Draw(ic)
            d.rounded_rectangle([8, 8, 142, 142], 30, fill=col + (255,), outline=(150, 140, 255, 255), width=5)
            d.text((34, 32), nm, font=fx.font("mont", 62), fill=(170, 160, 255, 255))
            CACHE["pf_" + nm] = np.array(ic)
        for nm in ("content creator", "social media"):
            f = fx.font("inter", 22); tw = f.getlength(nm)
            pl = Image.new("RGBA", (int(tw + 50), 50), (0, 0, 0, 0)); d = ImageDraw.Draw(pl)
            d.rounded_rectangle([3, 3, tw + 47, 47], 22, fill=(255, 255, 255, 240), outline=(120, 130, 220, 255), width=3)
            d.text((25, 11), nm, font=f, fill=(60, 70, 160, 255))
            CACHE["pf_pill_" + nm] = np.array(pl)
        st = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
        ImageDraw.Draw(st).polygon([(100, 0), (122, 78), (200, 100), (122, 122), (100, 200), (78, 122), (0, 100), (78, 78)], fill=(90, 120, 240, 255))
        CACHE["pf_star"] = np.array(st)
    frame[:] = fx.zoom(CACHE["pf_bg"], 1.0 + 0.03 * dt / 3.5)
    close = ease_in_out(clamp((t - 24.45) / 0.5)); flat = ease_in_out(clamp((t - 25.2) / 0.5))
    fxc, fyc = 690, 640 + 60 * close
    fx.place_center(frame, CACHE["pf_star"], 420, fyc + 120, 1.0, 0.7)
    fx.place_center(frame, CACHE["pf_star"], 1000, fyc + 230, 0.9, 0.35, 10)
    fx.place_center(frame, CACHE["pf_back"], fxc, fyc, 1.0, 1.0 - 0.15 * flat)
    for i, c in enumerate(_thumbs()[:6]):
        d0 = dt - 0.1 - i * 0.08
        if d0 < 0:
            continue
        p = ease_back(clamp(d0 / 0.4)) * (1 - close)
        fx.place_center(frame, c, fxc + (i - 2.5) * 80 * p, fyc + 10 - 250 * p + abs(i - 2.5) * 22 * p, 1.0, 0.85, -(i - 2.5) * 12 * p)
    for nm, x, yy in (("Ae", fxc - 110, fyc - 60), ("Pr", fxc + 160, fyc - 120)):
        d0 = dt - 0.5
        if d0 > 0:
            p = ease_back(clamp(d0 / 0.35)) * (1 - close)
            fx.place_center(frame, CACHE["pf_" + nm], x, yy - 40 * p, clamp(d0 / 0.1), 0.6 + 0.3 * p, (x - fxc) * -0.05)
    front = CACHE["pf_front"]
    if flat > 0:
        front = cv2.resize(front, (front.shape[1], max(10, int(front.shape[0] * (1 - 0.45 * flat)))))
    fx.place_center(frame, front, fxc, fyc + 90)
    if dt > 0.6:
        fx.place_center(frame, CACHE["pf_label"], 950, fyc + 140, clamp((dt - 0.6) / 0.15) * (1 - 0.6 * close), 1.0)
    hdr = 1 - clamp((t - 24.2) / 0.3)
    if hdr > 0:
        fx.place_center(frame, word_layer("PORT", "BP", 130), 530, 126, hdr * clamp(dt / 0.15))
        fx.place_center(frame, word_layer("folio", "BI", 110), 720, 140, hdr * clamp((dt - 0.1) / 0.15))
        fx.place_center(frame, CACHE["pf_pill_content creator"], 396, 223, hdr * clamp((dt - 0.3) / 0.15))
        fx.place_center(frame, CACHE["pf_pill_social media"], 1008, 180, hdr * clamp((dt - 0.35) / 0.15))
    if t >= 24.22:
        fx.place_center(frame, lw("PROFESSIONAL", 24.22, t, 230, "P"), 720, 216)
    if t >= 24.48:
        fx.place_center(frame, lw("PORTFOLIO", 24.48, t, 230, "W"), 520, 792)
    if t >= 25.26:
        fx.place_center(frame, word_layer("WEBSITE", "W", 110), 1134, 821, clamp((t - 25.26) / 0.1))
    blur = clamp(1 - dt / 0.25)
    if blur > 0:
        frame[:] = cv2.GaussianBlur(frame, (0, 0), 1 + 25 * blur)


def g_drive(frame, t, seg, ctx):
    g_board(frame, 25.95, {"t0": 22.50}, ctx)
    frame[:] = (cv2.GaussianBlur(frame, (0, 0), 2).astype(np.float32) * 0.3).astype(np.uint8)
    if t >= 26.10:
        fx.place_center(frame, word_layer("DON'T JUST USE", "W", 150), 720, 306, clamp((t - 26.1) / 0.08), 1.25 - 0.25 * ease_back(clamp((t - 26.1) / 0.2)))
    if t >= 26.52:
        fx.place_center(frame, lw("GOOGLE DRIVE", 26.52, t, 270, "C"), 720, 504)
    if t >= 26.75:
        if "drive" not in CACHE:
            im = Image.new("RGBA", (340, 320), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
            d.polygon([(170, 20), (320, 280), (20, 280)], fill=(255, 196, 40, 255)); d.polygon([(170, 20), (95, 150), (245, 150)], fill=(30, 160, 90, 255))
            d.polygon([(20, 280), (95, 150), (170, 280)], fill=(40, 120, 240, 255))
            d.ellipse([70, 60, 270, 260], outline=(255, 50, 70, 255), width=22); d.line([(102, 228), (238, 92)], fill=(255, 50, 70, 255), width=22)
            arr = np.array(im); glow = cv2.GaussianBlur(arr, (0, 0), 14); fx.over_rgba(glow, arr, 0, 0); CACHE["drive"] = glow
        d3 = t - 26.75
        fx.place_center(frame, CACHE["drive"], 1116, 702, clamp(d3 / 0.08), 0.4 + 0.6 * ease_back(clamp(d3 / 0.3)), -12)


def g_laptop(frame, t, seg, ctx, cx=760, cy=470):
    """Floating laptop (lid seen from behind) for the outreach shot."""
    if "laptop" not in CACHE:
        w, h = 560, 360
        im = Image.new("RGBA", (w + 120, h + 120), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        lid = np.zeros((h, w, 3), np.float32)
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        lid[:] = (150 + 50 * (1 - yy / h) + 20 * np.sin(xx / w * 3.1))[..., None] * np.array([1.0, 1.0, 1.04])
        m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], 26, fill=255)
        im.paste(Image.fromarray(np.clip(lid, 0, 255).astype(np.uint8)), (60, 50), m)
        d.rounded_rectangle([60, 50, 60 + w, 50 + h], 26, outline=(235, 238, 245, 255), width=3)
        d.ellipse([60 + w / 2 - 34, 50 + h / 2 - 34, 60 + w / 2 + 34, 50 + h / 2 + 34], fill=(60, 64, 72, 255))
        d.rounded_rectangle([40, 50 + h, 80 + w, 50 + h + 22], 10, fill=(110, 114, 124, 255))
        arr = np.array(im); sh = np.zeros_like(arr); sh[..., 3] = (cv2.GaussianBlur(arr[..., 3].astype(np.float32), (0, 0), 18) * 0.5).astype(np.uint8)
        fx.over_rgba(sh, arr, 0, 0)
        CACHE["laptop"] = fx.perspective(sh, 0.1, "left")
    dt = t - seg["t0"]
    p = ease_out(clamp(dt / 0.5))
    fx.place_center(frame, CACHE["laptop"], cx, cy + 40 * (1 - p) + 12 * math.sin(dt * 2.5), clamp(dt / 0.15), 0.85 + 0.15 * p, -4 + 3 * math.sin(dt * 1.7))


def g_rings(frame, t, seg, ctx, cx=760, cy=470):
    dt = t - seg["t0"]
    fx.place_center(frame, fx.glow_ring(1200, 700, phase=dt * 5.0, rng=np.random.default_rng(int(dt * 30))), cx, cy, clamp(dt / 0.12))


def g_search(frame, t, seg, ctx, t0=31.86):
    items = ["Real Estate Companies", "Influencers / creators", "Small businesses / start ups", "Filmmakers / agencies"]
    ys = [324, 490, 670, 842]; x0 = 170
    if t < t0:
        return
    fx.place_center(frame, word_layer("SEARCH ON IG :", "W", 120), 432, 155, clamp((t - t0) / 0.1))
    n = sum(1 for i in range(4) if t >= t0 + 0.08 + i * 0.07)
    if n:
        cv2.line(frame, (x0, ys[0] - 40), (x0, ys[n - 1] + 40), (225, 232, 255), 4, cv2.LINE_AA)
    for i, s in enumerate(items):
        ts = t0 + 0.08 + i * 0.07
        if t < ts:
            continue
        k = ("pill", s)
        if k not in CACHE:
            f = fx.font("inter", 40); tw = f.getlength(s)
            im = Image.fromarray(fx.rounded_panel(int(max(tw + 60, 460)), 80, 10, (64, 84, 225, 235), outline=(150, 170, 255, 255), width=3))
            ImageDraw.Draw(im).text((40 + 30, 40 + 16), s, font=f, fill=(255, 255, 255, 255))
            CACHE[k] = np.array(im)
        p = clamp((t - ts) / 0.2)
        fx.place_center(frame, CACHE[k], 400 - 220 * (1 - ease_out(p)), ys[i], clamp((t - ts) / 0.1))
        cv2.circle(frame, (x0, ys[i]), 12, (255, 255, 255), -1, cv2.LINE_AA)
    ti = 33.15
    if t >= ti:
        dt = t - ti
        if "ig" not in CACHE:
            n = 260; g = np.zeros((n, n, 4), np.float32)
            yy, xx = np.mgrid[0:n, 0:n].astype(np.float32) / n
            c1, c2, c3 = np.array([255, 205, 90]), np.array([245, 60, 130]), np.array([130, 70, 230])
            u = np.clip((xx * 0.4 + (1 - yy) * 0.6), 0, 1)[..., None]
            g[..., :3] = np.where(u < 0.5, c1 + (c2 - c1) * (u / 0.5), c2 + (c3 - c2) * ((u - 0.5) / 0.5))
            m = Image.new("L", (n, n), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, n - 1, n - 1], 70, fill=255); g[..., 3] = np.array(m)
            im = Image.fromarray(g.astype(np.uint8)); d = ImageDraw.Draw(im)
            d.rounded_rectangle([52, 52, n - 52, n - 52], 46, outline="white", width=18)
            d.ellipse([92, 92, n - 92, n - 92], outline="white", width=18); d.ellipse([n - 90, 66, n - 66, 90], fill="white")
            arr = np.array(im); glow = cv2.GaussianBlur(arr, (0, 0), 16); fx.over_rgba(glow, arr, 0, 0); CACHE["ig"] = glow
        if dt < 0.7:
            k = 1 - dt / 0.7
            for j in range(7):
                ang = j * 0.9 + 0.3; r = 120 + 280 * ease_out(clamp(dt / 0.5))
                cx, cy = int(760 + math.cos(ang) * r), int(300 + math.sin(ang) * r * 0.7)
                blob = np.zeros((150, 150, 4), np.uint8)
                cv2.ellipse(blob, (75, 75), (int(64 * k) + 5, int(36 * k) + 4), j * 30, 0, 360, (90, 150, 255, int(220 * k)), -1, cv2.LINE_AA)
                fx.over(frame, blob, cx - 75, cy - 75)
        fx.place_center(frame, CACHE["ig"], 760, 300 + 10 * math.sin(dt * 4), clamp(dt / 0.08), 0.3 + 0.7 * ease_back(clamp(dt / 0.35)), 8)


def g_envelope(frame, t, seg, ctx, t0=35.6, x=162, y=335):
    if t < t0:
        return
    if "env" not in CACHE:
        im = Image.new("RGBA", (260, 210), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([10, 30, 250, 200], 20, fill=(80, 165, 255, 255)); d.polygon([(14, 40), (130, 125), (246, 40)], fill=(170, 220, 255, 255))
        d.line([(14, 40), (130, 125), (246, 40)], fill="white", width=7)
        arr = np.array(im); glow = cv2.GaussianBlur(arr, (0, 0), 10); fx.over_rgba(glow, arr, 0, 0); CACHE["env"] = glow
    dt = t - t0; p = ease_back(clamp(dt / 0.35))
    fx.place_center(frame, CACHE["env"], x - 300 * (1 - p), y + 10 * math.sin(dt * 3), clamp(dt / 0.1), 0.5 + 0.5 * p, -12)


def g_brackets(frame, t, seg, ctx, t0=36.42, box=(486, 209, 1332, 569)):
    if t < t0:
        return
    x0, y0, x1, y1 = box; a = clamp((t - t0) / 0.15); col = (80, 220, 255, int(255 * a)); L = 50
    lay = np.zeros((H, W, 4), np.uint8)
    for (x, y, sx, sy) in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
        cv2.line(lay, (x, y), (x + sx * L, y), col, 6, cv2.LINE_AA); cv2.line(lay, (x, y), (x, y + sy * L), col, 6, cv2.LINE_AA)
    fx.over(frame, lay, 0, 0)


BARS = None


def g_bars(frame, t, seg, ctx):
    global BARS
    if BARS is None:
        rng = np.random.default_rng(3)
        cols = [(150, 80, 255), (60, 200, 140), (70, 140, 255), (255, 90, 170), (255, 170, 60), (90, 220, 255)]
        BARS = [dict(img=fx.motion_blur(fx.timeline_bar(int(rng.uniform(240, 640)), int(rng.uniform(36, 66)), cols[i % 6]), 11, 0),
                     y=rng.uniform(30, 980), speed=rng.uniform(1300, 2600), x0=rng.uniform(0, 3000), a=rng.uniform(0.6, 0.95)) for i in range(34)]
    dt = t - seg["t0"]
    for b in BARS:
        fx.over(frame, b["img"], int(1900 + b["x0"] - (dt * b["speed"]) % 3400 - 900), int(b["y"]), b["a"] * clamp(dt / 0.15))


def g_confetti(frame, t, seg, ctx, t0=47.5):
    if t < t0:
        return
    rng = np.random.default_rng(12); dt = t - t0
    cols = [(255, 90, 120), (255, 210, 70), (80, 200, 255), (120, 230, 140), (190, 120, 255)]
    for i in range(80):
        ang = rng.uniform(-math.pi * 0.95, -math.pi * 0.05); sp = rng.uniform(500, 1300)
        x = 720 + math.cos(ang) * sp * dt * 1.3; y = 900 + math.sin(ang) * sp * dt + 900 * dt * dt
        s = int(rng.uniform(10, 22))
        cv2.rectangle(frame, (int(x), int(y)), (int(x + s), int(y + s * 0.5)), cols[i % 5], -1)


def g_profile(frame, t, seg, ctx, t0=49.95):
    if t < t0:
        return
    if "profile" not in CACHE:
        w, h = 380, 640
        im = Image.new("RGBA", (w + 60, h + 60), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([30, 30, 30 + w, 30 + h], 32, fill=(16, 24, 40, 200), outline=(120, 190, 255, 230), width=4)
        face = cv2.cvtColor(cv2.imread(os.path.join(WORK, "airef", "ref_face.jpg")), cv2.COLOR_BGR2RGB)[200:1200, 40:1040]
        face = cv2.resize(face, (110, 110), interpolation=cv2.INTER_AREA)
        m = Image.new("L", (110, 110), 0); ImageDraw.Draw(m).ellipse([0, 0, 109, 109], fill=255)
        im.paste(Image.fromarray(face), (54, 62), m); d.ellipse([50, 58, 168, 176], outline=(255, 120, 180, 255), width=4)
        d.text((185, 78), "velora.media", font=fx.font("mont8", 28), fill="white")
        for i, (n, lab) in enumerate([("128", "posts"), ("24.6K", "followers"), ("312", "following")]):
            d.text((185 + i * 70, 124), n, font=fx.font("mont8", 22), fill="white"); d.text((185 + i * 70, 152), lab, font=fx.font("inter", 15), fill=(170, 180, 200, 255))
        d.text((54, 196), "FILMMAKER | EDITOR | VFX", font=fx.font("mont8", 20), fill="white")
        d.text((54, 226), "Email or DM for business", font=fx.font("inter", 20), fill=(170, 190, 230, 255))
        d.rounded_rectangle([54, 264, 30 + w - 26, 306], 12, fill=(64, 120, 255, 255)); d.text((170, 272), "Follow", font=fx.font("mont8", 22), fill="white")
        th = _thumbs()
        for i in range(6):
            im.alpha_composite(Image.fromarray(th[i % len(th)]).resize((112, 190)), (46 + (i % 3) * 118, 324 + (i // 3) * 196))
        arr = np.array(im); glow = cv2.GaussianBlur(arr, (0, 0), 12); fx.over_rgba(glow, arr, 0, 0)
        CACHE["profile"] = fx.perspective(glow, 0.2, "left")
    dt = t - t0; p = ease_out(clamp(dt / 0.35))
    fx.place_center(frame, CACHE["profile"], 252 - 300 * (1 - p), 504, clamp(dt / 0.12), 1.0)


def g_cta(frame, t, seg, ctx, tb=58.15):
    """Closing selfie: background turns blue with a white stripe and the person is rebuilt smaller, head and shoulders."""
    if t < tb:
        return
    if "cta_bg" not in CACHE:
        u = (_xx / W * 0.6 + _yy / H * 0.4)
        c1, c2 = np.array([50, 120, 245]), np.array([100, 165, 255])
        bg = c1 + (c2 - c1) * u[..., None]
        band = np.abs((_yy + 0.55 * _xx) - 1100) < 70
        bg[band] = bg[band] * 0.12 + 255 * 0.88
        CACHE["cta_bg"] = bg.astype(np.uint8)
    a = ease_out(clamp((t - tb) / 0.35))
    src = ctx["src"]
    s = 1.0 - 0.42 * a
    fpx, fpy = 0.47 * SW, 0.36 * SH
    tx0, ty0 = 0.0, 500 - fpy                    # where the face sits before the change (camera at z=1)
    tx1, ty1 = 430 - fpx * 0.58, 400 - fpy * 0.58
    tx, ty = tx0 + (tx1 - tx0) * a, ty0 + (ty1 - ty0) * a
    M = np.float32([[s, 0, tx], [0, s, ty]])
    person = cv2.warpAffine(src, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
    valid = cv2.warpAffine(np.ones((SH, SW), np.float32), M, (W, H), flags=cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    person = fx.grade(person, "clean")
    m = cv2.GaussianBlur(ctx["segm"].person(person), (0, 0), 2.5)
    prev = CACHE.get("cta_mprev")
    m = m if prev is None else 0.6 * m + 0.4 * prev
    CACHE["cta_mprev"] = m
    valid = cv2.GaussianBlur(valid, (0, 0), 28) * (valid > 0)
    m = (np.clip((m - 0.35) / 0.3, 0, 1) * np.clip(valid * 1.6 - 0.3, 0, 1))[..., None]
    bg = fx.zoom(CACHE["cta_bg"], 1.0 + 0.02 * (t - tb)).astype(np.float32)
    comp = person.astype(np.float32) * m + bg * (1 - m)
    wipe = np.clip(((_xx * 0.7 - _yy) + 2400 * a - 1150) / 120, 0, 1)[..., None]
    frame[:] = np.clip(comp * wipe + frame.astype(np.float32) * (1 - wipe), 0, 255).astype(np.uint8)


def g_cta_cards(frame, t, seg, ctx):
    if t >= 58.30:
        if "cta_panel" not in CACHE:
            p = Image.new("RGBA", (700, 380), (0, 0, 0, 0)); d = ImageDraw.Draw(p)
            d.rounded_rectangle([20, 20, 680, 360], 26, fill=(90, 150, 255, 150), outline=(150, 210, 255, 220), width=3)
            for (x, y, sx, sy) in [(20, 20, 1, 1), (680, 20, -1, 1), (20, 360, 1, -1), (680, 360, -1, -1)]:
                d.line([(x, y + sy * 50), (x, y), (x + sx * 50, y)], fill=(120, 230, 255, 255), width=7)
            arr = np.array(p)
            fx.over_rgba(arr, word_layer("OUTREACH", "W", 165), 30, 0)
            fx.over_rgba(arr, word_layer("TEMPLATE", "W", 95), 240, 190)
            CACHE["cta_panel"] = arr
        dt = t - 58.30; q = ease_out(clamp(dt / 0.3))
        fx.place_center(frame, CACHE["cta_panel"], 1060 + 500 * (1 - q), 300, clamp(dt / 0.1))
    if t >= 60.80:
        if "cta_card" not in CACHE:
            p = Image.fromarray(fx.rounded_panel(330, 300, 26, (238, 236, 255, 252), outline=(110, 90, 255, 255), width=8)); d = ImageDraw.Draw(p)
            d.text((40 + 34, 40 + 30), "FOLLOW", font=fx.font("mont", 50), fill=(20, 18, 60, 255))
            d.text((40 + 34, 40 + 88), "& COMMENT", font=fx.font("mont", 50), fill=(20, 18, 60, 255))
            arr = np.array(p); fx.over_rgba(arr, word_layer("“CLIENTS”", "B", 100), 40 - 20, 40 + 130); CACHE["cta_card"] = arr
        dt = t - 60.80
        fx.place_center(frame, CACHE["cta_card"], 1060, 650, clamp(dt / 0.1), 0.4 + 0.6 * ease_back(clamp(dt / 0.3)), -5)
    if t >= 61.90:
        dt = t - 61.90
        fx.place_center(frame, word_layer("FOR THE LINK", "W", 80), 1070, 880, clamp(dt / 0.1), 1.2 - 0.2 * ease_back(clamp(dt / 0.2)))


CUSTOM = dict(burst=g_burst, dmb=g_dm_bubbles, icons=g_screen_icons, iconpop=g_icon_pop, niche=g_niche, holo=g_holo,
              streaks=g_light_streaks, folder=g_folder_fly, board=g_board, drive=g_drive, rings=g_rings, laptop=g_laptop, search=g_search,
              envelope=g_envelope, brackets=g_brackets, bars=g_bars, confetti=g_confetti, profile=g_profile, cta=g_cta, cta_cards=g_cta_cards)
PRE = ("board", "drive", "cta")


# ================================================================ shots
def S(t0, t1, src, sin, grade="warm", speed=1.0, f=(0.5, 0.5), at=(720, 507), z=(1.0, 1.06), pan=((0, 0), (0, 0)), rot=(0, 0),
      matte=False, items=(), bw_from=None, blur=0, darken=0.0, tint=None):
    """f: source focal point (fractions); at: where it lands in the output; z: zoom start/end; pan: extra output offset start/end."""
    return dict(t0=t0, t1=t1, src=src, sin=sin, grade=grade, speed=speed, f=f, at=at, z=z, pan=pan, rot=rot, matte=matte,
                items=list(items), bw_from=bw_from, blur=blur, darken=darken, tint=tint)


EDL = [
    S(0.00, 3.45, "IMG_4960", 5.0, "warm", f=(0.52, 0.38), at=(720, 470), z=(1.0, 1.55), matte=True),           # 0 R1 hook
    S(3.45, 6.33, "IMG_4962", 13.2, "neon", f=(0.45, 0.6), at=(800, 520), z=(1.2, 1.4), pan=((0, 0), (-60, 0))),  # 1 R2 desk
    S(6.33, 7.75, "IMG_4976", 0.5, "dark", f=(0.4, 0.4), z=(1.25, 1.4), blur=7, darken=0.5),                     # 2 R3
    S(7.75, 8.55, "IMG_4963", 3.69, "clean", f=(0.2, 0.25), at=(380, 420), z=(1.45, 1.5)),                        # 3 R4 step 1
    S(8.55, 9.40, "IMG_4965", 4.6, "clean", f=(0.3, 0.3), at=(760, 520), z=(1.4, 1.48), matte=True),             # 4 R5 niche
    S(9.40, 10.62, "IMG_4962", 23.2, "neon", f=(0.5, 0.58), z=(1.1, 1.18)),                                      # 5 R6 stop
    S(10.62, 13.68, "IMG_4969", 0.0, "cine", f=(0.55, 0.5), z=(1.15, 1.25), bw_from=11.95),                      # 6 R7 desk niches
    S(13.68, 14.20, "IMG_4972", 2.9, "clean", f=(0.62, 0.4), at=(760, 560), z=(1.35, 1.42), matte=True),         # 7 R8 step 2
    S(14.20, 15.72, "IMG_4974", 2.0, "cine", speed=0.5, f=(0.52, 0.47), at=(720, 520), z=(1.0, 1.06)),           # 8 R9 holo
    S(15.72, 17.80, "IMG_4977", 0.0, "warm", f=(0.45, 0.48), z=(1.0, 1.12)),                                     # 9 R10 laptop
    S(17.80, 18.62, "AI_06a_film", 0.6, "warm", f=(0.48, 0.34), at=(720, 470), z=(1.0, 1.04), matte=True),       # 10 R11 shoot
    S(18.62, 19.28, "AI_06b_phone", 0.6, "warm", f=(0.41, 0.45), at=(560, 520), z=(1.35, 1.45)),                 # 11 R12 or use
    S(19.28, 20.66, "AI_kb_edit", 0.0, "neon", f=(0.38, 0.42), at=(520, 470), z=(1.0, 1.05), matte=True),         # 12 R13 internet
    S(20.66, 22.50, "IMG_4966", 7.5, "neon", f=(0.45, 0.5), at=(700, 560), z=(1.15, 1.25), matte=True),          # 13 R14 best work
    S(22.50, 26.05, None, 0, "clean"),                                                                           # 14 R15 board
    S(26.05, 27.45, None, 0, "clean"),                                                                           # 15 R16 drive
    S(27.45, 28.25, "IMG_4978", 2.9, "clean", f=(0.5, 0.33), at=(430, 470), z=(1.45, 1.5), matte=True),          # 16 R17 step 3
    S(28.25, 30.15, "IMG_4964", 0.5, "warm", f=(0.5, 0.33), at=(720, 507), z=(1.0, 1.08)),                        # 17 R18 outreach
    S(30.15, 31.82, "AI_kb_edit", 3.05, "warm", speed=0.6, f=(0.5, 0.55), at=(720, 507), z=(1.05, 1.15)),                      # 18 R19 DMs
    S(31.82, 34.62, "IMG_4980", 5.6, "clean", speed=1.16, f=(0.5, 0.38), at=(1000, 470), z=(1.4, 1.45)),         # 19 R20 search
    S(34.62, 38.55, "IMG_4982", 3.0, "clean", f=(0.5, 0.34), at=(430, 520), z=(1.35, 1.7)),                      # 20 R21 template
    S(38.55, 39.25, "IMG_4965", 0.4, "clean", f=(0.5, 0.35), z=(1.1, 1.2)),                                      # 21 R22 step 4
    S(39.25, 43.15, "AI_13_talk", 0.3, "neon", f=(0.5, 0.42), at=(620, 480), z=(1.15, 1.3), pan=((0, 0), (-80, 0)), matte=True),  # 22 R23
    S(43.15, 45.40, "IMG_4968", 4.3, "warm", f=(0.45, 0.6), at=(470, 560), z=(1.25, 1.38)),                      # 23 R24 best edit
    S(45.40, 48.15, "AI_kb_edit", 3.4, "neon", f=(0.5, 0.47), at=(950, 520), z=(1.4, 1.5), matte=True),          # 24 R25 happy client
    S(48.15, 49.85, "AI_16_hand", 3.45, "warm", f=(0.55, 0.52), at=(600, 540), z=(1.2, 1.3), matte=True),        # 25 R26 step 5
    S(49.85, 51.30, "IMG_4960", 9.0, "dark", f=(0.5, 0.34), at=(600, 480), z=(1.3, 1.38), matte=True, tint=(0.85, 1.0, 1.18)),  # 26 R27
    S(51.30, 51.70, "IMG_4977", 1.0, "warm", f=(0.35, 0.35), z=(1.5, 1.6)),                                      # 27 R28a
    S(51.70, 52.10, "IMG_4976", 3.0, "neon", f=(0.35, 0.35), z=(2.4, 2.6)),                                      # 28 R28b
    S(52.10, 52.85, "AI_18_eye", 0.6, "dark", f=(0.45, 0.36), at=(560, 470), z=(1.2, 1.26)),                      # 29 R29 eye
    S(52.85, 53.45, "IMG_4962", 16.0, "warm", f=(0.45, 0.6), z=(1.2, 1.26)),                                     # 30 R30
    S(53.45, 53.78, "AI_kb_edit", 3.1, "warm", f=(0.5, 0.5), z=(1.3, 1.5)),                                      # 31 R31
    S(53.78, 54.62, "IMG_4976", 1.5, "neon", f=(0.4, 0.4), z=(1.3, 1.4)),                                        # 32 R32
    S(54.62, 57.42, "AI_hp_work", 0.6, "clean", f=(0.52, 0.4), at=(520, 560), z=(1.0, 1.05), matte=True),         # 33 R33
    S(57.42, 63.15, "IMG_4985", 0.25, "clean", f=(0.47, 0.36), at=(720, 500), z=(1.0, 1.02), matte=False),        # 34 R34 CTA
]
TOTAL = EDL[-1]["t1"]


def add(i, *items):
    EDL[i]["items"].extend(items)


# hook text is placed in SOURCE pixels (world=True) so it rides the push-in like the reference
add(0, C("burst", behind=True, ox=960, oy=980, t0=0.55),
    T(0.34, "HOW TO", "W", 135, 344, 1258, anim="letters", world=True, rot=-6, stagger=0.07, extrude=6),
    T(0.84, "GET", "BI", 113, 952, 1222, world=True),
    T(1.04, "CLIENTS", "WI", 120, 821, 1055, world=True, rot=-5, persp=(0.2, "right")),
    T(1.38, "AS A", "W", 64, 582, 714, world=True, behind=True),
    T(1.88, "VIDEO EDITOR", "C", 160, 689, 829, world=True, behind=True, anim="slam"))
add(1, T(3.58, "THIS IS", "W", 110, 920, 120, anim="letters", persp=(0.18, "right"), rot=-4),
    T(4.10, "PROBABLY", "W", 180, 1050, 270, anim="letters", persp=(0.18, "right"), rot=-4, extrude=6),
    T(4.40, "THE MOST ASKED", "W", 100, 700, 800, persp=(0.4, "top"), rot=18),
    T(5.22, "QUESTION", "W", 240, 740, 930, persp=(0.4, "top"), rot=18, anim="slam", extrude=10),
    T(5.60, "ON THIS", "W", 78, 216, 205, anim="letters"),
    T(5.92, "PAGE", "W", 170, 270, 342, anim="slam"),
    C("icons", t0=5.55, ox=1060, oy=820))
add(2, T(6.33, "THE MOST ASKED QUESTION", "W", 100, 720, 930, anim="none", persp=(0.4, "top"), rot=14, alpha=0.3),
    T(6.50, "AND LET ME", "W", 145, 853, 353, anim="letters"),
    T(6.80, "BREAK IT DOWN", "C", 215, 720, 540, anim="slam"),
    T(7.30, "FOR YOU", "W", 145, 1037, 749, anim="letters"))
add(3, T(7.90, "STEP", "B", 265, 972, 504, anim="slam"), T(7.98, "1", "B", 360, 1296, 450, anim="slam"))
add(4, T(8.72, "PICK A", "W", 240, 380, 234, anim="letters"),
    T(8.92, "NICHE", "B", 510, 560, 684, behind=True, anim="slam"),
    C("iconpop", kind="clapper", t0=8.95, x=1152, y=306, size=200))
add(5, T(9.54, "STOP EDITING", "W", 240, 864, 317, anim="letters", extrude=8, stagger=0.035),
    T(9.98, "EVERYTHING", "W", 105, 828, 497, anim="letters", tracking=6))
add(6, C("niche"), T(12.30, "BE KNOWN", "W", 160, 650, 620, rot=35, anim="slam", extrude=8),
    T(12.72, "FOR ONE THING", "W", 70, 760, 700, rot=35, anim="letters"),
    C("iconpop", kind="scissors", t0=12.9, x=1116, y=605, size=110, spin=False))
add(7, T(13.74, "STEP", "B", 760, 702, 425, behind=True, anim="slam"),
    T(13.98, "2", "W", 560, 1188, 659, rot=-10, anim="slam", extrude=16))
add(8, C("streaks", t0=14.2, t1=14.7), C("holo", t0=14.55))
add(9, T(15.72, "CLIENTS", "W", 180, 470, 850, persp=(0.4, "top"), rot=-4, t1=16.95, extrude=8),
    T(15.80, "WITHOUT", "W", 180, 830, 830, persp=(0.4, "top"), rot=-4, t1=16.95, extrude=8),
    C("folder", t0=16.15, x1=1116, y1=454),
    T(16.40, "YOU CAN STILL", "W", 95, 396, 544, anim="letters"),
    T(16.98, "MAKE A", "W", 55, 720, 551),
    T(17.24, "PORTFOLIO", "C", 200, 468, 706, persp=(0.35, "top"), rot=-6, anim="letters"))
add(10, T(17.84, "SHOOT", "W", 290, 330, 260, behind=True, anim="slam", extrude=8),
     T(17.96, "YOUR OWN", "W", 70, 252, 508, anim="letters"),
     T(18.36, "FOOTAGE", "B", 240, 300, 724, behind=True, anim="slam"))
add(11, T(18.64, "OR", "W", 60, 432, 562), T(18.98, "USE", "W", 215, 600, 508, anim="slam"))
add(12, T(19.30, "FREE CLIPS FROM THE", "W", 105, 936, 202, anim="letters", rot=-4, stagger=0.03),
     T(20.30, "INTERNET", "W", 330, 1020, 400, behind=True, anim="slam", extrude=10))
add(13, T(21.06, "CREATE YOUR", "W", 105, 1134, 346, anim="letters"),
     T(21.58, "BEST WORK", "W", 360, 720, 562, behind=True, anim="slam", extrude=12))
add(14, C("board"))
add(15, C("drive"))
add(16, T(27.62, "STEP", "B", 265, 936, 504, anim="slam"), T(27.80, "3", "B", 360, 1278, 486, anim="slam"))
add(17, C("laptop", cx=760, cy=470), C("rings", cx=760, cy=470), T(28.30, "OUTREACH", "W", 340, 702, 216, anim="letters", extrude=10, stagger=0.045),
    C("dmb", t0=28.65), T(29.22, "SEND 20-30 DMs", "C", 75, 900, 440, anim="letters", stagger=0.03))
add(18, T(30.15, "DMs", "W", 125, 216, 353, anim="slam", extrude=6),
     T(30.54, "& EMAILS", "W", 135, 414, 479, anim="left", rot=-8, extrude=6),
     T(30.80, "EVERYDAY", "B", 155, 450, 623, anim="slam", rot=-10))
add(19, C("search", t0=31.86))
add(20, C("envelope", t0=35.6, x=162, y=335),
    T(35.08, "GET MY EXACT", "W", 75, 756, 173, anim="letters"),
    T(35.86, "OUTREACH", "W", 240, 900, 335, anim="letters", tracking=3),
    T(36.42, "TEMPLATE", "W", 120, 1062, 515),
    C("brackets", t0=36.42, box=(486, 209, 1332, 569)),
    T(37.20, "JUST FOLLOW & COMMENT", "W", 75, 954, 634, anim="letters", stagger=0.025),
    T(37.74, "“CLIENTS”", "C", 195, 954, 767, anim="letters"))
add(21, T(38.62, "STEP", "B", 760, 702, 425, anim="slam"), T(38.94, "4", "W", 560, 1188, 677, rot=-10, anim="slam", extrude=16))
add(22, C("bars", behind=True),
    T(39.48, "OVER DELIVER", "W", 230, 640, 190, behind=True, anim="letters", extrude=8),
    T(40.30, "BECAUSE THIS", "W", 220, 702, 857, out="down", t1=42.95, extrude=6),
    T(40.66, "IS YOUR", "W", 85, 360, 677, out="down", t1=42.95),
    T(40.96, "FIRST CLIENT", "B", 120, 820, 670, out="down", t1=42.95, anim="letters"),
    T(41.66, "BE RELIABLE", "W", 115, 300, 440, anim="letters"),
    T(42.58, "COMMUNICATE", "W", 110, 1116, 430, anim="letters"),
    T(42.98, "WELL", "W", 170, 1188, 570, anim="slam"))
add(23, T(43.62, "GIVE THE", "W", 90, 690, 240, rot=-8), T(44.00, "BEST", "W", 115, 715, 380, rot=-8),
    T(44.26, "EDIT", "W", 360, 1100, 310, anim="slam", extrude=14, rot=-8),
    T(44.52, "TO YOUR CLIENT", "W", 90, 1110, 560, anim="letters", rot=-8))
add(24, T(45.68, "ONE HAPPY", "W", 110, 306, 166, anim="letters", rot=-5),
    T(46.38, "CLIENT", "W", 340, 486, 418, anim="slam", extrude=14, rot=-5, persp=(0.15, "right"), t1=46.95),
    T(46.68, "CAN BRING IN", "W", 110, 576, 634, anim="letters"),
    T(47.52, "10 MORE", "W", 280, 720, 796, anim="slam", extrude=14, persp=(0.3, "top")),
    C("confetti", t0=47.5))
add(25, T(48.36, "STEP", "B", 265, 918, 300, anim="slam", t1=48.92), T(48.40, "5", "B", 360, 1250, 270, anim="slam", t1=48.92),
    T(48.94, "FINAL", "W", 265, 432, 252, anim="letters"),
    T(49.22, "STEP", "B", 760, 738, 594, behind=True, anim="slam"))
add(26, C("profile", behind=True, t0=49.95),
    T(49.88, "BUILD A", "W", 60, 1030, 144, anim="letters", behind=True),
    T(50.08, "PERSONAL", "W", 150, 1110, 236, anim="letters", behind=True, extrude=6),
    T(50.42, "BRAND", "W", 215, 1110, 380, anim="slam", behind=True, extrude=10),
    T(51.10, "YOU", "W", 120, 486, 864), T(51.16, "CAN", "W", 120, 666, 943))
add(27, T(51.10, "YOU", "W", 120, 486, 864, anim="none"), T(51.16, "CAN", "W", 120, 666, 943, anim="none"))
add(28, T(51.70, "YOU CAN POST:", "W", 120, 720, 800, anim="letters"))
POST = [T(51.70, "YOU CAN POST:", "W", 60, 1116, 198, anim="none"),
        T(51.58, "1) BEFORE &", "W", 160, 1044, 317, anim="letters"),
        T(52.20, "AFTER EDITS", "W", 105, 1134, 436, anim="letters")]
add(29, *POST)
B2 = [T(53.06, "2) BEHIND THE", "W", 130, 1044, 569, anim="letters"), T(53.20, "SCENES", "W", 130, 1170, 695, anim="letters")]
add(30, *[dict(p, anim="none") for p in POST], *B2)
add(31, *[dict(p, anim="none") for p in POST + B2])
add(32, *[dict(p, anim="none") for p in POST + B2], T(53.84, "3) EDIT BREAKDOWNS", "W", 105, 1044, 814, anim="letters", stagger=0.03))
add(33, T(55.02, "WHICH CAN GET YOU ALOT OF", "W", 55, 1110, 150, anim="letters", stagger=0.02, rot=15),
    T(56.16, "CLIENTS", "W", 230, 1110, 300, behind=False, anim="letters", extrude=10, rot=15),
    T(56.64, "IN THE LONG RUN", "W", 75, 1200, 440, anim="letters", rot=15))
add(34, C("cta"), C("cta_cards"))

FLASHES = [(6.31, 0.16), (26.03, 0.18), (34.60, 0.16), (40.12, 0.18), (22.46, 0.10)]


def camera(s, p, t):
    z = s["z"][0] + (s["z"][1] - s["z"][0]) * ease_in_out(p)
    (px0, py0), (px1, py1) = s["pan"]
    dx = px0 + (px1 - px0) * ease_in_out(p); dy = py0 + (py1 - py0) * ease_in_out(p)
    r = s["rot"][0] + (s["rot"][1] - s["rot"][0]) * ease_in_out(p)
    fxp, fyp = s["f"][0] * SW, s["f"][1] * SH
    M = cv2.getRotationMatrix2D((fxp, fyp), r, z)
    M[0, 2] += s["at"][0] + dx - fxp; M[1, 2] += s["at"][1] + dy - fyp
    # keep the window inside the source (no mirrored borders)
    M[0, 2] = min(0.0, max(W - z * SW, M[0, 2])); M[1, 2] = min(0.0, max(H - z * SH, M[1, 2]))
    return M, z


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out"); ap.add_argument("--from", dest="t_from", type=float, default=0.0)
    ap.add_argument("--to", dest="t_to", type=float, default=None)
    ap.add_argument("--stills", default=None); ap.add_argument("--every", type=float, default=0.5)
    ap.add_argument("--crf", default="17")
    a = ap.parse_args()
    t_to = a.t_to if a.t_to is not None else TOTAL
    segm = Segmenter(os.path.join(WORK, "models", "selfie_multiclass.tflite"))
    enc = None
    if a.stills:
        os.makedirs(a.stills, exist_ok=True)
    else:
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                                "-c:v", "libx264", "-preset", "medium", "-crf", a.crf, "-pix_fmt", "yuv420p", "-color_primaries", "bt709",
                                "-color_trc", "bt709", "-colorspace", "bt709", "-movflags", "+faststart", a.out], stdin=subprocess.PIPE)
    n0, n1 = int(round(a.t_from * FPS)), int(round(t_to * FPS))
    cur, clip, mema = -1, None, None
    t_start = time.time(); next_still = a.t_from
    for n in range(n0, n1):
        t = n / FPS
        i = next(k for k, s in enumerate(EDL) if s["t0"] <= t < s["t1"] or k == len(EDL) - 1)
        s = EDL[i]
        if i != cur:
            if clip: clip.close()
            cur, mema = i, None
            nf = int((s["t1"] - s["t0"]) * FPS) + 4
            clip = Clip(s["src"], s["sin"] + max(0.0, t - s["t0"]) * s["speed"], s["speed"], nf) if s["src"] else None
        lt = t - s["t0"]; dur = s["t1"] - s["t0"]; p = lt / max(dur, 1e-3)
        ctx = {"mask": None, "M": None, "z": 1.0, "z0": s["z"][0], "segm": segm, "src": None}
        if clip:
            M, z = camera(s, p, t)
            ctx["M"], ctx["z"] = M, z
            # extra shake on big slams
            for it in s["items"]:
                if it["kind"] == "text" and it["anim"] == "slam" and it["size"] >= 300 and 0 <= t - it["t0"] < 0.25:
                    amp = 14 * (1 - (t - it["t0"]) / 0.25)
                    M = M.copy(); M[0, 2] += amp * math.sin(n * 2.7); M[1, 2] += amp * math.cos(n * 3.1)
            ctx["src"] = clip.next()
            frame = cv2.warpAffine(ctx["src"], M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            g = "bw" if (s["bw_from"] and t >= s["bw_from"]) else s["grade"]
            frame = fx.grade(frame, g)
            if s["tint"]:
                frame = np.clip(frame.astype(np.float32) * np.array(s["tint"], np.float32), 0, 255).astype(np.uint8)
            if s["blur"]:
                frame = cv2.GaussianBlur(frame, (0, 0), s["blur"])
            if s["darken"]:
                frame = (frame.astype(np.float32) * (1 - s["darken"])).astype(np.uint8)
            if s["matte"]:
                m = cv2.GaussianBlur(segm.person(frame), (0, 0), 3)
                mema = m if mema is None else 0.55 * m + 0.45 * mema
                ctx["mask"] = np.clip((mema - 0.35) / 0.3, 0, 1).astype(np.float32)
        else:
            frame = np.zeros((H, W, 3), np.uint8)
        pre = [it for it in s["items"] if it["kind"] == "custom" and it["name"] in PRE]
        for it in pre:
            CUSTOM[it["name"]](frame, t, s, ctx, **it["kw"])
        behind = [it for it in s["items"] if it.get("behind") and it not in pre]
        if behind:
            base = frame.copy()
            for it in behind:
                draw_text(frame, it, t, s["t1"], ctx) if it["kind"] == "text" else CUSTOM[it["name"]](frame, t, s, ctx, **it["kw"])
            if ctx["mask"] is not None:
                m3 = ctx["mask"][..., None]; frame = (base * m3 + frame * (1 - m3)).astype(np.uint8)
        for it in s["items"]:
            if it in pre or it.get("behind"):
                continue
            draw_text(frame, it, t, s["t1"], ctx) if it["kind"] == "text" else CUSTOM[it["name"]](frame, t, s, ctx, **it["kw"])
        # transitions
        if i == 0 and dur - lt < 0.35:
            k = 1 - (dur - lt) / 0.35
            frame = fx.motion_blur(fx.zoom(frame, 1 + 0.25 * k, rot=-25 * k * k), 4 + 60 * k, -20)
        if i == 1 and lt < 0.15:
            k = 1 - lt / 0.15
            frame = fx.motion_blur(fx.zoom(frame, 1 + 0.2 * k, rot=12 * k), 4 + 50 * k, -20)
        if s["src"] == "AI_16_hand" and dur - lt < 0.3:
            k = 1 - (dur - lt) / 0.3
            frame = cv2.GaussianBlur(fx.zoom(frame, 1 + 0.6 * k), (0, 0), 1 + 18 * k)
        if i == 31:
            frame = fx.motion_blur(frame, 70, 0)
        for (tf, d) in FLASHES:
            if tf <= t < tf + d + 0.12:
                aa = 1.0 if t < tf + d else 1 - (t - tf - d) / 0.12
                frame = (frame.astype(np.float32) * (1 - aa) + 255 * aa).astype(np.uint8)
        frame = fx.grain(fx.sharpen(frame, 0.22), n, 4)
        if a.stills:
            if t + 1e-6 >= next_still:
                cv2.imwrite(os.path.join(a.stills, f"f_{t:06.2f}.jpg"), cv2.cvtColor(cv2.resize(frame, (480, 338), interpolation=cv2.INTER_AREA), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 88])
                next_still += a.every
        else:
            enc.stdin.write(frame.tobytes())
        if n % 90 == 0:
            print(f"t={t:6.2f}  {n - n0}/{n1 - n0}  {time.time() - t_start:6.1f}s", flush=True)
    if clip: clip.close()
    if enc: enc.stdin.close(); enc.wait()
    print("RENDER DONE", round(time.time() - t_start, 1))


if __name__ == "__main__":
    main()
