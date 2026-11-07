"""Motion templates rebuilt from the client's five reference edits (v1.1).

Each template is named after the reference motion it reproduces (see preview/data/analysis.json):
  r1m1 stack        word-by-word lead + light serif keyword
  r1m2 prompt       AI prompt bar typing
  r1m3 lightleak    warm light-leak flash
  r1m4 torso        white serif keyword over the torso
  r1m5 (renderer)   split-screen B-roll slide-in
  r1m6 confetti     confetti burst
  r1m7 chest        bold white word stack at chest
  r2m1 counter_behind  giant counter behind the speaker's head
  r2m2 money_chart  full-screen counter with chart line
  r2m3 pills        pill tags around the speaker
  r2m4 icon_cards   icon cards on gradient
  r2m5 karaoke      karaoke caption
  r2m6/7 doc_cam    shrink-to-card into a document with circle face-cam + highlighter
  r3m1 bignum       giant number fly-in to white card
  r3m2 cards        cards in a row + number slam
  r3m3 ui_card      speaker inside a UI card
  r3m4 wavy         wavy letter reveal
  r3m5 bars         two-bar chart
  r4m1 tiles        glossy icon tiles with camera pan
  r4m2 spotlight    spotlight beam
  r4m3 tree         tree diagram
  r4m4 title_icons  title + growing icon row
  r4m5 nodes        two nodes + dashed connector
  r5m1 behind_words huge words behind the speaker
  r5m2 caption      caption with accent keyword
  r5m3 ring         ring diagram with pills
  r5m4 numchips     numbered chips beside the speaker
  r5m5 countup      count-up beside the speaker
  r5m6 blur_list    icon list on blurred background
"""
import math, random
import numpy as np, cv2, skia

from gfx import *  # noqa: F401,F403

# ---------------------------------------------------------------- palettes (taken from the references)
WARM_SERIF = (128, 117, 106)       # r1 taupe serif
NAVY = (10, 21, 33)                # r4 background
NAVY_FOG = (44, 72, 98)
TILE_TOP, TILE_BOT = (34, 52, 72), (15, 26, 39)
ICE = (176, 220, 255)
PURPLE, LILAC = (139, 44, 226), (214, 168, 255)   # r2
KARAOKE = (190, 140, 255)
CAP_HL = (232, 255, 70)            # r5 yellow-green keyword
R5_YELLOW = (255, 214, 10)
R3_BLUE_A, R3_BLUE_B = (40, 132, 255), (125, 200, 255)
R3_GOLD_A, R3_GOLD_B = (246, 196, 56), (255, 236, 160)
R3_SLAM = (229, 83, 61)
MAROON = (92, 22, 24)

# ---------------------------------------------------------------- icons (Material Symbols Rounded, filled)
_CP = {}
for _l in open(os.path.join(FONTS, "MaterialSymbolsRounded.codepoints")):
    _p = _l.split()
    if len(_p) == 2:
        _CP[_p[0]] = chr(int(_p[1], 16))


def _icon_tf(fill):
    base = skia.Typeface.MakeFromFile(os.path.join(FONTS, "MaterialSymbolsRounded.ttf"))
    tag = lambda s: (ord(s[0]) << 24) | (ord(s[1]) << 16) | (ord(s[2]) << 8) | ord(s[3])
    C = skia.FontArguments.VariationPosition.Coordinate
    vp = skia.FontArguments.VariationPosition(skia.FontArguments.VariationPosition.Coordinates(
        [C(tag("FILL"), float(fill)), C(tag("wght"), 500.0), C(tag("opsz"), 48.0)]))
    fa = skia.FontArguments()
    fa.setVariationDesignPosition(vp)
    return base.makeClone(fa)


ICON_TF = {1: _icon_tf(1), 0: _icon_tf(0)}


def icon(cv, name, cx, cy, size, rgb, alpha=1.0, fill=1, glow=0.0):
    ch = _CP.get(name, _CP["circle"])
    f = skia.Font(ICON_TF[fill], size)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    w = f.measureText(ch)
    if glow > 0:
        cv.drawString(ch, cx - w / 2, cy + size / 2, f, skia.Paint(AntiAlias=True, Color=col(rgb, alpha * glow),
                      MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, size * 0.18)))
    cv.drawString(ch, cx - w / 2, cy + size / 2, f, skia.Paint(AntiAlias=True, Color=col(rgb, alpha)))


# ---------------------------------------------------------------- shared bits
def fade_of(t, start, end, fin=0.3, fout=0.25):
    pin, pout = env(t, start, end, fin, fout)
    return ease_out_cubic(pin) * (1 - ease_in_cubic(pout)), pin, pout


def bottom_shade(cv, a, h=420, strength=0.55):
    sh = skia.GradientShader.MakeLinear([skia.Point(0, H - h), skia.Point(0, H)],
                                        [col((0, 0, 0), 0), col((0, 0, 0), strength * a)])
    cv.drawRect(skia.Rect.MakeXYWH(0, H - h, W, h), skia.Paint(Shader=sh))


def word_times(words, start, end):
    """Evenly spread reveal times for words between start and end."""
    n = max(1, len(words))
    span = max(0.12 * n, end - start)
    return [start + span * i / n for i in range(n)]


def words_reveal(cv, t, words, times, x, y, f, rgb, align="left", glow=0.0, shadow=0.0, alpha=1.0, gap=None,
                 hl_rgb=None, hl_now=False, rise=10):
    """Draw words one by one (fading/blur in at their time). Returns total width."""
    gap = f.getSize() * 0.28 if gap is None else gap
    widths = [text_width(w, f) for w in words]
    total = sum(widths) + gap * (len(words) - 1)
    cx = x if align == "left" else (x - total if align == "right" else x - total / 2)
    for i, (w, wd, at) in enumerate(zip(words, widths, times)):
        p = prog(t, at - 0.04, 0.22)
        if p > 0:
            e = ease_out_cubic(p)
            c = rgb
            if hl_rgb is not None:
                nxt = times[i + 1] if i + 1 < len(times) else at + 0.6
                if not hl_now or (at - 0.04 <= t < nxt):
                    c = hl_rgb
            draw_text(cv, w, cx, y + (1 - e) * rise, f, c, alpha * (0.35 + 0.65 * e), blur=(1 - e) * 5, glow=glow,
                      shadow=shadow)
        cx += wd + gap
    return total


def glass_tile(cv, cx, cy, s, ic, label=None, alpha=1.0, scale=1.0, label_size=22, focus=1.0):
    """r4 glossy navy tile with an icon."""
    if alpha <= 0.01:
        return
    s *= scale
    x, y = cx - s / 2, cy - s / 2
    r = s * 0.22
    rect = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, s, s), r, r)
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y + s * 0.08, s, s), r, r),
                 skia.Paint(AntiAlias=True, Color=col((0, 0, 0), 0.55 * alpha),
                            MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, s * 0.12)))
    fill = skia.GradientShader.MakeLinear([skia.Point(x, y), skia.Point(x, y + s)],
                                          [col(TILE_TOP, alpha), col(TILE_BOT, alpha)])
    cv.drawRRect(rect, skia.Paint(AntiAlias=True, Shader=fill))
    edge = skia.GradientShader.MakeLinear([skia.Point(x, y), skia.Point(x + s, y + s)],
                                          [col(ICE, 0.75 * alpha * focus + 0.15 * alpha), col(ICE, 0.08 * alpha)])
    cv.drawRRect(rect, skia.Paint(AntiAlias=True, Shader=edge, Style=skia.Paint.kStroke_Style, StrokeWidth=max(1.5, s * 0.014)))
    icon(cv, ic, cx, cy, s * 0.46, (235, 246, 255), alpha, glow=0.55 * focus)
    if label:
        draw_text(cv, label.upper(), cx, y + s + label_size * 1.6, font("sans", label_size), (230, 240, 250), alpha * 0.85,
                  align="center", tracking=1.5)


def navy_bg(cv, t, a=1.0, seed=0):
    cv.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Color=col(NAVY, a)))
    for i, (fx, fy, rad, k) in enumerate([(0.30, 0.25, 900, 0.55), (0.78, 0.70, 800, 0.45), (0.55, 0.95, 700, 0.35)]):
        dx = math.sin(t * 0.25 + i + seed) * 60
        sh = skia.GradientShader.MakeRadial(skia.Point(W * fx + dx, H * fy), rad,
                                            [col(NAVY_FOG, k * a), col(NAVY_FOG, 0)])
        cv.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Shader=sh))
    vig = skia.GradientShader.MakeRadial(skia.Point(W / 2, H / 2), W * 0.75, [col((0, 0, 0), 0), col((0, 0, 0), 0.55 * a)])
    cv.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Shader=vig))


def lilac_bg(cv, a=1.0, phase=0.0):
    cv.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Color=col(WHITE, a)))
    for fx, fy, rad, k in [(0.95 + phase * 0.05, 1.05, 1300, 0.95), (0.05, 1.1, 900, 0.55)]:
        sh = skia.GradientShader.MakeRadial(skia.Point(W * fx, H * fy), rad, [col(LILAC, k * a), col(LILAC, 0)])
        cv.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Shader=sh))


