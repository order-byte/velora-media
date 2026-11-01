"""Image helpers for the reel renderer: grading, text layers, compositing, graphics."""
import math, os, random
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
FONT_DIR = os.environ.get("REEL_FONTS", "")
FONTS = {
    "anton": "anton-400-normal.ttf",
    "bebas": "bebas-neue-400-normal.ttf",
    "mont": "montserrat-900-normal.ttf",
    "monti": "montserrat-900-italic.ttf",
    "mont8": "montserrat-800-normal.ttf",
    "inter": "inter-600-normal.ttf",
}
BLUE = (47, 107, 255)
BLUE2 = (88, 150, 255)
WHITE = (255, 255, 255)
_font_cache = {}


def font(name, size):
    key = (name, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(os.path.join(FONT_DIR, FONTS[name]), size)
    return _font_cache[key]


# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def ease_out(x):
    x = clamp(x); return 1 - (1 - x) ** 3


def ease_in_out(x):
    x = clamp(x); return 3 * x * x - 2 * x * x * x


def ease_back(x, s=1.70158):
    x = clamp(x) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2


# ---------------------------------------------------------------- grading
def _curve(points):
    xs, ys = zip(*points)
    return np.clip(np.interp(np.arange(256), xs, ys), 0, 255).astype(np.uint8)


GRADES = {
    # name: per-channel tone curves (R, G, B), saturation, vignette strength
    "cine": dict(r=[(0, 4), (64, 52), (128, 132), (192, 206), (255, 252)],
                 g=[(0, 6), (64, 56), (128, 128), (192, 200), (255, 248)],
                 b=[(0, 14), (64, 66), (128, 128), (192, 192), (255, 240)], sat=1.12, vig=0.38),
    "warm": dict(r=[(0, 6), (64, 60), (128, 140), (192, 212), (255, 255)],
                 g=[(0, 4), (64, 54), (128, 128), (192, 198), (255, 246)],
                 b=[(0, 10), (64, 54), (128, 112), (192, 178), (255, 228)], sat=1.10, vig=0.40),
    "dark": dict(r=[(0, 0), (64, 34), (128, 104), (192, 186), (255, 246)],
                 g=[(0, 2), (64, 38), (128, 104), (192, 182), (255, 242)],
                 b=[(0, 12), (64, 54), (128, 120), (192, 190), (255, 240)], sat=1.05, vig=0.55),
    "neon": dict(r=[(0, 0), (64, 50), (128, 132), (192, 210), (255, 255)],
                 g=[(0, 0), (64, 48), (128, 126), (192, 204), (255, 252)],
                 b=[(0, 8), (64, 60), (128, 136), (192, 214), (255, 255)], sat=1.25, vig=0.45),
    "clean": dict(r=[(0, 8), (64, 62), (128, 134), (192, 204), (255, 252)],
                  g=[(0, 8), (64, 62), (128, 132), (192, 202), (255, 250)],
                  b=[(0, 12), (64, 66), (128, 132), (192, 200), (255, 246)], sat=1.06, vig=0.25),
    "bw": dict(r=[(0, 10), (64, 50), (128, 128), (192, 206), (255, 250)],
               g=[(0, 10), (64, 50), (128, 128), (192, 206), (255, 250)],
               b=[(0, 10), (64, 50), (128, 128), (192, 206), (255, 250)], sat=0.0, vig=0.45),
}
_luts = {}
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
_rad = np.sqrt(((_xx - W / 2) / (W * 0.62)) ** 2 + ((_yy - H / 2) / (H * 0.62)) ** 2)
_vig_base = np.clip(_rad, 0, 1.4) ** 2.2


def grade(img, name):
    g = GRADES[name]
    if name not in _luts:
        _luts[name] = np.stack([_curve(g["r"]), _curve(g["g"]), _curve(g["b"])], -1)[None]  # 1x256x3
    lut = _luts[name]
    out = cv2.LUT(img, lut)
    f = out.astype(np.float32)
    y = f[..., 0] * 0.299 + f[..., 1] * 0.587 + f[..., 2] * 0.114
    f = y[..., None] + g["sat"] * (f - y[..., None])
    f *= (1.0 - g["vig"] * _vig_base)[..., None]
    return np.clip(f, 0, 255).astype(np.uint8)


_grain = None


def grain(img, i, amt=7):
    global _grain
    if _grain is None:
        rng = np.random.default_rng(7)
        _grain = [cv2.GaussianBlur(rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32), (0, 0), 0.6) for _ in range(6)]
        _grain = [cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR) for g in _grain]
    n = _grain[i % len(_grain)]
    return np.clip(img.astype(np.float32) + amt * n[..., None], 0, 255).astype(np.uint8)


