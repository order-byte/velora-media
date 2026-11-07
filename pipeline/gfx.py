"""Shared drawing kit: fonts, colours, easing and Skia helpers used by every motion template."""
import math, os
import numpy as np, skia

W, H, FPS = 1920, 1080, 30
HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "assets", "fonts")

# ---------------------------------------------------------------- look & feel
INK = (17, 20, 24)
ACCENT = (214, 58, 47)       # Offscript red
GOLD = (222, 160, 40)
WHITE = (255, 255, 255)
PAPER = (246, 244, 239)
PAPER_LINE = (222, 226, 232)
MARGIN = (232, 150, 140)

TF = {k: skia.Typeface.MakeFromFile(os.path.join(FONTS, f)) for k, f in {
    "serif": "InstrumentSerif-Italic.ttf", "serif_up": "InstrumentSerif-Regular.ttf",
    "sans": "Inter-SemiBold.otf", "sans_med": "Inter-Medium.otf", "sans_bold": "Inter-Bold.otf",
    "sans_xb": "Inter-ExtraBold.otf", "mono": "CourierPrime-Bold.ttf", "mono_reg": "CourierPrime-Regular.ttf"}.items()}


def font(name, size):
    f = skia.Font(TF[name], size)
    f.setSubpixel(True)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    f.setHinting(skia.FontHinting.kNone)
    return f


def col(rgb, a=1.0):
    return skia.Color(int(rgb[0]), int(rgb[1]), int(rgb[2]), int(max(0, min(1, a)) * 255))


# ---------------------------------------------------------------- easing
def c01(x):
    return 0.0 if x <= 0 else 1.0 if x >= 1 else x


def ease_out_cubic(x):
    x = c01(x); return 1 - (1 - x) ** 3


def ease_in_cubic(x):
    x = c01(x); return x ** 3


def ease_in_out_cubic(x):
    x = c01(x); return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def ease_in_out_sine(x):
    x = c01(x); return -(math.cos(math.pi * x) - 1) / 2


def ease_out_back(x, s=1.70158):
    x = c01(x); return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2


def prog(t, a, d):
    return c01((t - a) / d) if d > 0 else (1.0 if t >= a else 0.0)


def env(t, start, end, fin=0.35, fout=0.25):
    """(in-progress, out-progress) for an element living in [start, end]."""
    return prog(t, start, fin), prog(t, end - fout, fout)


# ---------------------------------------------------------------- text helpers
def text_width(text, f, tracking=0.0):
    if not text:
        return 0.0
    g = f.textToGlyphs(text)
    return float(sum(f.getWidths(g))) + tracking * (len(g) - 1)


def draw_text(cv, text, x, y, f, rgb, alpha=1.0, blur=0.0, tracking=0.0, align="left", glow=0.0, glow_rgb=WHITE,
              shadow=0.0):
    """Draw text with optional tracking, blur-in, soft glow (for dark text on bright sky) or dark shadow."""
    if alpha <= 0.003 or not text:
        return 0.0
    w = text_width(text, f, tracking)
    if align == "right":
        x -= w
    elif align == "center":
        x -= w / 2
    g = f.textToGlyphs(text)
    widths = f.getWidths(g)
    xs, acc = [], x
    for wd in widths:
        xs.append(acc)
        acc += wd + tracking
    blob = skia.TextBlob.MakeFromPosTextH(text, [p - x for p in xs], 0, f)
    if blob is None:
        return w
    if glow > 0:
        gp = skia.Paint(AntiAlias=True, Color=col(glow_rgb, alpha * glow),
                        MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, max(4.0, f.getSize() * 0.12)))
        cv.drawTextBlob(blob, x, y, gp)
    if shadow > 0:
        sp = skia.Paint(AntiAlias=True, Color=col((0, 0, 0), alpha * shadow),
                        MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, max(3.0, f.getSize() * 0.08)))
        cv.drawTextBlob(blob, x, y + f.getSize() * 0.04, sp)
    p = skia.Paint(AntiAlias=True, Color=col(rgb, alpha))
    if blur > 0.25:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    cv.drawTextBlob(blob, x, y, p)
    return w


def wrap(text, f, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if text_width(trial, f) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


def fit_lines(text, face, size, max_w, max_lines=2, min_size=70):
    while True:
        f = font(face, size)
        lines = wrap(text, f, max_w)
        if (len(lines) <= max_lines and all(text_width(l, f) <= max_w for l in lines)) or size <= min_size:
            return f, lines
        size = int(size * 0.92)


def rrect(cv, x, y, w, h, r, rgb, alpha=1.0, shadow=0.0, stroke=None):
    rect = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r)
    if shadow > 0:
        sp = skia.Paint(AntiAlias=True, Color=col((0, 0, 0), alpha * shadow),
                        MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14))
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y + 8, w, h), r, r), sp)
    p = skia.Paint(AntiAlias=True, Color=col(rgb, alpha))
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(stroke)
    cv.drawRRect(rect, p)


def line(cv, x0, y0, x1, y1, rgb, width, alpha=1.0, cap=True):
    p = skia.Paint(AntiAlias=True, Color=col(rgb, alpha), StrokeWidth=width, Style=skia.Paint.kStroke_Style)
    if cap:
        p.setStrokeCap(skia.Paint.kRound_Cap)
    cv.drawLine(x0, y0, x1, y1, p)


SIDE_X = 112          # margin for side-anchored text
TOP_Y = 300           # baseline of the first line of side text


def side_x(side):
    return (SIDE_X, "left") if side == "L" else (W - SIDE_X, "right")