def blurred(img, k=24, dark=0.35, tint=None):
    small = cv2.resize(img[..., :3], (W // 8, H // 8), interpolation=cv2.INTER_AREA)
    small = cv2.GaussianBlur(small, (0, 0), k / 8)
    big = cv2.resize(small, (W, H), interpolation=cv2.INTER_LINEAR).astype(np.float32)
    big *= (1 - dark)
    if tint is not None:
        big = big * 0.8 + np.array(tint, np.float32) * 0.2
    out = np.empty((H, W, 4), np.uint8)
    out[..., :3] = np.clip(big, 0, 255)
    out[..., 3] = 255
    return out


def draw_image(cv, arr, dst, alpha=1.0):
    img = skia.Image.fromarray(np.ascontiguousarray(arr), colorType=skia.kRGBA_8888_ColorType)
    p = skia.Paint(AntiAlias=True, Alphaf=alpha)
    cv.drawImageRect(img, dst, skia.SamplingOptions(skia.FilterMode.kLinear), p)


def pill(cv, x, y, text, size=30, fill=WHITE, rgb=INK, alpha=1.0, ic=None, ic_rgb=None, scale=1.0, shadow=0.22,
         stroke=None):
    f = font("sans", size)
    h = size * 2.1
    icw = h * 0.62 if ic else 0
    w = text_width(text, f) + size * 1.3 + icw
    cv.save()
    cv.translate(x + w / 2, y + h / 2); cv.scale(scale, scale); cv.translate(-(x + w / 2), -(y + h / 2))
    rrect(cv, x, y, w, h, h / 2 if h < 80 else 18, fill, alpha, shadow=shadow)
    if stroke:
        rrect(cv, x, y, w, h, h / 2 if h < 80 else 18, stroke, alpha * 0.9, stroke=2.5)
    tx = x + size * 0.65
    if ic:
        cv.drawCircle(tx + icw * 0.38, y + h / 2, h * 0.24, skia.Paint(AntiAlias=True, Color=col(ic_rgb, alpha)))
        icon(cv, ic, tx + icw * 0.38, y + h / 2, h * 0.34, WHITE, alpha)
        tx += icw
    draw_text(cv, text, tx, y + h / 2 + size * 0.36, f, rgb, alpha)
    cv.restore()
    return w, h


# ================================================================== r1 motions
def m_stack(cv, t, c, ctx):
    """r1m1: small sans words appear as spoken; big serif keyword blurs in with tracking."""
    a, pin, pout = fade_of(t, c["start"], c["end"], 0.25, 0.22)
    if a <= 0:
        return
    x, align = side_x(c["side"])
    lead_f = font("sans_med", 38)
    words = c["lead"].split()
    times = c.get("lead_times") or word_times(words, c["start"], c["hero_at"] - 0.12)
    if align == "right":
        tw = text_width(" ".join(words), lead_f) + lead_f.getSize() * 0.28 * 0  # approx
    words_reveal(cv, t, words, times, x, TOP_Y, lead_f, INK, align=align, glow=0.8, alpha=1 - ease_in_cubic(pout),
                 gap=lead_f.getSize() * 0.27)
    accent = c.get("accent")
    face = "serif" if accent else "serif_up"
    hf, lines = fit_lines(c["hero"], face, 132, 700, 2, 74)
    rgb = ACCENT if accent else WARM_SERIF
    hw = c["hero"].split()
    # per-word reveal of the keyword line(s), like "Some" -> "Some version"
    ht = c.get("hero_times") or word_times(hw, c["hero_at"] - 0.05, c["hero_at"] + 0.18 * (len(hw) - 1))
    k = 0
    for i, ln in enumerate(lines):
        y = TOP_Y + 16 + hf.getSize() * (0.88 + 0.86 * i)
        lw = ln.split()
        widths = [text_width(w, hf) for w in lw]
        gap = hf.getSize() * 0.24
        total = sum(widths) + gap * (len(lw) - 1)
        cx = x if align == "left" else x - total
        for w, wd in zip(lw, widths):
            at = ht[min(k, len(ht) - 1)]
            p = prog(t, at, 0.5)
            if p > 0:
                e = ease_out_cubic(p)
                draw_text(cv, w, cx + (1 - e) * 26, y, hf, rgb, e * (1 - ease_in_cubic(pout)), blur=(1 - e) * 12 + pout * 8,
                          tracking=(1 - e) * hf.getSize() * 0.12, glow=0.85)
            cx += wd + gap
            k += 1


def m_torso(cv, t, c, ctx):
    """r1m4: tiny lead above, huge white serif over the torso, tail below."""
    a, pin, pout = fade_of(t, c["start"], c["end"], 0.25, 0.22)
    if a <= 0:
        return
    bottom_shade(cv, a, 460, 0.42)
    cx = W / 2 + c.get("dx", 0)
    hf = font("serif" if c.get("italic") else "serif_up", c.get("size", 230))
    hw = text_width(c["hero"], hf)
    while hw > W * 0.8:
        hf = font("serif" if c.get("italic") else "serif_up", hf.getSize() * 0.9); hw = text_width(c["hero"], hf)
    yb = H - 150
    lf = font("sans_med", 36)
    lw = c["lead"].split()
    words_reveal(cv, t, lw, word_times(lw, c["start"], c["hero_at"] - 0.1), cx - hw / 2 + 14, yb - hf.getSize() * 0.74,
                 lf, WHITE, shadow=0.55, alpha=1 - ease_in_cubic(pout))
    p = prog(t, c["hero_at"] - 0.05, 0.5)
    if p > 0:
        e = ease_out_cubic(p)
        rgb = ACCENT if c.get("red") else WHITE
        draw_text(cv, c["hero"], cx, yb, hf, rgb, e * (1 - ease_in_cubic(pout)), blur=(1 - e) * 14,
                  tracking=(1 - e) * hf.getSize() * 0.1, align="center", shadow=0.45)
    if c.get("tail"):
        pt = prog(t, c.get("tail_at", c["hero_at"] + 0.4), 0.3)
        if pt > 0:
            draw_text(cv, c["tail"], cx + hw / 2 - 10, yb + 44, lf, WHITE, ease_out_cubic(pt) * (1 - ease_in_cubic(pout)),
                      align="right", shadow=0.55)


def m_chest(cv, t, c, ctx):
    """r1m7: small word / big bold sans word / small tail, white at chest, bottom darkened."""
    a, pin, pout = fade_of(t, c["start"], c["end"], 0.25, 0.22)
    if a <= 0:
        return
    bottom_shade(cv, a, 520, 0.5)
    cx = W / 2
    big = font("sans_bold", 128)
    bw = text_width(c["big"], big)
    while bw > W * 0.78:
        big = font("sans_bold", big.getSize() * 0.9); bw = text_width(c["big"], big)
    yb = H - 190
    sf = font("sans_med", 44)
    fo = 1 - ease_in_cubic(pout)
    lw = c["small"].split()
    words_reveal(cv, t, lw, word_times(lw, c["start"], c["big_at"] - 0.1), cx - bw / 2 + 6, yb - big.getSize() * 0.86,
                 sf, WHITE, shadow=0.5, alpha=fo)
    p = prog(t, c["big_at"] - 0.04, 0.35)
    if p > 0:
        e = ease_out_cubic(p)
        draw_text(cv, c["big"], cx, yb + (1 - e) * 18, big, WHITE, e * fo, blur=(1 - e) * 10, align="center", shadow=0.5)
    if c.get("tail"):
        tw = c["tail"].split()
        words_reveal(cv, t, tw, word_times(tw, c["tail_at"], c["tail_at"] + 0.3 * len(tw)), cx + bw / 2 - 6, yb + 54, sf,
                     WHITE, align="right", shadow=0.5, alpha=fo)


def m_prompt(cv, t, c, ctx):
    """r1m2: white serif word with an AI prompt bar typing underneath."""
    a, pin, pout = fade_of(t, c["start"], c["end"], 0.3, 0.25)
    if a <= 0:
        return
    bottom_shade(cv, a, 460, 0.45)
    fo = 1 - ease_in_cubic(pout)
    hf = font("serif_up", 190)
    p = prog(t, c["start"], 0.5)
    e = ease_out_cubic(p)
    draw_text(cv, c["hero"], W / 2, H - 230, hf, WHITE, e * fo, blur=(1 - e) * 12, tracking=(1 - e) * 16, align="center",
              shadow=0.4)
    pb = prog(t, c["bar_at"] - 0.1, 0.4)
    if pb > 0:
        eb = ease_out_cubic(pb)
        bw, bh = 980, 82
        bx, by = W / 2 - bw / 2, H - 190 + (1 - eb) * 40
        rrect(cv, bx, by, bw, bh, bh / 2, WHITE, eb * fo * 0.96, shadow=0.25)
        icon(cv, "auto_awesome", bx + 52, by + bh / 2, 40, (214, 160, 80), eb * fo)
        txt = c["text"]
        n = int(c01((t - c["bar_at"] - 0.15) / max(0.4, c.get("type_dur", 1.6))) * len(txt) + 0.999)
        tf_ = font("sans_med", 34)
        shown = txt[:n]
        draw_text(cv, shown, bx + 96, by + bh / 2 + 12, tf_, (90, 96, 104), eb * fo)
        if n < len(txt) and int(t * 4) % 2 == 0:
            cxp = bx + 96 + text_width(shown, tf_) + 4
            cv.drawRect(skia.Rect.MakeXYWH(cxp, by + 22, 3, bh - 44), skia.Paint(Color=col((90, 96, 104), eb * fo)))


def m_confetti(cv, t, c, ctx):
    """r1m6: small coloured shapes burst out and drift away."""
    p = (t - c["at"]) / 1.3
    if p < 0 or p > 1:
        return
    rnd = random.Random(int(c["at"] * 1000))
    cols = [ACCENT, (120, 90, 230), (40, 150, 255), (245, 180, 40), (255, 255, 255)]
    cx, cy = c.get("x", W / 2), c.get("y", H - 260)
    for i in range(64):
        ang = rnd.uniform(0, math.tau)
        sp = rnd.uniform(220, 620)
        x = cx + math.cos(ang) * sp * ease_out_cubic(p) * 1.1
        y = cy + math.sin(ang) * sp * ease_out_cubic(p) * 0.7 + 260 * p * p
        a = (1 - p) ** 1.2
        s = rnd.uniform(16, 30)
        kind = i % 3
        paint = skia.Paint(AntiAlias=True, Color=col(cols[i % len(cols)], a), StrokeWidth=6,
                           Style=skia.Paint.kStroke_Style)
        rot = p * rnd.uniform(-6, 6)
        cv.save(); cv.translate(x, y); cv.rotate(math.degrees(rot))
        if kind == 0:
            cv.drawCircle(0, 0, s * 0.6, paint)
        elif kind == 1:
            path = skia.Path(); path.moveTo(0, -s * 0.7); path.lineTo(s * 0.6, s * 0.5); path.lineTo(-s * 0.6, s * 0.5); path.close()
            cv.drawPath(path, paint)
        else:
            cv.drawLine(-s * 0.5, -s * 0.5, s * 0.5, s * 0.5, paint); cv.drawLine(s * 0.5, -s * 0.5, -s * 0.5, s * 0.5, paint)
        cv.restore()


def m_lightleak(cv, t, c, ctx):
    """r1m3: warm pink leak + exposure lift for a few frames."""
    d = c.get("dur", 0.42)
    p = (t - c["at"]) / d
    if p < 0 or p > 1:
        return
    k = math.sin(math.pi * p)
    sx = W * (-0.2 + 1.4 * p)
    for (cx, cy, r, rgb, a) in [(sx, H * 0.45, 1100, (255, 120, 170), 0.75), (sx - 300, H * 0.2, 800, (255, 190, 120), 0.6)]:
        sh = skia.GradientShader.MakeRadial(skia.Point(cx, cy), r, [col(rgb, a * k), col(rgb, 0)])
        cv.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Shader=sh, BlendMode=skia.BlendMode.kScreen))
    cv.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Color=col(WHITE, 0.45 * k), BlendMode=skia.BlendMode.kScreen))


