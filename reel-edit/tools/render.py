#!/usr/bin/env python3
"""Reel renderer: EDL + kinetic text + graphics -> 1080x1920 30fps video (silent). Audio is mixed by audio.py.

usage: render.py OUT.mp4 [--from T] [--to T] [--stills DIR] [--preview]
"""
import argparse, json, math, os, subprocess, sys, time
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
WORK = os.environ.get("REEL_WORK", os.path.join(ROOT, "work"))
PROXY = os.path.join(WORK, "proxy")
os.environ.setdefault("REEL_FONTS", os.path.join(WORK, "fonts"))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "tools"))
import fx
from fx import W, H, FPS, BLUE, BLUE2, WHITE, ease_out, ease_back, ease_in_out, clamp
from seg import Segmenter

AI_DIR = os.path.join(WORK, "ai")  # AI clips dropped here later override placeholders


# =============================================================== clip reader
class Clip:
    def __init__(self, src, sin, speed=1.0, nframes=60):
        self.path = os.path.join(PROXY, src + ".mp4") if not os.path.isabs(src) else src
        vf = f"setpts=PTS/{speed},fps={FPS},scale={W}:{H}:flags=lanczos,format=rgb24"
        cmd = ["ffmpeg", "-v", "error", "-ss", f"{max(0, sin):.3f}", "-i", self.path, "-vf", vf,
               "-frames:v", str(nframes + 2), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
        self.p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=W * H * 3 * 4)
        self.last = np.zeros((H, W, 3), np.uint8)

    def next(self):
        buf = self.p.stdout.read(W * H * 3)
        if len(buf) == W * H * 3:
            self.last = np.frombuffer(buf, np.uint8).reshape(H, W, 3).copy()
        return self.last.copy()

    def close(self):
        try:
            self.p.stdout.close(); self.p.kill()
        except Exception:
            pass


# =============================================================== text items
_layer_cache = {}


def L(text, style="W", size=160, **kw):
    key = (text, style, size, tuple(sorted(kw.items())))
    if key in _layer_cache:
        return _layer_cache[key]
    if style == "W":
        lay = fx.text_layer(text, "anton", size, WHITE, **kw)
    elif style == "WG":  # white with blue glow
        lay = fx.text_layer(text, "anton", size, WHITE, glow=(70, 130, 255), **kw)
    elif style == "B":
        lay = fx.text_layer(text, "anton", size, BLUE, glow=BLUE2, **kw)
    elif style == "BI":
        lay = fx.text_layer(text, "monti", size, BLUE, glow=BLUE2, **kw)
    elif style == "WI":
        lay = fx.text_layer(text, "monti", size, WHITE, **kw)
    elif style == "D":  # dark text for light backgrounds
        lay = fx.text_layer(text, "anton", size, (24, 28, 48), shadow=False, **kw)
    elif style == "S":
        lay = fx.text_layer(text, "mont8", size, WHITE, **kw)
    elif style == "R":
        lay = fx.text_layer(text, "anton", size, WHITE, glow=(255, 60, 60), **kw)
    elif style == "G":
        lay = fx.text_layer(text, "anton", size, WHITE, glow=(255, 190, 80), **kw)
    else:
        raise ValueError(style)
    _layer_cache[key] = lay
    return lay


def text(t0, s, style="W", size=160, x=540, y=960, t1=None, anim="pop", behind=False, rot=0.0, persp=None, sfx="pop", **kw):
    return dict(kind="text", t0=t0, t1=t1, s=s, style=style, size=size, x=x, y=y, anim=anim, behind=behind, rot=rot,
                persp=persp, sfx=sfx, kw=kw)


def draw_text(frame, it, t, seg_t1):
    t1 = it["t1"] if it["t1"] is not None else seg_t1
    if t < it["t0"] or t >= t1:
        return
    lay = L(it["s"], it["style"], it["size"], **it["kw"])
    if it["persp"]:
        k = ("persp", it["s"], it["style"], it["size"], it["persp"])
        if k not in _layer_cache:
            _layer_cache[k] = fx.perspective(lay, *it["persp"])
        lay = _layer_cache[k]
    dt = t - it["t0"]
    a, sc, dx, dy = 1.0, 1.0, 0.0, 0.0
    if it["anim"] == "pop":
        p = clamp(dt / 0.2)
        sc = 1.35 - 0.35 * ease_back(p); a = clamp(dt / 0.07)
    elif it["anim"] == "slam":
        p = clamp(dt / 0.16)
        sc = 2.2 - 1.2 * ease_out(p); a = clamp(dt / 0.05)
    elif it["anim"] == "up":
        p = clamp(dt / 0.25); dy = 90 * (1 - ease_out(p)); a = clamp(dt / 0.12)
    elif it["anim"] == "left":
        p = clamp(dt / 0.25); dx = -160 * (1 - ease_out(p)); a = clamp(dt / 0.12)
    elif it["anim"] == "right":
        p = clamp(dt / 0.25); dx = 160 * (1 - ease_out(p)); a = clamp(dt / 0.12)
    elif it["anim"] == "fade":
        a = clamp(dt / 0.15)
    sc *= 1.0 + 0.025 * dt  # slow push while on screen
    # quick exit
    out = t1 - t
    if out < 0.06:
        a *= clamp(out / 0.06)
    fx.place_center(frame, lay, it["x"] + dx, it["y"] + dy, a, sc, it["rot"])


# =============================================================== custom graphics
_rng = np.random.default_rng(11)
BUBBLES = None


def g_bubbles(frame, t, seg, ctx):
    global BUBBLES
    if BUBBLES is None:
        rng = np.random.default_rng(5)
        BUBBLES = []
        spots = [(170, 300), (420, 220), (760, 260), (930, 420), (140, 560), (300, 470), (860, 640), (700, 450),
                 (150, 820), (930, 860), (240, 1060), (880, 1100), (380, 360), (620, 330), (980, 250), (90, 980)]
        for i, (x, y) in enumerate(spots):
            BUBBLES.append(dict(img=fx.chat_bubble(rng, scale=rng.uniform(0.8, 1.15)), x=x, y=y,
                                t0=seg["t0"] + 0.05 + i * 0.065, vy=rng.uniform(-30, -12), vx=rng.uniform(-8, 8)))
    for b in BUBBLES:
        if t < b["t0"]:
            continue
        dt = t - b["t0"]
        sc = 0.4 + 0.6 * ease_back(clamp(dt / 0.25))
        fx.place_center(frame, b["img"], b["x"] + b["vx"] * dt, b["y"] + b["vy"] * dt, clamp(dt / 0.1) * 0.95, sc)