def sharpen(img, amt=0.35):
    b = cv2.GaussianBlur(img, (0, 0), 1.6)
    return cv2.addWeighted(img, 1 + amt, b, -amt, 0)


# ---------------------------------------------------------------- transforms
def zoom(img, s, cx=0.5, cy=0.5, dx=0.0, dy=0.0, rot=0.0):
    """Scale about (cx, cy) in normalised coords, then shift by (dx, dy) px."""
    if abs(s - 1) < 1e-4 and dx == 0 and dy == 0 and rot == 0:
        return img
    M = cv2.getRotationMatrix2D((cx * W, cy * H), rot, s)
    M[0, 2] += dx; M[1, 2] += dy
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def motion_blur(img, length, angle=0.0):
    length = int(length)
    if length < 3:
        return img
    k = np.zeros((length, length), np.float32)
    k[length // 2, :] = 1.0 / length
    M = cv2.getRotationMatrix2D((length / 2 - 0.5, length / 2 - 0.5), angle, 1.0)
    k = cv2.warpAffine(k, M, (length, length))
    k /= max(k.sum(), 1e-6)
    return cv2.filter2D(img, -1, k)


def rgb_split(img, px):
    if px < 1:
        return img
    out = img.copy()
    out[..., 0] = np.roll(img[..., 0], int(px), axis=1)
    out[..., 2] = np.roll(img[..., 2], -int(px), axis=1)
    return out


# ---------------------------------------------------------------- compositing
def over(dst, rgba, x, y, alpha=1.0):
    """Alpha-composite an RGBA uint8 patch onto dst (RGB uint8) with top-left at (x, y)."""
    h, w = rgba.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(dst.shape[1], x + w), min(dst.shape[0], y + h)
    if x1 <= x0 or y1 <= y0 or alpha <= 0:
        return dst
    p = rgba[y0 - y:y1 - y, x0 - x:x1 - x]
    a = p[..., 3:4].astype(np.float32) * (alpha / 255.0)
    region = dst[y0:y1, x0:x1].astype(np.float32)
    dst[y0:y1, x0:x1] = (p[..., :3].astype(np.float32) * a + region * (1 - a)).astype(np.uint8)
    return dst


def over_full(dst, layer_rgba, alpha=1.0):
    return over(dst, layer_rgba, 0, 0, alpha)


def transform_rgba(rgba, scale=1.0, rot=0.0, out_size=None):
    h, w = rgba.shape[:2]
    if abs(scale - 1) < 1e-3 and rot == 0:
        return rgba
    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
    if rot == 0:
        return cv2.resize(rgba, (nw, nh), interpolation=cv2.INTER_LINEAR if scale > 1 else cv2.INTER_AREA)
    d = int(math.hypot(nw, nh)) + 4
    M = cv2.getRotationMatrix2D((w / 2, h / 2), rot, scale)
    M[0, 2] += d / 2 - w / 2; M[1, 2] += d / 2 - h / 2
    return cv2.warpAffine(rgba, M, (d, d), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))


def place_center(dst, rgba, cx, cy, alpha=1.0, scale=1.0, rot=0.0):
    t = transform_rgba(rgba, scale, rot)
    h, w = t.shape[:2]
    return over(dst, t, int(cx - w / 2), int(cy - h / 2), alpha)


def perspective(rgba, k=0.25, side="right"):
    """Fake 3D tilt: the given edge recedes (gets shorter) by fraction k."""
    h, w = rgba.shape[:2]
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    if side == "right":
        dst = np.float32([[0, 0], [w, h * k / 2], [w, h - h * k / 2], [0, h]])
    elif side == "left":
        dst = np.float32([[0, h * k / 2], [w, 0], [w, h], [0, h - h * k / 2]])
    elif side == "top":
        dst = np.float32([[w * k / 2, 0], [w - w * k / 2, 0], [w, h], [0, h]])
    else:
        dst = np.float32([[0, 0], [w, 0], [w - w * k / 2, h], [w * k / 2, h]])
    M = cv2.getPerspectiveTransform(src, dst)
    return cv2.warpPerspective(rgba, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))