# ================================================================== r2 motions
def m_counter_behind(cv, t, c, ctx):
    """r2m1: huge digits roll up behind the speaker; small label settles top-right. (drawn in the 'behind' pass)"""
    a, pin, pout = fade_of(t, c["start"], c["end"], 0.2, 0.25)
    if a <= 0:
        return
    p = ease_out_cubic(prog(t, c["at"] - 0.1, c.get("roll", 1.6)))
    val = c["value"] * p
    txt = c.get("prefix", "") + f"{int(val):,}"
    f = font("sans_xb", 290)
    w = text_width(txt, f, -6)
    final_w = text_width(c.get("prefix", "") + f"{c['value']:,}", f, -6)
    if final_w > W * 0.94:
        f = font("sans_xb", 290 * W * 0.94 / final_w); w = text_width(txt, f, -6); final_w = text_width(c.get("prefix", "") + f"{c['value']:,}", f, -6)
    x0 = W / 2 - final_w / 2
    y = c.get("y", 450)
    sh = skia.GradientShader.MakeLinear([skia.Point(0, y - f.getSize() * 0.75), skia.Point(0, y)],
                                        [col(INK, a), col(INK, 0.55 * a)])
    g = f.textToGlyphs(txt)
    xs, acc = [], 0.0
    for wd in f.getWidths(g):
        xs.append(acc); acc += wd - 6
    blob = skia.TextBlob.MakeFromPosTextH(txt, xs, 0, f)
    # right-align digits so they roll in place
    cv.drawTextBlob(blob, x0 + final_w - w, y, skia.Paint(AntiAlias=True, Shader=sh))
    if p > 0.97 and c.get("tag"):
        pl = prog(t, c["at"] + c.get("roll", 1.6) * 0.8, 0.3)
        draw_text(cv, c["tag"], x0 + final_w - 8, y - f.getSize() * 0.78, font("sans", 40), INK, ease_out_cubic(pl) * a,
                  align="right", glow=0.8)


def m_money_chart(cv, t, c, ctx):
    """r2m2: lilac gradient, big counter, thick line drawing with a glowing dot, optional icon cards."""
    vis = prog(t, c["start"], 0.25) * (1 - prog(t, c["end"] - 0.2, 0.2))
    if vis <= 0:
        return
    cv.save()
    s = 1.0 + 0.05 * prog(t, c["start"], c["end"] - c["start"])
    cv.translate(W / 2, H / 2); cv.scale(s, s); cv.translate(-W / 2, -H / 2)
    lilac_bg(cv, 1.0, prog(t, c["start"], 3))
    p = ease_out_cubic(prog(t, c["at"] - 0.15, 1.4))
    val = c["value"] * p
    txt = c["prefix"] + f"{int(val):,}" + (c.get("suffix", "") if p > 0.98 else "")
    nf = font("sans_xb", 190)
    sh = skia.GradientShader.MakeLinear([skia.Point(0, 230), skia.Point(0, 420)], [col((20, 20, 24)), col((95, 95, 105))])
    tw = text_width(txt, nf, -4)
    g = nf.textToGlyphs(txt); xs, acc = [], 0.0
    for wd in nf.getWidths(g):
        xs.append(acc); acc += wd - 4
    final_w = text_width(c["prefix"] + f"{c['value']:,}" + c.get("suffix", ""), nf, -4)
    cv.drawTextBlob(skia.TextBlob.MakeFromPosTextH(txt, xs, 0, nf), W / 2 - final_w / 2, 400, skia.Paint(AntiAlias=True, Shader=sh))
    # chart line
    pts = [(-40, 760), (300, 700), (560, 770), (860, 720), (1160, 600), (1440, 470), (1700, 330)]
    path = skia.Path(); path.moveTo(*pts[0])
    for i in range(1, len(pts)):
        x0, y0 = pts[i - 1]; x1, y1 = pts[i]
        path.cubicTo(x0 + (x1 - x0) * 0.5, y0, x0 + (x1 - x0) * 0.5, y1, x1, y1)
    meas = skia.PathMeasure(path, False)
    L = meas.getLength()
    pl = ease_in_out_cubic(prog(t, c["at"] - 0.25, 1.6))
    if pl > 0:
        seg = skia.Path()
        meas.getSegment(0, L * pl, seg, True)
        fillp = skia.Path(seg)
        pos = meas.getPosTan(L * pl)[0]
        fillp.lineTo(pos.x(), H + 20); fillp.lineTo(-40, H + 20); fillp.close()
        cv.drawPath(fillp, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
            [skia.Point(0, 400), skia.Point(0, H)], [col(PURPLE, 0.35), col(PURPLE, 0.0)])))
        cv.drawPath(seg, skia.Paint(AntiAlias=True, Color=col(PURPLE), Style=skia.Paint.kStroke_Style, StrokeWidth=26,
                                    StrokeCap=skia.Paint.kRound_Cap))
        cv.drawCircle(pos.x(), pos.y(), 34, skia.Paint(AntiAlias=True, Color=col((190, 110, 255), 0.6),
                                                       MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 18)))
        cv.drawCircle(pos.x(), pos.y(), 26, skia.Paint(AntiAlias=True, Color=col((176, 92, 255))))
    for card in c.get("cards", []):
        pc = prog(t, card["at"] - 0.05, 0.4)
        if pc > 0:
            sc = 0.6 + 0.4 * ease_out_back(pc)
            cx, cy = card["x"], card["y"]
            cv.save(); cv.translate(cx, cy); cv.scale(sc, sc); cv.translate(-cx, -cy)
            rrect(cv, cx - 85, cy - 95, 170, 190, 22, WHITE, ease_out_cubic(pc), shadow=0.3)
            icon(cv, card["icon"], cx, cy - 22, 74, PURPLE, ease_out_cubic(pc))
            draw_text(cv, card["text"], cx, cy + 62, font("sans", 22), INK, ease_out_cubic(pc), align="center")
            cv.restore()
    if c.get("note"):
        plb = prog(t, c.get("note_at", c["at"] + 1.0), 0.4)
        if plb > 0:
            draw_text(cv, c["note"], W / 2, 480, font("serif", 72), (60, 50, 70), ease_out_cubic(plb), align="center",
                      blur=(1 - plb) * 8)
    cv.restore()
    if vis < 1:
        pass