def g_glass_panel(frame, t, seg, ctx):
    t0 = 14.36
    if t < t0:
        return
    dt = t - t0
    k = "glass"
    if k not in _layer_cache:
        w, h = 760, 520
        img = Image.new("RGBA", (w + 80, h + 80), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([40, 40, 40 + w, 40 + h], 34, fill=(120, 170, 255, 70), outline=(170, 210, 255, 230), width=5)
        for (cx, cy) in [(40, 40), (40 + w, 40), (40, 40 + h), (40 + w, 40 + h)]:
            d.rectangle([cx - 14, cy - 14, cx + 14, cy + 14], fill=(90, 255, 140, 255))
        d.rounded_rectangle([40 + 30, 40 + h - 70, 40 + w - 30, 40 + h - 25], 18, fill=(20, 30, 60, 170))
        for i in range(8):
            d.ellipse([40 + 60 + i * 80, 40 + h - 60, 40 + 84 + i * 80, 40 + h - 36], fill=(200, 220, 255, 220))
        glow = img.filter(ImageFilter.GaussianBlur(18))
        base = Image.alpha_composite(glow, img)
        arr = np.array(base)
        port = L("PORT", "W", 200); folio = L("FOLIO", "B", 200)
        fx.over_rgba(arr, port, 40 + w // 2 - port.shape[1] + 50, 40 + 70)
        fx.over_rgba(arr, folio, 40 + w // 2 - 30, 40 + 70)
        _layer_cache[k] = fx.perspective(arr, 0.12, "right")
    sc = 0.3 + 0.7 * ease_back(clamp(dt / 0.3))
    fx.place_center(frame, _layer_cache[k], 540, 1230 - 25 * math.sin(dt * 2), clamp(dt / 0.12), sc * 0.85, rot=-3)


def _thumbs():
    if "thumbs" not in _layer_cache:
        picks = [("IMG_4973", 3.4), ("IMG_4962", 15.0), ("IMG_4966", 9.0), ("IMG_4967", 8.0), ("IMG_4960", 8.0), ("IMG_4968", 5.0)]
        out = []
        for src, tt in picks:
            cap = cv2.VideoCapture(os.path.join(PROXY, src + ".mp4")); cap.set(cv2.CAP_PROP_POS_MSEC, tt * 1000)
            ok, fr = cap.read(); cap.release()
            fr = cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)
            fr = fx.grade(fr, "neon")
            th = cv2.resize(fr, (240, 426), interpolation=cv2.INTER_AREA)
            card = Image.new("RGBA", (240 + 24, 426 + 24), (0, 0, 0, 0))
            m = Image.new("L", (240, 426), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, 240, 426], 22, fill=255)
            card.paste(Image.fromarray(th), (12, 12), m)
            ImageDraw.Draw(card).rounded_rectangle([12, 12, 252, 438], 22, outline=(255, 255, 255, 255), width=6)
            sh = Image.new("RGBA", card.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([14, 20, 252, 444], 22, fill=(0, 0, 0, 120))
            card = Image.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)), card)
            out.append(np.array(card))
        _layer_cache["thumbs"] = out
    return _layer_cache["thumbs"]


def g_cards_fly(frame, t, seg, ctx):
    t0 = 17.2
    if t < t0:
        return
    th = _thumbs()[:3]
    for i, c in enumerate(th):
        dt = t - t0 - i * 0.08
        if dt < 0:
            continue
        p = ease_back(clamp(dt / 0.35))
        x = 540 + (i - 1) * 230 * p; y = 780 - 60 * p + abs(i - 1) * 40
        fx.place_center(frame, c, x, y, clamp(dt / 0.1), 0.55 + 0.25 * p, rot=(i - 1) * -12 * p)