# ---------------------------------------------------------------- text
def text_layer(text, fname="anton", size=160, fill=WHITE, stroke=0, stroke_fill=(0, 0, 0), glow=None, shadow=True,
               tracking=0, italic_skew=0.0, pad=60, extrude=0):
    """Render text to an RGBA numpy patch with optional glow, soft shadow and 3D extrusion."""
    if extrude:
        base_lay = text_layer(text, fname, size, fill, stroke, stroke_fill, glow, False, tracking, italic_skew, pad + extrude)
        f = font(fname, size)
        side = text_layer(text, fname, size, (120, 124, 140), 0, (0, 0, 0), None, False, tracking, italic_skew, pad + extrude)
        h, w = base_lay.shape[:2]
        out = np.zeros_like(base_lay)
        for i in range(extrude, 0, -1):
            shade = 0.55 + 0.45 * (1 - i / extrude)
            s = side.copy(); s[..., :3] = (s[..., :3].astype(np.float32) * shade).astype(np.uint8)
            over_rgba(out, s, int(i * 0.35), i)
        if shadow:
            a = out[..., 3].astype(np.float32) / 255.0
            sh = cv2.GaussianBlur(a, (0, 0), size * 0.07)
            sh = np.roll(sh, int(size * 0.05), 0) * 0.6
            shl = np.zeros_like(out); shl[..., 3] = (sh * 255).astype(np.uint8)
            over_rgba(shl, out, 0, 0); out = shl
        over_rgba(out, base_lay, 0, 0)
        return out
    f = font(fname, size)
    # measure with tracking
    if tracking:
        widths = [f.getbbox(c)[2] - f.getbbox(c)[0] if c != " " else size * 0.28 for c in text]
        tw = int(sum(widths) + tracking * (len(text) - 1))
    else:
        bb = f.getbbox(text); tw = bb[2] - bb[0]
    asc, desc = f.getmetrics()
    th = asc + desc
    Wp, Hp = tw + pad * 2, th + pad * 2
    img = Image.new("RGBA", (Wp, Hp), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if tracking:
        x = pad
        for c, cw in zip(text, widths):
            if c != " ":
                bb = f.getbbox(c)
                d.text((x - bb[0], pad), c, font=f, fill=fill + (255,), stroke_width=stroke, stroke_fill=stroke_fill)
            x += cw + tracking
    else:
        bb = f.getbbox(text)
        d.text((pad - bb[0], pad), text, font=f, fill=fill + (255,), stroke_width=stroke, stroke_fill=stroke_fill)
    base = np.array(img)
    if italic_skew:
        M = np.float32([[1, -italic_skew, italic_skew * Hp / 2], [0, 1, 0]])
        base = cv2.warpAffine(base, M, (Wp, Hp), borderValue=(0, 0, 0, 0))
    a = base[..., 3].astype(np.float32) / 255.0
    out = np.zeros_like(base, dtype=np.float32)
    if shadow:
        sh = cv2.GaussianBlur(a, (0, 0), size * 0.06)
        sh = np.roll(np.roll(sh, int(size * 0.03), 0), int(size * 0.01), 1) * 0.55
        out[..., 3] = sh * 255
    if glow is not None:
        gl = cv2.GaussianBlur(a, (0, 0), size * 0.12) * 1.25
        ga = np.clip(gl, 0, 1)
        for c in range(3):
            out[..., c] = out[..., c] * (1 - ga) + glow[c] * ga
        out[..., 3] = np.maximum(out[..., 3], ga * 255 * 0.85)
    # text on top
    for c in range(3):
        out[..., c] = out[..., c] * (1 - a) + base[..., c] * a
    out[..., 3] = np.maximum(out[..., 3], a * 255)
    # keep colour where alpha is from shadow only: shadow colour black
    return np.clip(out, 0, 255).astype(np.uint8)


def stack_layers(layers, gap=-10, align="center"):
    """Vertically stack RGBA patches."""
    w = max(l.shape[1] for l in layers)
    h = sum(l.shape[0] for l in layers) + gap * (len(layers) - 1)
    out = np.zeros((max(h, 1), w, 4), np.uint8)
    y = 0
    for l in layers:
        x = (w - l.shape[1]) // 2 if align == "center" else 0 if align == "left" else w - l.shape[1]
        over_rgba(out, l, x, y)
        y += l.shape[0] + gap
    return out


def over_rgba(dst, src, x, y):
    h, w = src.shape[:2]
    x0, y0, x1, y1 = max(0, x), max(0, y), min(dst.shape[1], x + w), min(dst.shape[0], y + h)
    if x1 <= x0 or y1 <= y0:
        return dst
    s = src[y0 - y:y1 - y, x0 - x:x1 - x].astype(np.float32)
    d = dst[y0:y1, x0:x1].astype(np.float32)
    sa = s[..., 3:4] / 255.0; da = d[..., 3:4] / 255.0
    oa = sa + da * (1 - sa)
    oc = (s[..., :3] * sa + d[..., :3] * da * (1 - sa)) / np.maximum(oa, 1e-6)
    dst[y0:y1, x0:x1, :3] = oc.astype(np.uint8)
    dst[y0:y1, x0:x1, 3:4] = (oa * 255).astype(np.uint8)
    return dst


# ---------------------------------------------------------------- shapes & graphics
def rounded_panel(w, h, r, fill, outline=None, width=0, shadow=True):
    pad = 40
    img = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    if shadow:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle([pad, pad + 10, pad + w, pad + h + 10], r, fill=(0, 0, 0, 110))
        img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(16)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([pad, pad, pad + w, pad + h], r, fill=fill, outline=outline, width=width)
    return np.array(img)


def chat_bubble(rng, scale=1.0):
    w = int(rng.integers(230, 330) * scale); h = int(78 * scale)
    color = [(255, 255, 255, 235), (94, 196, 120, 235), (64, 132, 255, 235)][int(rng.integers(0, 3))]
    pad = 24
    img = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([pad, pad + 6, pad + w, pad + h + 6], 18 * scale, fill=(0, 0, 0, 90))
    img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(8)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([pad, pad, pad + w, pad + h], int(18 * scale), fill=color)
    r = int(20 * scale)
    d.ellipse([pad + 14 * scale, pad + h / 2 - r, pad + 14 * scale + 2 * r, pad + h / 2 + r], fill=(205, 214, 230, 255))
    line = (60, 70, 90, 200) if color[0] > 200 else (255, 255, 255, 210)
    x0 = pad + 14 * scale + 2 * r + 12 * scale
    d.rounded_rectangle([x0, pad + 20 * scale, x0 + (w - x0 + pad) * 0.75, pad + 32 * scale], 6, fill=line)
    d.rounded_rectangle([x0, pad + 44 * scale, x0 + (w - x0 + pad) * 0.5, pad + 54 * scale], 5, fill=line)
    return np.array(img)


def glow_ring(w, h, color=(255, 196, 92), thick=10, phase=0.0, sparkles=40, rng=None):
    """Elliptical glowing light trail, used around the floating laptop."""
    img = np.zeros((h, w, 4), np.float32)
    cx, cy = w / 2, h / 2
    for k, (rx, ry, tilt) in enumerate([(w * 0.46, h * 0.16, -8), (w * 0.40, h * 0.12, 6)]):
        ring = np.zeros((h, w), np.float32)
        pts = []
        for t in np.linspace(0, 2 * math.pi, 240):
            a = t + phase * (1 if k == 0 else -1.3)
            x = cx + rx * math.cos(a); y = cy + ry * math.sin(a) + math.sin(a * 2 + phase) * 12
            pts.append((x, y))
        pts = np.array(pts, np.int32)
        cv2.polylines(ring, [pts], True, 1.0, thick, cv2.LINE_AA)
        ring = cv2.warpAffine(ring, cv2.getRotationMatrix2D((cx, cy), tilt, 1.0), (w, h))
        core = ring
        halo = cv2.GaussianBlur(ring, (0, 0), thick * 2.2)
        a = np.clip(core * 1.0 + halo * 1.4, 0, 1)
        for c in range(3):
            img[..., c] = np.maximum(img[..., c], (color[c] * (halo > 0.01) + (255 - color[c]) * core * 0.8) * 1.0)
        img[..., 3] = np.maximum(img[..., 3], a * 255)
    if rng is not None:
        for _ in range(sparkles):
            x = int(rng.uniform(0, w)); y = int(cy + rng.normal(0, h * 0.18))
            r = rng.uniform(2, 6)
            cv2.circle(img, (x, y), int(r), (255, 230, 170, 255), -1, cv2.LINE_AA)
    img[..., :3] = np.clip(img[..., :3], 0, 255)
    return img.astype(np.uint8)


def timeline_bar(w, h, color):
    img = Image.new("RGBA", (w + 20, h + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([10, 10, 10 + w, 10 + h], 8, fill=color + (230,))
    # waveform ticks
    rnd = random.Random(w * 7 + h)
    for x in range(18, w, 9):
        hh = rnd.uniform(0.15, 0.8) * h * 0.5
        d.line([(10 + x, 10 + h / 2 - hh), (10 + x, 10 + h / 2 + hh)], fill=(255, 255, 255, 120), width=3)
    return np.array(img.filter(ImageFilter.GaussianBlur(0.6)))