def m_pills(cv, t, c, ctx):
    """r2m3: white pills with ✕/✓ icons pop at four spots around the speaker, then fade out together."""
    a, pin, pout = fade_of(t, c["start"], c["end"], 0.01, 0.35)
    if a <= 0:
        return
    spots = [(120, 270, "l"), (W - 120, 270, "r"), (80, 480, "l"), (W - 80, 480, "r")]
    for i, it in enumerate(c["items"]):
        p = prog(t, it["at"] - 0.06, 0.32)
        if p <= 0:
            continue
        x, y, side = spots[i % 4]
        good = it.get("ok", c.get("ok", False))
        f = font("sans", 46)
        w = text_width(it["text"], f) + 46 * 1.3 + 46 * 2.1 * 0.62
        px = x if side == "l" else x - w
        sc = 0.5 + 0.5 * ease_out_back(p)
        fade = ease_out_cubic(p) * (1 - ease_in_cubic(pout))
        pill(cv, px, y, it["text"], size=46, alpha=fade, ic="check" if good else "close",
             ic_rgb=(52, 180, 90) if good else (226, 60, 50), scale=sc)


def m_icon_cards(cv, t, c, ctx):
    """r2m4: white icon cards pop in one by one on a lilac gradient and the row re-centres."""
    vis = prog(t, c["start"], 0.25) * (1 - prog(t, c["end"] - 0.2, 0.2))
    if vis <= 0:
        return
    cv.save()
    s = 1.0 + 0.04 * prog(t, c["start"], c["end"] - c["start"])
    cv.translate(W / 2, H / 2); cv.scale(s, s); cv.translate(-W / 2, -H / 2)
    lilac_bg(cv, 1.0)
    if c.get("title"):
        pt = prog(t, c["start"] + 0.1, 0.4)
        draw_text(cv, c["title"], W / 2, 240, font("sans_bold", 72), INK, ease_out_cubic(pt), align="center",
                  blur=(1 - pt) * 10)
    items = c["items"]
    n_on = [it for it in items if t >= it["at"] - 0.06]
    cw, gap = 290, 56
    # positions re-centre smoothly as cards arrive
    for i, it in enumerate(items):
        p = prog(t, it["at"] - 0.06, 0.38)
        if p <= 0:
            continue
        k_prev = i  # cards before this one
        cnt_now = len(n_on)
        # animate count change
        last_at = n_on[-1]["at"] if n_on else 0
        m = ease_out_cubic(prog(t, last_at - 0.06, 0.4))
        cnt = (cnt_now - 1) + m if cnt_now else 0
        total = cnt * cw + (cnt - 1) * gap if cnt > 0 else cw
        x0 = W / 2 - total / 2
        cx = x0 + i * (cw + gap) + cw / 2
        cy = 560
        sc = 0.5 + 0.5 * ease_out_back(p)
        al = ease_out_cubic(p)
        cv.save(); cv.translate(cx, cy); cv.scale(sc, sc); cv.translate(-cx, -cy)
        rrect(cv, cx - cw / 2, cy - 165, cw, 330, 36, WHITE, al, shadow=0.32)
        icon(cv, it["icon"], cx, cy - 40, 132, PURPLE, al)
        draw_text(cv, it["text"], cx, cy + 108, font("sans", 38), INK, al, align="center")
        cv.restore()
    cv.restore()


def m_karaoke(cv, t, c, ctx):
    """r2m5: words type in, the spoken word lights up; a bigger second line lands with a highlighted phrase."""
    a, pin, pout = fade_of(t, c["start"], c["end"], 0.15, 0.3)
    if a <= 0:
        return
    bottom_shade(cv, a, 380, 0.6)
    fo = 1 - ease_in_cubic(pout)
    lf = font("sans_med", 40)
    l1 = c["line1"].split()
    words_reveal(cv, t, l1, c.get("t1") or word_times(l1, c["start"], c["line2_at"] - 0.1), W / 2, H - 150, lf, WHITE,
                 align="center", shadow=0.55, alpha=fo, hl_rgb=KARAOKE, hl_now=True)
    if t >= c["line2_at"] - 0.05:
        bf = font("sans_bold", 72)
        l2 = c["line2"].split()
        hl = set(c.get("hl", []))
        times = c.get("t2") or word_times(l2, c["line2_at"], c["line2_at"] + 0.22 * len(l2))
        widths = [text_width(w, bf) for w in l2]
        gap = 18
        total = sum(widths) + gap * (len(l2) - 1)
        x = W / 2 - total / 2
        for i, (w, wd) in enumerate(zip(l2, widths)):
            p = prog(t, times[i] - 0.04, 0.25)
            if p > 0:
                e = ease_out_cubic(p)
                draw_text(cv, w, x, H - 70 + (1 - e) * 14, bf, KARAOKE if i in hl else WHITE, e * fo, blur=(1 - e) * 6,
                          shadow=0.55)
            x += wd + gap


def m_doc_cam(cv, t, c, ctx):
    """r2m6 + r2m7: frame shrinks into a circle cam over a document; highlighter sweeps each line as it is said."""
    vis = prog(t, c["start"], 0.05) * (1 - prog(t, c["end"] - 0.3, 0.3))
    if vis <= 0:
        return
    aroll = ctx["aroll"]
    pe = ease_in_out_cubic(prog(t, c["start"], 0.55))     # shrink-to-card
    cv.save()
    s = 1.0 + 0.06 * prog(t, c["start"], c["end"] - c["start"])
    cv.translate(W / 2, H * 0.3); cv.scale(s, s); cv.translate(-W / 2, -H * 0.3)
    cv.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Color=col((250, 250, 252))))
    draw_text(cv, c["title"], 200, 220, font("sans_bold", 96), (30, 34, 44), 1.0)
    draw_text(cv, c["kicker"], 204, 320, font("sans", 46), ACCENT, 1.0)
    lf = font("sans_med", 58)
    for i, ln in enumerate(c["lines"]):
        y = 460 + i * 118
        p = prog(t, ln["at"] - 0.05, 0.3)
        if p <= 0:
            continue
        ph = ease_out_cubic(prog(t, ln["at"], 0.45))
        tw = text_width(ln["text"], lf)
        if ph > 0:
            cv.drawRect(skia.Rect.MakeXYWH(250, y - 56, (tw + 56) * ph, 76), skia.Paint(Color=col((255, 232, 60), 0.95)))
        cv.drawCircle(226, y - 18, 9, skia.Paint(AntiAlias=True, Color=col((40, 44, 54))))
        draw_text(cv, ln["text"], 272, y, lf, (40, 44, 54), ease_out_cubic(p))
    cv.restore()
    # camera frame: from full screen to a circle bottom-right
    d = 380
    cx_end, cy_end = W - 330, H - 290
    if pe < 1:
        # rounded card shrinking
        w_ = W + (d - W) * pe
        h_ = H + (d - H) * pe
        cx_ = W / 2 + (cx_end - W / 2) * pe
        cy_ = H / 2 + (cy_end - H / 2) * pe
        r_ = 10 + (d / 2 - 10) * pe
    else:
        w_ = h_ = d; cx_, cy_ = cx_end, cy_end; r_ = d / 2
    rect = skia.Rect.MakeXYWH(cx_ - w_ / 2, cy_ - h_ / 2, w_, h_)
    cv.save()
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(rect.x(), rect.y() + 10, w_, h_), r_, r_),
                 skia.Paint(AntiAlias=True, Color=col((0, 0, 0), 0.25), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 16)))
    cv.clipRRect(skia.RRect.MakeRectXY(rect, r_, r_), True)
    # source region: whole frame at start, face crop at the end
    fx, fy = ctx.get("face_out", (W / 2, H * 0.36))
    cs = H * 0.72
    sx0, sy0, sw, sh_ = 0 + (fx - cs / 2) * pe, 0 + (fy - cs * 0.42) * pe, W + (cs - W) * pe, H + (cs - H) * pe
    img = skia.Image.fromarray(np.ascontiguousarray(aroll), colorType=skia.kRGBA_8888_ColorType)
    cv.drawImageRect(img, skia.Rect.MakeXYWH(sx0, sy0, sw, sh_), rect, skia.SamplingOptions(skia.FilterMode.kLinear),
                     skia.Paint(AntiAlias=True))
    cv.restore()