def g_portfolio_page(frame, t, seg, ctx):
    """Scene 7: light 'portfolio' board with folder and cards, then the Google Drive warning."""
    dt = t - seg["t0"]
    if "pf_bg" not in _layer_cache:
        bg = np.zeros((H, W, 3), np.float32)
        top, bot = np.array([244, 245, 252], np.float32), np.array([214, 220, 248], np.float32)
        for y in range(H):
            bg[y] = top + (bot - top) * (y / H)
        _layer_cache["pf_bg"] = bg.astype(np.uint8)
        # folder back / front
        fb = Image.new("RGBA", (760, 560), (0, 0, 0, 0)); d = ImageDraw.Draw(fb)
        d.rounded_rectangle([20, 60, 740, 540], 40, fill=(186, 176, 246, 255))
        d.rounded_rectangle([20, 20, 300, 120], 30, fill=(186, 176, 246, 255))
        _layer_cache["pf_back"] = np.array(fb)
        ff = Image.new("RGBA", (800, 420), (0, 0, 0, 0)); d = ImageDraw.Draw(ff)
        d.rounded_rectangle([20, 20, 780, 400], 40, fill=(206, 198, 252, 236), outline=(255, 255, 255, 200), width=4)
        _layer_cache["pf_front"] = np.array(ff.filter(ImageFilter.GaussianBlur(0.5)))
        lab = fx.rounded_panel(430, 120, 24, (255, 255, 255, 245))
        im = Image.fromarray(lab); d = ImageDraw.Draw(im)
        d.text((70, 62), "Video Editor & VFX Artist", font=fx.font("mont8", 30), fill=(30, 34, 60, 255))
        d.text((70, 104), "Reels · YouTube · Ads", font=fx.font("inter", 26), fill=(90, 96, 130, 255))
        _layer_cache["pf_label"] = np.array(im)
    s = 1.0 + 0.05 * (dt / 5.0)
    bg = fx.zoom(_layer_cache["pf_bg"], s)
    frame[:] = bg
    # header
    fx.place_center(frame, L("PORT", "B", 230), 350, 330, clamp(dt / 0.15), 1.0)
    fx.place_center(frame, L("folio", "BI", 170), 700, 345, clamp((dt - 0.12) / 0.15), 1.0)
    # folder + cards
    fx.place_center(frame, _layer_cache["pf_back"], 540, 1000)
    cards = _thumbs()
    for i, c in enumerate(cards):
        d0 = dt - 0.25 - i * 0.11
        if d0 < 0:
            continue
        p = ease_back(clamp(d0 / 0.4))
        ang = (i - 2.5) * 11 * p
        x = 540 + (i - 2.5) * 105 * p; y = 1010 - 330 * p + abs(i - 2.5) * 30 * p
        fx.place_center(frame, c, x, y, 1.0, 0.85, rot=-ang)
    fx.place_center(frame, _layer_cache["pf_front"], 540, 1140)
    if dt > 1.2:
        fx.place_center(frame, _layer_cache["pf_label"], 740, 1250, clamp((dt - 1.2) / 0.15), 0.6 + 0.4 * ease_back(clamp((dt - 1.2) / 0.3)))
    # bottom lines
    if t >= 24.32:
        fx.place_center(frame, L("PROFESSIONAL", "B", 170), 540, 1500, clamp((t - 24.32) / 0.08), 1.3 - 0.3 * ease_back(clamp((t - 24.32) / 0.2)))
    if t >= 24.60:
        fx.place_center(frame, L("PORTFOLIO WEBSITE", "D", 120), 540, 1660, clamp((t - 24.6) / 0.1), 1.0, )
    # google drive warning
    if t >= 25.70:
        d2 = t - 25.70
        frame[:] = (frame.astype(np.float32) * (1 - 0.72 * clamp(d2 / 0.15))).astype(np.uint8)
        fx.place_center(frame, L("DON'T JUST USE", "W", 160), 540, 860, clamp(d2 / 0.08), 1.3 - 0.3 * ease_back(clamp(d2 / 0.2)))
        if t >= 26.60:
            d3 = t - 26.60
            fx.place_center(frame, L("GOOGLE DRIVE", "B", 180), 540, 1060, clamp(d3 / 0.08), 1.4 - 0.4 * ease_back(clamp(d3 / 0.2)))
            if "nosign" not in _layer_cache:
                im = Image.new("RGBA", (220, 220), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
                d.ellipse([12, 12, 208, 208], outline=(255, 64, 72, 255), width=22)
                d.line([(48, 172), (172, 48)], fill=(255, 64, 72, 255), width=22)
                _layer_cache["nosign"] = np.array(im)
            fx.place_center(frame, _layer_cache["nosign"], 880, 1180, clamp((d3 - 0.1) / 0.1), 0.5 + 0.5 * ease_back(clamp((d3 - 0.1) / 0.25)))


def g_rings(frame, t, seg, ctx):
    dt = t - seg["t0"]
    lay = fx.glow_ring(1000, 760, phase=dt * 5.0, rng=np.random.default_rng(int(dt * 30)))
    fx.place_center(frame, lay, 540, 1000, clamp(dt / 0.12), 1.0)


def g_search_list(frame, t, seg, ctx):
    items = [("Real Estate Companies", 32.54), ("Influencers / Creators", 32.92), ("Small Businesses / Startups", 33.38),
             ("Filmmakers / Agencies", 33.74)]
    x0, y0 = 60, 560
    if t >= 31.98:
        lay = L("SEARCH ON IG :", "W", 120)
        fx.over(frame, lay, x0 - 50, y0 - 260, clamp((t - 31.98) / 0.1))
    # vertical connector
    shown = [it for it in items if t >= it[1]]
    if shown:
        last_y = y0 + (len(shown) - 1) * 150
        cv2.line(frame, (x0 + 10, y0 - 40), (x0 + 10, last_y + 40), (230, 235, 255), 4, cv2.LINE_AA)
    for i, (s, ts) in enumerate(items):
        if t < ts:
            continue
        key = ("pill", s)
        if key not in _layer_cache:
            f = fx.font("mont8", 50)
            tw = f.getbbox(s)[2]
            im = Image.fromarray(fx.rounded_panel(tw + 70, 100, 14, (58, 80, 230, 240), outline=(150, 170, 255, 255), width=3))
            ImageDraw.Draw(im).text((40 + 35, 40 + 22), s, font=f, fill=(255, 255, 255, 255))
            _layer_cache[key] = np.array(im)
        p = clamp((t - ts) / 0.22)
        lay = _layer_cache[key]
        fx.over(frame, lay, int(x0 - 10 + (1 - ease_out(p)) * -200), y0 + i * 150 - 90, clamp((t - ts) / 0.1))
        cv2.circle(frame, (x0 + 10, y0 + i * 150), 13, (255, 255, 255), -1, cv2.LINE_AA)
    if t >= 34.16:
        if "igicon" not in _layer_cache:
            n = 230
            g = np.zeros((n, n, 4), np.float32)
            yy, xx = np.mgrid[0:n, 0:n].astype(np.float32) / n
            c1, c2, c3 = np.array([255, 200, 80]), np.array([240, 50, 120]), np.array([120, 60, 220])
            u = np.clip((xx * 0.4 + (1 - yy) * 0.6), 0, 1)[..., None]
            col = np.where(u < 0.5, c1 + (c2 - c1) * (u / 0.5), c2 + (c3 - c2) * ((u - 0.5) / 0.5))
            g[..., :3] = col
            m = Image.new("L", (n, n), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, n - 1, n - 1], 60, fill=255)
            g[..., 3] = np.array(m)
            im = Image.fromarray(g.astype(np.uint8)); d = ImageDraw.Draw(im)
            d.rounded_rectangle([45, 45, n - 45, n - 45], 40, outline=(255, 255, 255, 255), width=16)
            d.ellipse([80, 80, n - 80, n - 80], outline=(255, 255, 255, 255), width=16)
            d.ellipse([n - 78, 60, n - 58, 80], fill=(255, 255, 255, 255))
            _layer_cache["igicon"] = np.array(im)
        dt = t - 34.16
        fx.place_center(frame, _layer_cache["igicon"], 880, 420 + 10 * math.sin(dt * 4), clamp(dt / 0.08), 0.3 + 0.7 * ease_back(clamp(dt / 0.3)), rot=8)