# ================================================================== r3 motions
def m_bignum(cv, t, c, ctx):
    """r3m1: giant number slides across the speaker, then a clean white card with the number."""
    if t < c["start"] or t > c["end"]:
        return
    if t < c["cut_at"]:
        p = ease_in_out_cubic(prog(t, c["start"], c["cut_at"] - c["start"]))
        f = font("sans_xb", 900)
        x = W * 1.05 - p * W * 0.75
        draw_text(cv, c["fly"], x, H * 0.86, f, MAROON, 0.92, tracking=-30)
        return
    p = prog(t, c["cut_at"], 0.45)
    fo = 1 - ease_in_cubic(prog(t, c["end"] - 0.2, 0.2))
    cv.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Color=col(WHITE, fo)))
    s = 1.18 - 0.18 * ease_out_cubic(p)
    cv.save(); cv.translate(W / 2, H / 2); cv.scale(s, s); cv.translate(-W / 2, -H / 2)
    draw_text(cv, c["text"], W / 2, H / 2 + 90, font("sans_xb", 290), MAROON, fo, align="center", tracking=-8)
    cv.restore()
    if c.get("sub"):
        ps = prog(t, c.get("sub_at", c["cut_at"] + 0.4), 0.35)
        draw_text(cv, c["sub"], W / 2, H / 2 + 200, font("sans", 46), (90, 60, 60), ease_out_cubic(ps) * fo, align="center")


def job_card(cv, x, y, w, h, title, company, pay, a):
    rrect(cv, x, y, w, h, 18, WHITE, a, shadow=0.2)
    rrect(cv, x, y, w, h, 18, (225, 228, 234), a, stroke=2)
    cv.drawCircle(x + 52, y + 58, 26, skia.Paint(AntiAlias=True, Color=col((214, 222, 236), a)))
    icon(cv, "work", x + 52, y + 58, 30, (90, 110, 150), a)
    draw_text(cv, company, x + 94, y + 52, font("sans", 28), (40, 44, 54), a)
    draw_text(cv, "Full-time · On-site", x + 94, y + 84, font("sans_med", 22), (130, 136, 146), a)
    draw_text(cv, title, x + 34, y + 182, font("sans_bold", 50), (24, 28, 36), a)
    for k in range(3):
        rrect(cv, x + 34, y + 224 + k * 30, w - 68 - k * 70, 14, 7, (230, 233, 238), a)
    draw_text(cv, pay, x + 34, y + h - 44, font("sans_xb", 54), (30, 120, 70), a)


def m_cards(cv, t, c, ctx):
    """r3m2: cards pop in a row on white, then a big coloured word slams on top and the cards fade back."""
    vis = prog(t, c["start"], 0.12)
    fo = 1 - ease_in_cubic(prog(t, c["end"] - 0.2, 0.2))
    if vis <= 0 or fo <= 0:
        return
    cv.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Color=col(WHITE, vis * fo)))
    ps = prog(t, c["slam_at"] - 0.04, 0.35)
    dim = 1 - 0.6 * ease_out_cubic(ps)
    cw, ch, gap = 500, 450, 56
    n = len(c["cards"])
    x0 = W / 2 - (n * cw + (n - 1) * gap) / 2
    for i, cd in enumerate(c["cards"]):
        p = prog(t, cd["at"] - 0.06, 0.35)
        if p <= 0:
            continue
        sc = 0.85 + 0.15 * ease_out_back(p)
        x = x0 + i * (cw + gap)
        y = 315 + (1 - ease_out_cubic(p)) * 40
        cv.save(); cv.translate(x + cw / 2, y + ch / 2); cv.scale(sc, sc); cv.translate(-(x + cw / 2), -(y + ch / 2))
        job_card(cv, x, y, cw, ch, cd["title"], cd["company"], cd["pay"], ease_out_cubic(p) * dim * fo)
        cv.restore()
    if ps > 0:
        s = 1.7 - 0.7 * ease_out_back(ps, 1.2)
        shake = math.sin(t * 90) * 10 * (1 - ps)
        cv.save(); cv.translate(W / 2 + shake, H / 2); cv.scale(s, s); cv.translate(-W / 2, -H / 2)
        draw_text(cv, c["slam"], W / 2, H / 2 + 110, font("sans_xb", 300), R3_SLAM, min(1, ps * 2) * fo, align="center",
                  tracking=-8)
        cv.restore()


def m_ui_card(cv, t, c, ctx):
    """r3m3: the talking head shrinks into a rounded UI card on white with copy and a button (cursor clicks it)."""
    if t < c["start"] or t > c["end"]:
        return
    aroll = ctx["aroll"]
    pe = ease_in_out_cubic(prog(t, c["start"], 0.5))
    fo = 1 - ease_in_cubic(prog(t, c["end"] - 0.25, 0.25))
    cv.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Color=col(WHITE, pe * fo)))
    cw, chh = 820, 461
    cx, cy = W / 2, 400
    w_ = W + (cw - W) * pe; h_ = H + (chh - H) * pe
    x_ = cx - w_ / 2 + (0 if pe >= 1 else (W / 2 - cx) * (1 - pe))
    y_ = (cy - chh / 2) * pe
    r_ = 28 * pe
    rect = skia.Rect.MakeXYWH(x_, y_, w_, h_)
    cv.save()
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x_, y_ + 14, w_, h_), r_, r_),
                 skia.Paint(AntiAlias=True, Color=col((0, 0, 0), 0.22 * pe * fo), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 22)))
    cv.clipRRect(skia.RRect.MakeRectXY(rect, r_, r_), True)
    img = skia.Image.fromarray(np.ascontiguousarray(aroll), colorType=skia.kRGBA_8888_ColorType)
    cv.drawImageRect(img, rect, skia.SamplingOptions(skia.FilterMode.kLinear), skia.Paint(Alphaf=fo))
    cv.restore()
    if pe >= 0.98:
        pc = prog(t, c["start"] + 0.5, 0.35)
        a = ease_out_cubic(pc) * fo
        top = cy + chh / 2 + 40
        draw_text(cv, c["brand"], W / 2 - cw / 2 + 6, top + 20, font("sans", 24), (140, 146, 156), a, tracking=2)
        draw_text(cv, c["headline"], W / 2 - cw / 2 + 4, top + 82, font("sans_bold", 56), (24, 28, 36), a)
        draw_text(cv, c["sub"], W / 2 - cw / 2 + 6, top + 132, font("sans_med", 34), (120, 126, 136), a)
        bf = font("sans_xb", 40)
        bw, bh = text_width(c["button"], bf) + 90, 84
        bx, by = W / 2 + cw / 2 - bw, top + 52
        pk = prog(t, c["click_at"] - 0.05, 0.25)
        press = 1 - 0.08 * math.sin(math.pi * pk) if 0 < pk < 1 else 1.0
        cv.save(); cv.translate(bx + bw / 2, by + bh / 2); cv.scale(press, press); cv.translate(-(bx + bw / 2), -(by + bh / 2))
        rrect(cv, bx, by, bw, bh, bh / 2, ACCENT, a, shadow=0.25)
        draw_text(cv, c["button"], bx + bw / 2, by + bh / 2 + 12, bf, WHITE, a, align="center")
        cv.restore()
        pr = prog(t, c["click_at"], 0.5)
        if 0 < pr < 1:
            cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(bx - 24 * pr, by - 24 * pr, bw + 48 * pr, bh + 48 * pr),
                                               bh / 2 + 24 * pr, bh / 2 + 24 * pr),
                         skia.Paint(AntiAlias=True, Color=col(ACCENT, (1 - pr) * 0.6 * fo), Style=skia.Paint.kStroke_Style, StrokeWidth=5))
        pm = ease_in_out_cubic(prog(t, c["start"] + 0.7, max(0.2, c["click_at"] - c["start"] - 0.8)))
        tx, ty = bx + bw * 0.7, by + bh * 0.55
        sx, sy = bx + bw + 220, by + bh + 200
        _cursor(cv, sx + (tx - sx) * pm, sy + (ty - sy) * pm, 1.2, a)


def _cursor(cv, x, y, s=1.0, alpha=1.0):
    path = skia.Path()
    pts = [(0, 0), (0, 64), (16, 49), (28, 76), (40, 71), (28, 45), (50, 45)]
    path.moveTo(x, y)
    for px, py in pts[1:]:
        path.lineTo(x + px * s, y + py * s)
    path.close()
    cv.drawPath(path, skia.Paint(AntiAlias=True, Color=col(WHITE, alpha)))
    cv.drawPath(path, skia.Paint(AntiAlias=True, Color=col(INK, alpha), Style=skia.Paint.kStroke_Style, StrokeWidth=4,
                                 StrokeJoin=skia.Paint.kRound_Join))


def m_wavy(cv, t, c, ctx):
    """r3m4: bold white words build letter by letter with a small wave, smaller tail word."""
    a, pin, pout = fade_of(t, c["start"], c["end"], 0.1, 0.22)
    if a <= 0:
        return
    bottom_shade(cv, a, 500, 0.5)
    fo = 1 - ease_in_cubic(pout)
    if c.get("lead"):
        lw = c["lead"].split()
        words_reveal(cv, t, lw, word_times(lw, c["start"], c["at"] - 0.1), W / 2, H - 330, font("sans_med", 40), WHITE,
                     align="center", shadow=0.55, alpha=fo)
    f = font("sans_xb", 120)
    txt = c["text"]
    total = text_width(txt, f, 2)
    x = W / 2 - total / 2
    dur = c.get("dur", 0.6)
    g = f.textToGlyphs(txt)
    widths = f.getWidths(g)
    for i, (ch, wd) in enumerate(zip(txt, widths)):
        at = c["at"] + dur * i / max(1, len(txt))
        p = prog(t, at - 0.02, 0.28)
        if p > 0:
            e = ease_out_back(p, 2.2)
            draw_text(cv, ch, x, H - 190 + (1 - e) * 46 + math.sin(t * 9 + i * 0.7) * 3 * (1 - p), f, WHITE,
                      min(1, p * 2) * fo, shadow=0.5)
        x += wd + 2
    if c.get("tail"):
        pt = prog(t, c["at"] + dur + 0.05, 0.3)
        draw_text(cv, c["tail"], W / 2 + total / 2 + 14, H - 190, font("sans", 40), WHITE, ease_out_cubic(pt) * fo, shadow=0.5)


def m_bars(cv, t, c, ctx):
    """r3m5: label pills, gradient bars grow from the bottom, values pop on top."""
    vis = prog(t, c["start"], 0.15)
    fo = 1 - ease_in_cubic(prog(t, c["end"] - 0.2, 0.2))
    if vis <= 0 or fo <= 0:
        return
    cv.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Color=col(WHITE, vis * fo)))
    cols_ = [(R3_BLUE_A, R3_BLUE_B), (R3_GOLD_A, R3_GOLD_B)]
    base_y = 960
    for i, b in enumerate(c["bars"]):
        cx = W / 2 + (i - 0.5) * 600
        pl = prog(t, c["start"] + 0.1 + i * 0.12, 0.35)
        if pl > 0:
            f = font("sans_bold", 46)
            pw = text_width(b["label"], f) + 80
            sc = 0.6 + 0.4 * ease_out_back(pl)
            cv.save(); cv.translate(cx, 190); cv.scale(sc, sc); cv.translate(-cx, -190)
            sh = skia.GradientShader.MakeLinear([skia.Point(cx - pw / 2, 0), skia.Point(cx + pw / 2, 0)],
                                                [col(cols_[i][0], fo), col(cols_[i][1], fo)])
            cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(cx - pw / 2, 150, pw, 84), 42, 42), skia.Paint(AntiAlias=True, Shader=sh))
            draw_text(cv, b["label"], cx, 208, f, WHITE, fo, align="center")
            cv.restore()
        pg = ease_out_cubic(prog(t, b["at"] - 0.1, 0.7))
        if pg > 0:
            hmax = b["h"]
            h = hmax * pg
            bw = 420
            sh = skia.GradientShader.MakeLinear([skia.Point(0, base_y - hmax), skia.Point(0, base_y)],
                                                [col(cols_[i][0], fo), col(cols_[i][1], fo * 0.0)])
            cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(cx - bw / 2, base_y - h, bw, h + 40), 26, 26),
                         skia.Paint(AntiAlias=True, Shader=sh))
            pv = prog(t, b["at"] + 0.3, 0.35)
            if pv > 0:
                sc = 0.6 + 0.4 * ease_out_back(pv)
                vy = base_y - h + 96
                cv.save(); cv.translate(cx, vy); cv.scale(sc, sc); cv.translate(-cx, -vy)
                draw_text(cv, b["value"], cx, vy + 14, font("sans_xb", 116), WHITE, ease_out_cubic(pv) * fo, align="center",
                          shadow=0.25)
                cv.restore()
    if c.get("caption"):
        pc = prog(t, c.get("caption_at", c["end"] - 1.5), 0.4)
        draw_text(cv, c["caption"], W / 2, 1040, font("serif", 60), (70, 76, 90), ease_out_cubic(pc) * fo, align="center")


# ================================================================== r4 motions
def scene_camera(cv, t, start, end, push=0.06):
    p = prog(t, start, max(0.1, end - start))
    s = 1.0 + push * ease_in_out_sine(p)
    cv.translate(W / 2, H / 2); cv.scale(s, s); cv.translate(-W / 2, -H / 2)


def scene_vis(t, g, fin=0.3, fout=0.25):
    return prog(t, g["start"], fin) * (1 - prog(t, g["end"] - fout, fout))


def title_words(cv, t, text, at, y, size=60, rgb=WHITE, alpha=1.0, step=0.12):
    f = font("sans_bold", size)
    words = text.split()
    times = [at + step * i for i in range(len(words))]
    total = sum(text_width(w, f) for w in words) + size * 0.28 * (len(words) - 1)
    x = W / 2 - total / 2
    for w, tt in zip(words, times):
        p = prog(t, tt, 0.4)
        wd = text_width(w, f)
        if p > 0:
            e = ease_out_cubic(p)
            draw_text(cv, w, x, y + (1 - e) * 12, f, rgb, e * alpha, blur=(1 - e) * 12)
        x += wd + size * 0.28


def m_tiles(cv, t, g, ctx):
    """r4m1: glossy icon tiles pop on foggy navy while the camera pans to each new tile."""
    vis = scene_vis(t, g)
    if vis <= 0:
        return
    P = g["params"]
    cv.save()
    navy_bg(cv, t, 1.0)
    if P.get("title"):
        title_words(cv, t, P["title"], P.get("title_at", g["start"] + 0.1), 200, 72)
    items = P["items"]
    spacing = 470
    # camera x follows the newest tile
    k = 0.0
    for i, it in enumerate(items):
        k = i * ease_in_out_cubic(prog(t, it["at"] - 0.15, 0.55)) if i else 0
        if t < it["at"] - 0.15:
            break
        cam_i = k
    cam_i = 0.0
    for i, it in enumerate(items):
        if t >= it["at"] - 0.15:
            cam_i = (i - 1) + ease_in_out_cubic(prog(t, it["at"] - 0.15, 0.55)) if i else 0.0
    cam_x = cam_i * spacing
    cy = 600
    pts = []
    for i, it in enumerate(items):
        cx = W / 2 + i * spacing - cam_x
        pts.append(cx)
    # connector line
    for i in range(1, len(items)):
        pl = prog(t, items[i]["at"] - 0.25, 0.3)
        if pl > 0:
            x0, x1 = pts[i - 1] + 150, pts[i] - 150
            line(cv, x0, cy, x0 + (x1 - x0) * ease_out_cubic(pl), cy, ICE, 4, 0.6)
    for i, it in enumerate(items):
        p = prog(t, it["at"] - 0.08, 0.4)
        if p <= 0:
            continue
        newest = all(t < o["at"] - 0.08 for o in items[i + 1:])
        focus = 1.0 if newest else 0.55
        size = 290 if newest else 210
        glass_tile(cv, pts[i], cy, size, it["icon"], it["text"], alpha=ease_out_cubic(p) * (1.0 if newest else 0.85),
                   scale=0.6 + 0.4 * ease_out_back(p), label_size=32, focus=focus)
    if P.get("strike_at"):
        ps = prog(t, P["strike_at"], 0.35)
        if ps > 0:
            x0, x1 = pts[0] - 120, pts[-1] + 120
            line(cv, x0, cy - 140, x0 + (x1 - x0) * ease_out_cubic(ps), cy + 140, ACCENT, 14, 0.95)
            line(cv, x0, cy + 140, x0 + (x1 - x0) * ease_out_cubic(prog(t, P["strike_at"] + 0.15, 0.35)), cy - 140, ACCENT, 14, 0.95)
    cv.restore()
    if vis < 1:
        cv.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Color=col(NAVY, 0)))


def m_spotlight(cv, t, g, ctx):
    """r4m2: glowing dot throws a light cone that sweeps round and lands on an icon tile."""
    vis = scene_vis(t, g)
    if vis <= 0:
        return
    P = g["params"]
    cv.save(); scene_camera(cv, t, g["start"], g["end"], 0.05)
    navy_bg(cv, t, 1.0, seed=2)
    ox, oy = W * 0.58, H * 0.66
    pa = ease_in_out_cubic(prog(t, g["start"] + 0.2, P["land_at"] - g["start"] - 0.2))
    ang = math.radians(200 + (300 - 200) * pa)
    L = 470
    tx, ty = ox + math.cos(ang) * L, oy + math.sin(ang) * L
    spread = math.radians(15)
    path = skia.Path(); path.moveTo(ox, oy)
    path.lineTo(ox + math.cos(ang - spread) * L * 1.1, oy + math.sin(ang - spread) * L * 1.1)
    path.lineTo(ox + math.cos(ang + spread) * L * 1.1, oy + math.sin(ang + spread) * L * 1.1)
    path.close()
    sh = skia.GradientShader.MakeRadial(skia.Point(ox, oy), L * 1.1, [col((120, 200, 255), 0.75), col((120, 200, 255), 0.0)])
    cv.drawPath(path, skia.Paint(AntiAlias=True, Shader=sh, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14)))
    cv.drawCircle(ox, oy, 26, skia.Paint(AntiAlias=True, Color=col((150, 220, 255), 0.6), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 16)))
    cv.drawCircle(ox, oy, 15, skia.Paint(AntiAlias=True, Color=col(WHITE)))
    pl = prog(t, P["land_at"] - 0.1, 0.4)
    glass_tile(cv, tx, ty, 230, P["icon"], P.get("tile"), alpha=0.35 + 0.65 * ease_out_cubic(pl), scale=0.8 + 0.2 * ease_out_back(pl),
               focus=0.4 + 0.6 * pl, label_size=30)
    if P.get("title"):
        title_words(cv, t, P["title"], P.get("title_at", g["start"] + 0.2), 170, 64)
    cv.restore()