def g_envelope(frame, t, seg, ctx):
    t0 = 36.84
    if t < t0:
        return
    if "env" not in _layer_cache:
        im = Image.new("RGBA", (260, 200), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([10, 30, 250, 190], 20, fill=(70, 150, 255, 255))
        d.polygon([(14, 40), (130, 120), (246, 40)], fill=(150, 205, 255, 255))
        d.line([(14, 40), (130, 120), (246, 40)], fill=(255, 255, 255, 255), width=6)
        _layer_cache["env"] = np.array(im.filter(ImageFilter.GaussianBlur(0.4)))
    dt = t - t0
    fx.place_center(frame, _layer_cache["env"], 210, 690 + 12 * math.sin(dt * 3), clamp(dt / 0.1), 0.4 + 0.6 * ease_back(clamp(dt / 0.3)), rot=-10)


BARS = None


def g_timeline_bars(frame, t, seg, ctx):
    global BARS
    if BARS is None:
        rng = np.random.default_rng(3)
        cols = [(150, 80, 255), (60, 200, 140), (60, 140, 255), (255, 90, 170), (255, 170, 60)]
        BARS = []
        for i in range(18):
            w = int(rng.uniform(260, 620)); h = int(rng.uniform(46, 80))
            BARS.append(dict(img=fx.timeline_bar(w, h, cols[i % len(cols)]), y=rng.uniform(150, 1750),
                             speed=rng.uniform(900, 1800), x0=rng.uniform(0, 2400), a=rng.uniform(0.55, 0.95)))
    dt = t - seg["t0"]
    for b in BARS:
        x = 1500 + b["x0"] - (dt * b["speed"]) % 2600 - 600
        lay = b["img"]
        if b["speed"] > 1400:
            lay = fx.motion_blur(lay, 9, 0)
        fx.over(frame, lay, int(x), int(b["y"]), b["a"] * clamp(dt / 0.2))


def g_profile_card(frame, t, seg, ctx):
    t0 = seg["t0"] + 0.05
    if t < t0:
        return
    if "profile" not in _layer_cache:
        w, h = 470, 760
        im = Image.new("RGBA", (w + 60, h + 60), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([30, 30, 30 + w, 30 + h], 36, fill=(18, 22, 34, 215), outline=(120, 180, 255, 230), width=4)
        face = cv2.cvtColor(cv2.imread(os.path.join(WORK, "airef", "ref_face.jpg")), cv2.COLOR_BGR2RGB)
        face = face[200:200 + 1000, 40:40 + 1000]
        face = cv2.resize(face, (140, 140), interpolation=cv2.INTER_AREA)
        m = Image.new("L", (140, 140), 0); ImageDraw.Draw(m).ellipse([0, 0, 139, 139], fill=255)
        im.paste(Image.fromarray(face), (60, 70), m)
        d.ellipse([56, 66, 204, 214], outline=(255, 120, 180, 255), width=5)
        f1, f2 = fx.font("mont8", 34), fx.font("inter", 26)
        d.text((230, 92), "velora.media", font=f1, fill=(255, 255, 255, 255))
        for i, (n, lab) in enumerate([("128", "posts"), ("24.6K", "followers"), ("312", "following")]):
            d.text((230 + i * 85, 150), n, font=fx.font("mont8", 26), fill=(255, 255, 255, 255))
            d.text((230 + i * 85, 182), lab, font=fx.font("inter", 18), fill=(170, 180, 200, 255))
        d.text((62, 238), "FILMMAKER | EDITOR | VFX", font=fx.font("mont8", 24), fill=(255, 255, 255, 255))
        d.text((62, 272), "DM for business", font=f2, fill=(170, 190, 230, 255))
        d.rounded_rectangle([62, 318, 30 + w - 32, 368], 14, fill=(64, 120, 255, 255))
        d.text((200, 328), "Follow", font=fx.font("mont8", 26), fill=(255, 255, 255, 255))
        thumbs = _thumbs()
        for i in range(6):
            th = Image.fromarray(thumbs[i % len(thumbs)]).resize((140, 236))
            im.alpha_composite(th, (52 + (i % 3) * 146, 392 + (i // 3) * 200))
        arr = np.array(im)
        glow = cv2.GaussianBlur(arr, (0, 0), 14)
        out = arr.copy(); fx.over_rgba(glow, arr, 0, 0)
        _layer_cache["profile"] = fx.perspective(glow, 0.16, "left")
    dt = t - t0
    p = ease_back(clamp(dt / 0.35))
    fx.place_center(frame, _layer_cache["profile"], 250 - 200 * (1 - p), 980, clamp(dt / 0.12), 0.95, rot=0)


def g_cta_bg(frame, t, seg, ctx):
    """Replace the background of the closing selfie with the reel's blue stripe backdrop."""
    if ctx.get("mask") is None:
        return
    if "cta_bg" not in _layer_cache:
        bg = np.zeros((H, W, 3), np.float32)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        u = (xx / W * 0.6 + yy / H * 0.4)
        c1, c2 = np.array([40, 92, 245]), np.array([96, 150, 255])
        bg[:] = c1 + (c2 - c1) * u[..., None]
        band = np.abs((yy - 0.62 * xx) - 1250) < 70
        bg[band] = bg[band] * 0.3 + 255 * 0.7
        band2 = np.abs((yy - 0.62 * xx) - 1450) < 26
        bg[band2] = bg[band2] * 0.4 + 255 * 0.6
        _layer_cache["cta_bg"] = bg.astype(np.uint8)
    dt = t - seg["t0"]
    bg = fx.zoom(_layer_cache["cta_bg"], 1.0 + 0.03 * dt).astype(np.float32)
    a = ease_out(clamp(dt / 0.35))
    sc = 1.0 - 0.28 * a                     # person shrinks to 72% and slides left
    ox = -90 * a; oy = H * (1 - sc)
    M = np.float32([[sc, 0, ox], [0, sc, oy]])
    person = cv2.warpAffine(frame, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE).astype(np.float32)
    m = cv2.warpAffine(ctx["mask"], M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    # keep the bottom edge solid so the body is not cut off by the backdrop
    m[int(H - 40):, :] = np.maximum(m[int(H - 40):, :], (m[int(H - 41), :] > 0.5).astype(np.float32))
    m = m[..., None]
    frame[:] = np.clip(person * m + bg * (1 - m), 0, 255).astype(np.uint8)


def g_cta_cards(frame, t, seg, ctx):
    if t >= 64.05:
        if "cta_panel" not in _layer_cache:
            p = Image.fromarray(fx.rounded_panel(560, 270, 30, (255, 255, 255, 245)))
            arr = np.array(p)
            fx.over_rgba(arr, L("OUTREACH", "B", 160), 40 + 20, 40 - 30)
            fx.over_rgba(arr, L("TEMPLATE", "B", 100), 40 + 230, 40 + 130)
            _layer_cache["cta_panel"] = arr
        dt = t - 64.05
        fx.place_center(frame, _layer_cache["cta_panel"], 725, 430, clamp(dt / 0.1), 0.5 + 0.5 * ease_back(clamp(dt / 0.3)))
    if t >= 65.45:
        if "cta_card" not in _layer_cache:
            p = Image.fromarray(fx.rounded_panel(440, 330, 30, (196, 186, 255, 250), outline=(120, 100, 255, 255), width=6))
            d = ImageDraw.Draw(p)
            d.text((40 + 40, 40 + 30), "FOLLOW", font=fx.font("mont", 56), fill=(24, 20, 70, 255))
            d.text((40 + 40, 40 + 92), "& COMMENT", font=fx.font("mont", 56), fill=(24, 20, 70, 255))
            arr = np.array(p)
            fx.over_rgba(arr, L("“CLIENTS”", "B", 110), 40 - 10, 40 + 140)
            _layer_cache["cta_card"] = arr
        dt = t - 65.45
        fx.place_center(frame, _layer_cache["cta_card"], 770, 770, clamp(dt / 0.1), 0.5 + 0.5 * ease_back(clamp(dt / 0.3)), rot=-7)
    if t >= 66.43:
        dt = t - 66.43
        fx.place_center(frame, L("FOR THE LINK", "W", 90), 790, 1020, clamp(dt / 0.1), 1.2 - 0.2 * ease_back(clamp(dt / 0.2)))


def g_niche(frame, t, seg, ctx):
    labels = [("1) AI VFX", "EDITS", 10.00), ("2) REAL", "ESTATE", 10.42), ("3) EVENT", "EDITS", 10.84), ("4) AUTOMOBILE", "EDITS", 11.26)]
    for i, (a, b, ts) in enumerate(labels):
        te = labels[i + 1][2] if i + 1 < len(labels) else 11.72
        if ts <= t < te:
            dt = t - ts
            ai = os.path.join(AI_DIR, f"AI_niche_{i + 1}.png")
            key = ("obj", i)
            if key not in _layer_cache:
                if os.path.exists(ai):
                    im = Image.open(ai).convert("RGBA"); im.thumbnail((420, 420)); _layer_cache[key] = np.array(im)
                else:  # placeholder glowing disc until the AI object arrives
                    im = Image.new("RGBA", (300, 300), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
                    d.ellipse([60, 60, 240, 240], fill=(90, 150, 255, 200))
                    im = Image.alpha_composite(im.filter(ImageFilter.GaussianBlur(30)), im.filter(ImageFilter.GaussianBlur(2)))
                    arr = np.array(im); fx.over_rgba(arr, L(str(i + 1), "W", 120, shadow=False), 150 - 60, 150 - 110)
                    _layer_cache[key] = arr
            fx.place_center(frame, _layer_cache[key], 560, 820 - 20 * dt, clamp(dt / 0.08), 0.5 + 0.5 * ease_back(clamp(dt / 0.25)))
            fx.place_center(frame, L(a, "W", 130), 600, 1120, clamp(dt / 0.06), 1.0, rot=32)
            fx.place_center(frame, L(b, "W", 90), 700, 1240, clamp(dt / 0.06), 1.0, rot=32)


# =============================================================== EDL
def S(t0, t1, src, sin, grade="warm", speed=1.0, z=(1.0, 1.08), c=(0.5, 0.5), matte=False, items=(), punch=True,
      trans_in=None, bw_from=None, darken=0.0, blur_out=False, shake=()):
    return dict(t0=t0, t1=t1, src=src, sin=sin, grade=grade, speed=speed, z=z, c=c, matte=matte, items=list(items),
                punch=punch, trans_in=trans_in, bw_from=bw_from, darken=darken, blur_out=blur_out, shake=list(shake))


CUSTOM = dict(bubbles=g_bubbles, glass=g_glass_panel, cards=g_cards_fly, portfolio=g_portfolio_page, rings=g_rings,
              search=g_search_list, envelope=g_envelope, bars=g_timeline_bars, profile=g_profile_card, cta_bg=g_cta_bg,
              cta_cards=g_cta_cards, niche=g_niche)


def C(name, behind=False, pre=False):
    return dict(kind="custom", name=name, behind=behind, pre=pre)


EDL = [
    # 1 hook
    S(0.00, 2.05, "IMG_4960", 5.2, "warm", z=(1.04, 1.13), c=(0.5, 0.42), matte=True, punch=False, items=[
        C("bubbles", behind=True),
        text(0.92, "AS A", "W", 120, 540, 330, behind=True),
        text(1.42, "VIDEO", "WG", 330, 540, 560, behind=True, anim="slam", sfx="impact"),
        text(1.60, "EDITOR", "B", 230, 430, 800, behind=True, anim="slam"),
        text(0.60, "CLIENTS", "WI", 150, 600, 1060, rot=6),
        text(0.00, "HOW TO", "W", 200, 330, 1420, anim="slam", sfx="whoosh"),
        text(0.42, "GET", "BI", 160, 820, 1320),
    ], shake=[1.42]),
    # 2 question
    S(2.05, 5.10, "IMG_4962", 13.0, "neon", z=(1.0, 1.18), c=(0.55, 0.6), trans_in="whip", items=[
        text(2.16, "THIS IS", "W", 140, 540, 470),
        text(2.86, "PROBABLY", "W", 240, 540, 650, anim="slam"),
        text(3.12, "THE MOST ASKED", "W", 130, 540, 1270, persp=(0.2, "right")),
        text(3.88, "QUESTION", "B", 250, 540, 1450, persp=(0.2, "right"), anim="slam", sfx="impact_s"),
    ]),
    # 3 break it down
    S(5.10, 6.80, "IMG_4976", 0.2, "warm", z=(1.0, 1.5), c=(0.5, 0.42), darken=0.35, blur_out=True, items=[
        text(5.20, "AND LET ME", "W", 150, 540, 760),
        text(5.52, "BREAK IT DOWN", "B", 150, 540, 950, anim="slam", sfx="whoosh"),
        text(6.08, "FOR YOU", "W", 150, 680, 1140),
    ]),
    # 4a step 1
    S(6.80, 7.62, "IMG_4963", 6.47, "warm", z=(1.06, 1.1), matte=True, trans_in="flash", items=[
        text(6.86, "STEP 1", "B", 300, 540, 420, behind=True, anim="slam", sfx="impact"),
    ], shake=[6.88]),
    # 4b pick a niche (finger)
    S(7.62, 8.62, "IMG_4965", 5.0, "warm", z=(1.05, 1.12), items=[
        text(7.64, "PICK A", "W", 150, 540, 1300),
        text(7.98, "NICHE", "B", 300, 540, 1510, anim="slam"),
    ]),
    # 4c stop editing everything
    S(8.62, 9.98, "IMG_4962", 24.0, "neon", z=(1.0, 1.06), trans_in="whip", items=[
        text(8.70, "STOP EDITING", "W", 190, 540, 800, anim="slam", sfx="impact_s"),
        text(9.22, "EVERYTHING", "W", 120, 540, 960, tracking=10),
    ]),
    # 4d desk: niche list then black & white
    S(9.98, 13.38, "IMG_4969", 0.0, "cine", z=(1.0, 1.1), bw_from=11.72, items=[
        C("niche"),
        text(11.94, "BE KNOWN", "W", 220, 560, 1080, rot=32, anim="slam", sfx="impact_s"),
        text(12.22, "FOR ONE THING", "W", 110, 660, 1240, rot=32),
    ]),
    # 5a step 2
    S(13.38, 14.30, "IMG_4972", 2.9, "warm", z=(1.04, 1.1), matte=True, trans_in="flash", items=[
        text(13.44, "STEP 2", "B", 300, 540, 400, behind=True, anim="slam", sfx="impact"),
    ], shake=[13.44]),
    # 5b portfolio hologram (slow motion)
    S(14.30, 15.42, "IMG_4974", 2.2, "neon", speed=0.5, z=(1.02, 1.08), items=[C("glass")]),
    # 6a without clients
    S(15.42, 17.95, "IMG_4977", 0.0, "warm", z=(1.0, 1.2), c=(0.5, 0.4), trans_in="whip", items=[
        text(15.46, "WITHOUT", "W", 150, 540, 1150, t1=16.20),
        text(15.62, "CLIENTS", "B", 230, 540, 1330, t1=16.20, anim="slam"),
        text(16.26, "YOU CAN STILL MAKE A", "W", 110, 540, 1170),
        text(17.28, "PORTFOLIO", "B", 250, 540, 1340, anim="slam", sfx="impact_s"),
        C("cards"),
    ]),
    # 6b shoot your own footage (placeholder until AI clip)
    S(17.95, 18.85, "IMG_4975", 4.0, "neon", speed=0.5, z=(1.05, 1.12), items=[
        text(18.00, "SHOOT YOUR", "W", 160, 540, 470, sfx="shutter"),
        text(18.36, "OWN FOOTAGE", "B", 190, 540, 650),
    ]),
    # 6c free clips
    S(18.85, 21.30, "IMG_4968", 4.2, "neon", z=(1.0, 1.1), trans_in="whip", items=[
        text(18.90, "OR USE", "W", 150, 540, 560),
        text(19.68, "FREE CLIPS", "B", 220, 540, 750, anim="slam"),
        text(20.24, "FROM THE INTERNET", "W", 130, 540, 930),
    ]),
    # 6d create your best work
    S(21.30, 22.65, "IMG_4966", 7.0, "neon", z=(1.05, 1.15), items=[
        text(21.36, "CREATE YOUR", "W", 150, 540, 660),
        text(21.78, "BEST WORK", "R", 220, 540, 860, anim="slam", sfx="impact_s"),
    ]),
    # 7 portfolio website (graphics only)
    S(22.65, 27.70, None, 0, "clean", z=(1.0, 1.0), trans_in="whip", punch=False, items=[C("portfolio", pre=True)]),
    # 8 step 3
    S(27.70, 28.80, "IMG_4978", 2.74, "warm", z=(1.05, 1.1), matte=True, trans_in="whip", items=[
        text(28.04, "STEP 3", "B", 290, 540, 380, behind=True, anim="slam", sfx="impact"),
    ], shake=[28.06]),
    # 9 outreach (laptop to lens)
    S(28.80, 29.50, "IMG_4979", 8.05, "warm", z=(1.0, 1.1), items=[
        C("rings", behind=False),
        text(28.86, "OUTREACH", "G", 250, 540, 420, anim="slam", sfx="shimmer"),
    ]),
    # 10 send DMs
    S(29.50, 31.90, "IMG_4967", 5.5, "neon", z=(1.08, 1.2), trans_in="whip", items=[
        text(29.56, "SEND 20-30", "W", 170, 540, 600, sfx="typing"),
        text(30.60, "DMs", "B", 240, 540, 800, anim="slam"),
        text(31.06, "& EMAILS", "W", 170, 540, 990),
        text(31.30, "EVERYDAY", "B", 200, 540, 1170),
    ]),
    # 11 who to DM
    S(31.90, 35.30, "IMG_4980", 5.57, "warm", speed=1.16, z=(1.12, 1.16), c=(0.3, 0.5), items=[C("search")]),
    # 12 get my template
    S(35.30, 39.95, "IMG_4982", 3.4, "warm", z=(1.0, 1.12), trans_in="whip", items=[
        C("envelope"),
        text(36.10, "GET MY EXACT", "W", 110, 610, 500),
        text(36.84, "OUTREACH", "W", 230, 610, 670, anim="slam"),
        text(37.46, "TEMPLATE", "W", 150, 610, 840),
        text(38.22, "JUST FOLLOW & COMMENT", "W", 80, 610, 990),
        text(38.46, "“CLIENTS”", "B", 230, 610, 1170, anim="slam", sfx="impact"),
    ]),
    # 13 step 4 overdeliver (placeholder until AI clip)
    S(39.95, 44.55, "IMG_4968", 3.9, "neon", speed=0.8, z=(1.04, 1.14), trans_in="flash", items=[
        C("bars", pre=False),
        text(40.14, "STEP 4", "B", 330, 540, 620, t1=41.85, anim="slam", sfx="impact"),
        text(41.08, "OVERDELIVER", "W", 200, 540, 840, t1=41.85, anim="slam"),
        text(41.90, "BECAUSE THIS IS YOUR", "W", 100, 540, 1180, t1=43.50),
        text(42.80, "FIRST CLIENT", "B", 210, 540, 1340, t1=43.50, anim="slam"),
        text(43.58, "BE RELIABLE", "W", 180, 540, 860, anim="slam", sfx="impact_s"),
    ], shake=[40.16]),
    # 14 communicate / best edit
    S(44.55, 47.72, "IMG_4966", 7.5, "neon", z=(1.0, 1.12), trans_in="whip", items=[
        text(44.62, "COMMUNICATE", "W", 180, 540, 620, t1=45.70),
        text(45.06, "WELL", "B", 230, 540, 820, t1=45.70, anim="slam"),
        text(45.76, "GIVE THE BEST", "W", 140, 540, 1100),
        text(46.42, "EDIT", "R", 380, 540, 1340, anim="slam", sfx="impact_s"),
        text(47.02, "TO YOUR CLIENT", "W", 110, 540, 1560),
    ]),
    # 15 one happy client (placeholder until AI clips)
    S(47.72, 51.45, "IMG_4962", 25.0, "neon", z=(1.0, 1.15), trans_in="whip", items=[
        text(48.10, "ONE HAPPY", "W", 170, 540, 600),
        text(48.96, "CLIENT", "B", 260, 540, 800, anim="slam"),
        text(49.34, "CAN BRING IN", "W", 140, 540, 1120),
        text(50.30, "10 MORE", "G", 290, 540, 1380, anim="slam", sfx="impact"),
    ], shake=[50.30]),
    # 16 step 5 (placeholder until AI clip / reshoot)
    S(51.45, 53.10, "IMG_4980", 3.2, "warm", z=(1.1, 1.2), matte=True, trans_in="flash", items=[
        text(51.70, "STEP 5", "B", 340, 560, 720, behind=True, anim="slam", sfx="impact"),
        text(52.28, "FINAL STEP", "W", 200, 560, 960, anim="slam"),
    ], shake=[51.72]),
    # 17 personal brand (cover shot)
    S(53.10, 54.50, "IMG_4960", 9.0, "dark", z=(1.06, 1.12), c=(0.5, 0.45), matte=True, trans_in="whip", items=[
        C("profile"),
        text(53.16, "BUILD A", "W", 100, 540, 150),
        text(53.48, "PERSONAL", "W", 190, 540, 320, behind=True, anim="slam"),
        text(53.82, "BRAND", "WG", 230, 800, 560, behind=True, anim="slam", sfx="impact_s"),
    ]),
    # 18 what to post
    S(54.50, 55.90, "IMG_4977", 0.5, "warm", z=(1.1, 1.25), c=(0.5, 0.35), items=[
        text(54.54, "YOU CAN POST:", "W", 100, 600, 1010, t1=58.62),
        text(55.06, "1) BEFORE & AFTER EDITS", "W", 90, 600, 1130, t1=58.62, anim="left"),
    ]),
    S(55.90, 56.60, "IMG_4976", 3.0, "dark", z=(1.4, 1.55), c=(0.5, 0.35), trans_in="whip", items=[
        text(54.54, "YOU CAN POST:", "W", 100, 600, 1010, anim="none"),
        text(55.06, "1) BEFORE & AFTER EDITS", "W", 90, 600, 1130, anim="none"),
    ]),
    S(56.60, 57.50, "IMG_4976", 1.0, "warm", z=(1.15, 1.25), items=[
        text(54.54, "YOU CAN POST:", "W", 100, 600, 1010, anim="none"),
        text(55.06, "1) BEFORE & AFTER EDITS", "W", 90, 600, 1130, anim="none"),
        text(56.70, "2) BEHIND THE SCENES", "W", 90, 600, 1240, anim="left"),
    ]),
    S(57.50, 58.62, "IMG_4968", 5.0, "neon", z=(1.0, 1.08), trans_in="whip", items=[
        text(54.54, "YOU CAN POST:", "W", 100, 600, 1010, anim="none"),
        text(55.06, "1) BEFORE & AFTER EDITS", "W", 90, 600, 1130, anim="none"),
        text(56.70, "2) BEHIND THE SCENES", "W", 90, 600, 1240, anim="none"),
        text(57.56, "3) EDIT BREAKDOWNS", "B", 100, 600, 1355, anim="left"),
    ]),
    # 19 long run (placeholder until AI clip)
    S(58.62, 62.10, "IMG_4973", 2.6, "clean", z=(1.0, 1.12), trans_in="whip", items=[
        text(58.66, "WHICH CAN GET YOU", "W", 110, 540, 520),
        text(59.84, "A LOT OF", "W", 150, 540, 680),
        text(60.34, "CLIENTS", "B", 300, 540, 900, anim="slam", sfx="impact_s"),
        text(60.64, "IN THE LONG RUN", "W", 120, 540, 1100, sfx="riser"),
    ]),
    # 20 CTA selfie with blue backdrop
    S(62.10, 67.90, "IMG_4985", 0.25, "clean", z=(1.0, 1.06), c=(0.5, 0.4), matte=True, trans_in="flash", items=[
        C("cta_bg", pre=True), C("cta_cards"),
    ]),
]
TOTAL = EDL[-1]["t1"]


# =============================================================== render
def build_events():
    """SFX cue list for audio.py."""
    ev = []
    for s in EDL:
        if s["trans_in"] == "whip":
            ev.append(("whoosh", s["t0"] - 0.12))
        elif s["trans_in"] == "flash":
            ev.append(("hit", s["t0"]))
        for it in s["items"]:
            if it["kind"] == "text" and it.get("sfx") and it["anim"] != "none" and it["t0"] >= s["t0"] - 1e-6:
                ev.append((it["sfx"], it["t0"]))
    for ts in (32.54, 32.92, 33.38, 33.74):
        ev.append(("click", ts))
    ev.append(("pop", 34.16)); ev.append(("ding", 50.86))
    ev.append(("pop", 64.05)); ev.append(("pop", 65.45)); ev.append(("click", 66.43))
    ev.append(("whoosh", 14.30)); ev.append(("riser_long", 60.2))
    for i in range(14):
        ev.append(("bubble", 0.05 + i * 0.065))
    return sorted(ev, key=lambda e: e[1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out"); ap.add_argument("--from", dest="t_from", type=float, default=0.0)
    ap.add_argument("--to", dest="t_to", type=float, default=None)
    ap.add_argument("--stills", default=None, help="write a PNG every N seconds instead of video")
    ap.add_argument("--every", type=float, default=0.5)
    ap.add_argument("--events", default=None)
    ap.add_argument("--size", default=f"{W}x{H}")
    ap.add_argument("--crf", default="18")
    args = ap.parse_args()
    if args.events:
        json.dump(build_events(), open(args.events, "w"))
    t_to = args.t_to if args.t_to is not None else TOTAL
    segm = Segmenter(os.path.join(WORK, "models", "selfie_multiclass.tflite"))

    enc = None
    if not args.stills:
        ow, oh = map(int, args.size.split("x"))
        vf = [] if (ow, oh) == (W, H) else ["-vf", f"scale={ow}:{oh}:flags=lanczos"]
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                                "-i", "-", *vf, "-c:v", "libx264", "-preset", "medium", "-crf", args.crf, "-pix_fmt", "yuv420p",
                                "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-movflags", "+faststart",
                                args.out], stdin=subprocess.PIPE)
    else:
        os.makedirs(args.stills, exist_ok=True)

    n0, n1 = int(round(args.t_from * FPS)), int(round(t_to * FPS))
    seg_idx, clip, mask_ema = -1, None, None
    t_start = time.time()
    next_still = args.t_from
    for n in range(n0, n1):
        t = n / FPS
        i = next(k for k, s in enumerate(EDL) if s["t0"] <= t < s["t1"] or k == len(EDL) - 1)
        s = EDL[i]
        if i != seg_idx:
            if clip: clip.close()
            seg_idx, mask_ema = i, None
            nfr = int((s["t1"] - s["t0"]) * FPS) + 4
            sin = s["sin"] + max(0.0, t - s["t0"]) * s["speed"]
            clip = Clip(s["src"], sin, s["speed"], nfr) if s["src"] else None
        lt = t - s["t0"]; dur = s["t1"] - s["t0"]
        frame = clip.next() if clip else np.zeros((H, W, 3), np.uint8)
        # camera move
        p = lt / max(dur, 1e-3)
        z = s["z"][0] + (s["z"][1] - s["z"][0]) * ease_in_out(p)
        if s["punch"] and lt < 0.2:
            z *= 1.0 + 0.07 * (1 - ease_out(lt / 0.2))
        dx = dy = 0.0
        for ts in s["shake"]:
            if 0 <= t - ts < 0.3:
                amp = 22 * (1 - (t - ts) / 0.3)
                dx += amp * math.sin(n * 2.7); dy += amp * math.cos(n * 3.1)
        if clip:
            frame = fx.zoom(frame, z, s["c"][0], s["c"][1], dx, dy)
        # grade
        if clip:
            gname = "bw" if (s["bw_from"] and t >= s["bw_from"]) else s["grade"]
            frame = fx.grade(frame, gname)
            if s["darken"]:
                frame = (frame.astype(np.float32) * (1 - s["darken"] * clamp(lt / 0.2))).astype(np.uint8)
            if s["blur_out"] and dur - lt < 0.35:
                frame = fx.motion_blur(frame, 2 + 40 * (1 - (dur - lt) / 0.35), 90)
        # matte
        ctx = {"mask": None}
        if s["matte"]:
            m = segm.person(frame)
            m = cv2.GaussianBlur(m, (0, 0), 3)
            mask_ema = m if mask_ema is None else 0.55 * m + 0.45 * mask_ema
            ctx["mask"] = np.clip((mask_ema - 0.35) / 0.3, 0, 1).astype(np.float32)
        # pre-layers (backgrounds), behind layers, person, front layers
        for it in s["items"]:
            if it["kind"] == "custom" and it["pre"]:
                CUSTOM[it["name"]](frame, t, s, ctx)
        base = frame.copy()
        behind = [it for it in s["items"] if it.get("behind")]
        if behind:
            for it in behind:
                if it["kind"] == "text": draw_text(frame, it, t, s["t1"])
                else: CUSTOM[it["name"]](frame, t, s, ctx)
            if ctx["mask"] is not None:
                m3 = ctx["mask"][..., None]
                frame = (base * m3 + frame * (1 - m3)).astype(np.uint8)
        for it in s["items"]:
            if it.get("behind") or (it["kind"] == "custom" and it["pre"]):
                continue
            if it["kind"] == "text": draw_text(frame, it, t, s["t1"])
            else: CUSTOM[it["name"]](frame, t, s, ctx)
        # transitions
        if s["trans_in"] == "flash" and lt < 0.16:
            a = 0.85 * (1 - lt / 0.16)
            frame = (frame.astype(np.float32) * (1 - a) + 255 * a).astype(np.uint8)
        if s["trans_in"] == "whip" and lt < 0.12:
            k = 1 - lt / 0.12
            frame = fx.motion_blur(fx.zoom(frame, 1.0, dx=-260 * k), 6 + 70 * k, 0)
        if i + 1 < len(EDL) and EDL[i + 1]["trans_in"] == "whip" and dur - lt <= 0.12:
            k = 1 - (dur - lt) / 0.12
            frame = fx.motion_blur(fx.zoom(frame, 1.0, dx=260 * k), 6 + 70 * k, 0)
        if s["trans_in"] == "flash" and lt < 0.1:
            frame = fx.rgb_split(frame, 10 * (1 - lt / 0.1))
        frame = fx.grain(fx.sharpen(frame, 0.25), n, 5)
        if args.stills:
            if t + 1e-6 >= next_still:
                cv2.imwrite(os.path.join(args.stills, f"f_{t:06.2f}.jpg"), cv2.cvtColor(cv2.resize(frame, (360, 640), interpolation=cv2.INTER_AREA), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 88])
                next_still += args.every
        else:
            enc.stdin.write(frame.tobytes())
        if n % 60 == 0:
            el = time.time() - t_start
            print(f"t={t:6.2f}s  frame {n - n0}/{n1 - n0}  {el:6.1f}s elapsed", flush=True)
    if clip: clip.close()
    if enc:
        enc.stdin.close(); enc.wait()
    print("RENDER DONE", time.time() - t_start)


if __name__ == "__main__":
    main()