def m_tree(cv, t, g, ctx):
    """r4m3: top node, lines draw down and branch to three children that pop in order."""
    vis = scene_vis(t, g)
    if vis <= 0:
        return
    P = g["params"]
    cv.save(); scene_camera(cv, t, g["start"], g["end"], 0.05)
    navy_bg(cv, t, 1.0, seed=1)
    rx, ry = W / 2, 230
    pr = prog(t, P["root"]["at"] - 0.1, 0.4)
    glass_tile(cv, rx, ry, 230, P["root"]["icon"], P["root"]["text"], alpha=ease_out_cubic(pr), scale=0.6 + 0.4 * ease_out_back(pr),
               label_size=32)
    kids = P["children"]
    xs = [W / 2 + (i - (len(kids) - 1) / 2) * 560 for i in range(len(kids))]
    bar_y, kid_y = 520, 760
    pv = prog(t, kids[0]["at"] - 0.55, 0.25)
    if pv > 0:
        line(cv, rx, ry + 175, rx, ry + 175 + (bar_y - ry - 175) * ease_out_cubic(pv), ICE, 4, 0.75)
    for i, k in enumerate(kids):
        pb = prog(t, k["at"] - 0.35, 0.25)
        if pb > 0:
            line(cv, rx, bar_y, rx + (xs[i] - rx) * ease_out_cubic(pb), bar_y, ICE, 4, 0.75)
        pd = prog(t, k["at"] - 0.15, 0.2)
        if pd > 0:
            line(cv, xs[i], bar_y, xs[i], bar_y + (kid_y - 120 - bar_y) * ease_out_cubic(pd), ICE, 4, 0.75)
        pk = prog(t, k["at"] - 0.02, 0.4)
        if pk > 0:
            glass_tile(cv, xs[i], kid_y, 210, k["icon"], k["text"], alpha=ease_out_cubic(pk), scale=0.6 + 0.4 * ease_out_back(pk),
                       label_size=30, focus=1.0 if i == len([x for x in kids if t >= x["at"]]) - 1 else 0.6)
    cv.restore()


def m_title_icons(cv, t, g, ctx):
    """r4m4: title blurs in word by word, icon tiles arrive one by one beneath it (row stays centred)."""
    vis = scene_vis(t, g)
    if vis <= 0:
        return
    P = g["params"]
    cv.save(); scene_camera(cv, t, g["start"], g["end"], 0.07)
    navy_bg(cv, t, 1.0, seed=3)
    title_words(cv, t, P["title"], P.get("title_at", g["start"] + 0.1), 380, 84)
    items = P["items"]
    on = [i for i, it in enumerate(items) if t >= it["at"] - 0.08]
    sp = 330
    if on:
        last = items[on[-1]]["at"]
        cnt = (len(on) - 1) + ease_out_cubic(prog(t, last - 0.08, 0.4))
    else:
        cnt = 0
    for i in on:
        it = items[i]
        p = prog(t, it["at"] - 0.08, 0.4)
        x = W / 2 + (i - (max(cnt, 1) - 1) / 2) * sp if cnt >= 1 else W / 2
        glass_tile(cv, x, 640, 200, it["icon"], it["text"], alpha=ease_out_cubic(p), scale=0.6 + 0.4 * ease_out_back(p),
                   label_size=26, focus=1.0 if i == on[-1] else 0.6)
    cv.restore()


def m_nodes(cv, t, g, ctx):
    """r4m5: left node, a dashed line draws across, right node pops with a caption arrow."""
    vis = scene_vis(t, g)
    if vis <= 0:
        return
    P = g["params"]
    cv.save(); scene_camera(cv, t, g["start"], g["end"], 0.06)
    navy_bg(cv, t, 1.0, seed=4)
    lx, rx, y = W * 0.25, W * 0.75, H * 0.48
    pl = prog(t, P["left"]["at"] - 0.1, 0.4)
    glass_tile(cv, lx, y, 270, P["left"]["icon"], P["left"]["text"], alpha=ease_out_cubic(pl), scale=0.6 + 0.4 * ease_out_back(pl),
               label_size=34)
    pd = prog(t, P["left"]["at"] + 0.3, max(0.3, P["right"]["at"] - P["left"]["at"] - 0.4))
    if pd > 0:
        x0, x1 = lx + 175, rx - 175
        xe = x0 + (x1 - x0) * ease_in_out_cubic(pd)
        p = skia.Paint(AntiAlias=True, Color=col(ICE, 0.8), StrokeWidth=4, Style=skia.Paint.kStroke_Style,
                       PathEffect=skia.DashPathEffect.Make([26, 18], 0))
        cv.drawLine(x0, y, xe, y, p)
    pr = prog(t, P["right"]["at"] - 0.05, 0.4)
    if pr > 0:
        glass_tile(cv, rx, y, 270, P["right"]["icon"], P["right"]["text"], alpha=ease_out_cubic(pr), scale=0.6 + 0.4 * ease_out_back(pr),
                   label_size=34)
    if P.get("caption"):
        pc = prog(t, P["caption_at"], 0.4)
        if pc > 0:
            e = ease_out_cubic(pc)
            path = skia.Path(); path.moveTo(rx - 16, y + 262); path.lineTo(rx, y + 242); path.lineTo(rx + 16, y + 262); path.close()
            cv.drawPath(path, skia.Paint(AntiAlias=True, Color=col(WHITE, e)))
            draw_text(cv, P["caption"], rx, y + 316, font("sans", 40), (220, 232, 245), e, align="center")
    if P.get("title"):
        title_words(cv, t, P["title"], P.get("title_at", g["start"] + 0.1), 200, 70)
    cv.restore()


# ================================================================== r5 motions
def m_behind_words(cv, t, c, ctx):
    """r5m1: giant words fill the frame behind the speaker (drawn in the 'behind' pass)."""
    a, pin, pout = fade_of(t, c["start"], c["end"], 0.25, 0.25)
    if a <= 0:
        return
    gap = c.get("gap", 120)
    size = c.get("size", 300)
    room = W / 2 - gap - 40
    f = font("sans_xb", size)
    while max(text_width(c["left"], f, -6), text_width(c["right"], f, -6)) > room and size > 80:
        size *= 0.94
        f = font("sans_xb", size)
    y = c.get("y", 420)
    lw, rw = text_width(c["left"], f, -6), text_width(c["right"], f, -6)
    pl = ease_out_cubic(prog(t, c["left_at"] - 0.05, 0.45))
    pr = ease_out_cubic(prog(t, c["right_at"] - 0.05, 0.45))
    fo = 1 - ease_in_cubic(pout)
    draw_text(cv, c["left"], W / 2 - gap - lw - (1 - pl) * 160, y, f, c.get("left_rgb", INK), pl * fo, blur=(1 - pl) * 18,
              tracking=-6)
    draw_text(cv, c["right"], W / 2 + gap + (1 - pr) * 160, y, f, c.get("right_rgb", INK), pr * fo, blur=(1 - pr) * 18,
              tracking=-6)


def m_behind_front(cv, t, c, ctx):
    """r5m1 front layer: the coloured second line in front of the speaker."""
    if not c.get("front"):
        return
    a, pin, pout = fade_of(t, c["start"], c["end"], 0.25, 0.25)
    if a <= 0:
        return
    p = prog(t, c["front_at"] - 0.05, 0.4)
    if p > 0:
        e = ease_out_back(p)
        f = font("sans_xb", c.get("front_size", 120))
        cv.save(); cv.translate(W / 2, H - 170); cv.scale(0.6 + 0.4 * e, 0.6 + 0.4 * e); cv.translate(-W / 2, -(H - 170))
        draw_text(cv, c["front"], W / 2, H - 140, f, c.get("front_rgb", ACCENT), min(1, p * 2) * (1 - ease_in_cubic(pout)),
                  align="center", shadow=0.45, tracking=-2)
        cv.restore()


def m_caption(cv, t, c, ctx):
    """r5m2: lower caption word by word; the keyword lands bigger in the accent colour."""
    a, pin, pout = fade_of(t, c["start"], c["end"], 0.15, 0.25)
    if a <= 0:
        return
    bottom_shade(cv, a, 330, 0.55)
    fo = 1 - ease_in_cubic(pout)
    words = c["text"].split()
    key = set(c.get("key", []))
    times = c.get("times") or word_times(words, c["start"], c.get("key_at", c["end"] - 0.6))
    sf, kf = font("sans", 44), font("sans_xb", 66)
    widths = [text_width(w, kf if i in key else sf) for i, w in enumerate(words)]
    gap = 16
    total = sum(widths) + gap * (len(words) - 1)
    x = W / 2 - total / 2
    for i, (w, wd) in enumerate(zip(words, widths)):
        at = times[i] if i < len(times) else times[-1]
        p = prog(t, at - 0.04, 0.25)
        if p > 0:
            if i in key:
                e = ease_out_back(p, 2.0)
                cv.save(); cv.translate(x + wd / 2, H - 112); cv.scale(0.6 + 0.4 * e, 0.6 + 0.4 * e); cv.translate(-(x + wd / 2), -(H - 112))
                draw_text(cv, w, x, H - 92, kf, c.get("key_rgb", CAP_HL), min(1, p * 2) * fo, shadow=0.5)
                cv.restore()
            else:
                e = ease_out_cubic(p)
                draw_text(cv, w, x, H - 96 + (1 - e) * 10, sf, WHITE, e * fo, shadow=0.55)
        x += wd + gap


def m_ring(cv, t, g, ctx):
    """r5m3: blurred frame, title, dashed ring draws round it, pills pop on the ring."""
    vis = scene_vis(t, g)
    if vis <= 0:
        return
    P = g["params"]
    bg = blurred(ctx["aroll"], 30, 0.45, tint=(120, 100, 20))
    draw_image(cv, bg, skia.Rect.MakeWH(W, H), vis)
    cv.save(); scene_camera(cv, t, g["start"], g["end"], 0.05)
    pt = prog(t, g["start"] + 0.1, 0.45)
    draw_text(cv, P["title"], W / 2, 330, font("sans_xb", 70), R5_YELLOW, ease_out_cubic(pt) * vis, align="center",
              blur=(1 - pt) * 10, tracking=1, shadow=0.35)
    pr = ease_in_out_cubic(prog(t, g["start"] + 0.3, 0.9))
    if pr > 0:
        rect = skia.Rect.MakeXYWH(W / 2 - 560, 210, 1120, 640)
        path = skia.Path(); path.addArc(rect, -90, 359.9 * pr)
        cv.drawPath(path, skia.Paint(AntiAlias=True, Color=col(R5_YELLOW, 0.9 * vis), StrokeWidth=5, Style=skia.Paint.kStroke_Style,
                                     PathEffect=skia.DashPathEffect.Make([22, 16], 0)))
    spots = [(W / 2 - 560, 560), (W / 2 + 560, 560), (W / 2, 850)]
    for i, it in enumerate(P["items"]):
        p = prog(t, it["at"] - 0.06, 0.35)
        if p <= 0:
            continue
        x, y = spots[i % 3]
        f = font("sans_bold", 40)
        w = text_width(it["text"], f) + 70
        sc = 0.5 + 0.5 * ease_out_back(p)
        cv.save(); cv.translate(x, y); cv.scale(sc, sc); cv.translate(-x, -y)
        rrect(cv, x - w / 2, y - 40, w, 80, 16, (30, 26, 10), 0.82 * vis, shadow=0.3)
        rrect(cv, x - w / 2, y - 40, w, 80, 16, R5_YELLOW, 0.9 * vis, stroke=3)
        draw_text(cv, it["text"].upper(), x, y + 14, f, WHITE, ease_out_cubic(p) * vis, align="center", tracking=1)
        cv.restore()
    cv.restore()


def m_numchips(cv, t, c, ctx):
    """r5m4: numbered square chips pop in a row beside the speaker, caption underneath."""
    a, pin, pout = fade_of(t, c["start"], c["end"], 0.2, 0.25)
    if a <= 0:
        return
    fo = 1 - ease_in_cubic(pout)
    x, align = side_x(c["side"])
    n = len(c["items"])
    s, gap = 176, 34
    total = n * s + (n - 1) * gap
    x0 = x if align == "left" else x - total
    y = 250
    if c.get("lead"):
        draw_text(cv, c["lead"], x0, y - 34, font("sans", 46), INK, ease_out_cubic(pin) * fo, glow=0.9)
    for i, it in enumerate(c["items"]):
        p = prog(t, it["at"] - 0.06, 0.35)
        if p <= 0:
            continue
        cx = x0 + i * (s + gap) + s / 2
        sc = 0.5 + 0.5 * ease_out_back(p)
        al = ease_out_cubic(p) * fo
        cv.save(); cv.translate(cx, y + s / 2); cv.scale(sc, sc); cv.translate(-cx, -(y + s / 2))
        rrect(cv, cx - s / 2, y, s, s, 22, (24, 22, 10), 0.82 * al, shadow=0.3)
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(cx - s / 2, y, s, s), 22, 22),
                     skia.Paint(AntiAlias=True, Color=col(R5_YELLOW, 0.5 * al), Style=skia.Paint.kStroke_Style, StrokeWidth=10,
                                MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 8)))
        rrect(cv, cx - s / 2, y, s, s, 22, R5_YELLOW, al, stroke=4)
        draw_text(cv, f"{i + 1:02d}", cx, y + s / 2 + 34, font("sans_xb", 92), R5_YELLOW, al, align="center")
        cv.restore()
        draw_text(cv, it["text"], cx, y + s + 62, font("sans_bold", 42), INK, al, align="center", glow=0.9)


def m_countup(cv, t, c, ctx):
    """r5m5: big accent number counts up next to the speaker with a small sub-line."""
    a, pin, pout = fade_of(t, c["start"], c["end"], 0.2, 0.25)
    if a <= 0:
        return
    fo = 1 - ease_in_cubic(pout)
    x, align = side_x(c["side"])
    p = ease_out_cubic(prog(t, c["at"] - 0.25, 0.9))
    v = int(round(c["value"] * p))
    txt = f"{v}{c['unit']}"
    nf = font("sans_xb", 190)
    if c.get("lead"):
        lw = c["lead"].split()
        bottom_shade(cv, a, 460, 0.35)
        words_reveal(cv, t, lw, word_times(lw, c["start"], c["at"] - 0.3), x, H - 360, font("sans", 46), INK,
                     align=align, glow=0.95, alpha=fo)
    pn = prog(t, c["at"] - 0.3, 0.3)
    if pn > 0:
        draw_text(cv, txt, x, H - 200, nf, R5_YELLOW, ease_out_cubic(pn) * fo, align=align, shadow=0.5, tracking=-4)
    if c.get("sub"):
        ps = prog(t, c["at"] + 0.6, 0.35)
        draw_text(cv, c["sub"], x, H - 130, font("sans", 40), WHITE, ease_out_cubic(ps) * fo, align=align, shadow=0.6)


def m_blur_list(cv, t, g, ctx):
    """r5m6: the frame blurs heavily; heading and an icon list build line by line."""
    vis = scene_vis(t, g)
    if vis <= 0:
        return
    P = g["params"]
    bg = blurred(ctx["aroll"], 34, 0.45, tint=(120, 100, 20))
    draw_image(cv, bg, skia.Rect.MakeWH(W, H), vis)
    cv.save(); scene_camera(cv, t, g["start"], g["end"], 0.04)
    pt = prog(t, g["start"] + 0.1, 0.4)
    draw_text(cv, P["title"], W / 2, 290, font("sans_bold", 84), R5_YELLOW, ease_out_cubic(pt) * vis, align="center",
              blur=(1 - pt) * 10, shadow=0.3)
    n = len(P["items"])
    for i, it in enumerate(P["items"]):
        p = prog(t, it["at"] - 0.06, 0.35)
        if p <= 0:
            continue
        e = ease_out_cubic(p)
        y = 450 + i * 140
        x = W / 2 - 420 + (1 - e) * -30
        icon(cv, it["icon"], x, y - 22, 84, R5_YELLOW, e * vis, glow=0.5)
        draw_text(cv, it["text"], x + 84, y + 6, font("sans_bold", 72), WHITE, e * vis, shadow=0.35)
    cv.restore()


# registry: name -> (fn, layer)  layer: behind | text | full | fx
TEXT_MOTIONS = {"stack": m_stack, "torso": m_torso, "chest": m_chest, "prompt": m_prompt, "pills": m_pills,
                "karaoke": m_karaoke, "wavy": m_wavy, "caption": m_caption, "numchips": m_numchips, "countup": m_countup,
                "behind_front": m_behind_front}
BEHIND_MOTIONS = {"counter_behind": m_counter_behind, "behind_words": m_behind_words}
FULL_MOTIONS = {"money_chart": m_money_chart, "icon_cards": m_icon_cards, "doc_cam": m_doc_cam, "bignum": m_bignum,
                "cards": m_cards, "ui_card": m_ui_card, "bars": m_bars, "tiles": m_tiles, "spotlight": m_spotlight,
                "tree": m_tree, "title_icons": m_title_icons, "nodes": m_nodes, "ring": m_ring, "blur_list": m_blur_list}
FX_MOTIONS = {"confetti": m_confetti, "lightleak": m_lightleak}
