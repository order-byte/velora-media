"""Render the Offscript VSL edit from the EDL.

Talking-head zoom motion (OpenCV sub-pixel warps), B-roll inserts and all motion
graphics (Skia, drawn straight into the frame buffer), encoded with ffmpeg.

Usage:
  python3 render.py --edl edl.json --raw raw.mp4 --broll DIR --start 0 --end 30 \
      --master out_master.mp4 [--preview out_720.mp4] [--stills t1,t2,... --stills-dir DIR]
"""
import argparse, bisect, json, math, os, subprocess, sys, time
import numpy as np, cv2, skia

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # sibling modules (also under python -I)
from gfx import *  # noqa: E402,F401,F403  (fonts, colours, easing, draw helpers)
import motions as MO  # noqa: E402


# ---------------------------------------------------------------- kinetic text renderers
def draw_stack(cv, t, c):
    pin, pout = env(t, c["start"], c["end"], 0.35, 0.22)
    if pout >= 1:
        return
    x, align = side_x(c["side"])
    fade = 1 - ease_in_cubic(pout)
    lead_f = font("sans", 40)
    a = ease_out_cubic(pin) * fade
    dy = (1 - ease_out_cubic(pin)) * 22 - ease_in_cubic(pout) * 12
    draw_text(cv, c["lead"], x, TOP_Y + dy, lead_f, INK, a, blur=(1 - pin) * 6 + pout * 6, tracking=0.5, align=align, glow=0.85)
    # hero
    ph = prog(t, c["hero_at"] - 0.06, 0.45)
    if ph <= 0:
        return
    hf, lines = fit_lines(c["hero"], "serif", 126, 690, 2, 72)
    rgb = ACCENT if c.get("accent") else INK
    e = ease_out_cubic(ph)
    track = (1 - e) * hf.getSize() * 0.16
    for i, ln in enumerate(lines):
        y = TOP_Y + 22 + hf.getSize() * (0.9 + 0.88 * i) + (1 - e) * 26 - ease_in_cubic(pout) * 12
        draw_text(cv, ln, x, y, hf, rgb, e * fade, blur=(1 - e) * 14 + pout * 10, tracking=track, align=align, glow=0.9)


def draw_wordlist(cv, t, c):
    pin, pout = env(t, c["start"], c["end"], 0.3, 0.22)
    if pout >= 1:
        return
    x, align = side_x(c["side"])
    fade = 1 - ease_in_cubic(pout)
    f = font("sans", 50)
    n_on = sum(1 for it in c["items"] if t >= it["at"] - 0.05)
    y = TOP_Y - 40
    for i, it in enumerate(c["items"]):
        p = prog(t, it["at"] - 0.05, 0.3)
        if p <= 0:
            break
        dim = 0.62 if i < n_on - 1 or t >= c["final_at"] - 0.05 else 1.0
        e = ease_out_cubic(p)
        dx = (1 - e) * (-28 if align == "left" else 28)
        draw_text(cv, it["text"], x + dx, y + i * 64, f, INK, e * fade * dim, blur=(1 - e) * 8, align=align, glow=0.8)
    pf = prog(t, c["final_at"] - 0.06, 0.45)
    if pf > 0:
        e = ease_out_cubic(pf)
        hf = font("serif", 134)
        draw_text(cv, c["final"], x, y + len(c["items"]) * 64 + 120 + (1 - e) * 24, hf, ACCENT, e * fade,
                  blur=(1 - e) * 14, tracking=(1 - e) * 22, align=align, glow=0.9)


def draw_marker(cv, t, c):
    pin, pout = env(t, c["start"], c["end"], 0.32, 0.2)
    if pout >= 1:
        return
    fade = 1 - ease_in_cubic(pout)
    f = font("sans_xb", 66)
    tw = text_width(c["text"], f)
    pad_x, bh = 34, 104
    bw = tw + pad_x * 2
    y = int(H * c.get("y", 0.30))
    x = SIDE_X if c["side"] == "L" else W - SIDE_X - bw
    if c.get("lead"):
        lf = font("sans", 38)
        la = ease_out_cubic(prog(t, c["start"], 0.3)) * fade
        lx, al = (x, "left") if c["side"] == "L" else (x + bw, "right")
        draw_text(cv, c["lead"], lx, y - 26, lf, INK, la, align=al, glow=0.85)
    e = ease_out_cubic(prog(t, c["start"] + 0.04, 0.32))
    s = 0.9 + 0.1 * ease_out_back(prog(t, c["start"] + 0.04, 0.4))
    cv.save()
    cx, cy = x + bw / 2, y + bh / 2
    cv.translate(cx, cy); cv.scale(s, s); cv.translate(-cx, -cy)
    # wipe from the anchored side
    if c["side"] == "L":
        clip = skia.Rect.MakeXYWH(x - 20, y - 20, (bw + 40) * e, bh + 60)
    else:
        clip = skia.Rect.MakeXYWH(x + bw + 20 - (bw + 40) * e, y - 20, (bw + 40) * e, bh + 60)
    cv.clipRect(clip)
    rrect(cv, x, y, bw, bh, 14, INK, fade, shadow=0.25)
    draw_text(cv, c["text"], x + pad_x, y + bh / 2 + 24, f, WHITE, fade)
    cv.restore()


def chip_row(cv, t, items, x, y, align, max_w, dark=False, fade=1.0, size=38):
    f = font("sans", size)
    pad, h, gap = 26, size + 36, 14
    rows, cur, cw = [], [], 0
    for it in items:
        w = text_width(it["text"], f) + pad * 2
        if cur and cw + gap + w > max_w:
            rows.append((cur, cw)); cur, cw = [], 0
        cur.append((it, w)); cw += (gap if cw else 0) + w
    if cur:
        rows.append((cur, cw))
    for r, (row, rw) in enumerate(rows):
        cx = x if align == "left" else x - rw
        for it, w in row:
            p = prog(t, it["at"] - 0.08, 0.38)
            if p > 0:
                s = 0.55 + 0.45 * ease_out_back(p)
                a = ease_out_cubic(p) * fade
                cy = y + r * (h + gap)
                cv.save()
                ox, oy = cx + w / 2, cy + h / 2
                cv.translate(ox, oy); cv.scale(s, s); cv.translate(-ox, -oy)
                if dark:
                    rrect(cv, cx, cy, w, h, h / 2, (12, 14, 16), a * 0.78)
                    draw_text(cv, it["text"], cx + pad, cy + h / 2 + size * 0.36, f, WHITE, a)
                else:
                    rrect(cv, cx, cy, w, h, h / 2, WHITE, a * 0.94, shadow=0.18)
                    draw_text(cv, it["text"], cx + pad, cy + h / 2 + size * 0.36, f, INK, a)
                cv.restore()
            cx += w + gap
    return len(rows) * (h + gap)


def draw_chips(cv, t, c):
    pin, pout = env(t, c["start"], c["end"], 0.3, 0.22)
    if pout >= 1:
        return
    fade = 1 - ease_in_cubic(pout)
    x, align = side_x(c["side"])
    lf = font("sans", 40)
    a = ease_out_cubic(pin) * fade
    draw_text(cv, c["lead"], x, TOP_Y + (1 - ease_out_cubic(pin)) * 20, lf, INK, a, blur=(1 - pin) * 6, align=align, glow=0.85)
    chip_row(cv, t, c["items"], x, TOP_Y + 34, align, 720, fade=fade, size=40)


def fmt_num(v):
    return f"{int(round(v)):,}"


def draw_counter(cv, t, c):
    pin, pout = env(t, c["start"], c["end"], 0.35, 0.22)
    if pout >= 1:
        return
    fade = 1 - ease_in_cubic(pout)
    x, align = side_x(c["side"])
    lf = font("sans", 40)
    a = ease_out_cubic(pin) * fade
    draw_text(cv, c["lead"], x, TOP_Y + (1 - ease_out_cubic(pin)) * 20, lf, INK, a, blur=(1 - pin) * 6, align=align, glow=0.85)
    first = c["steps"][0]["at"]
    pn = prog(t, first - 0.1, 0.3)
    if pn <= 0:
        return
    val, prev = 0.0, 0.0
    for st in c["steps"]:
        p = ease_out_cubic(prog(t, st["at"] - 0.1, 0.85))
        if t >= st["at"] - 0.1:
            val = prev + (st["value"] - prev) * p
        prev = st["value"]
    nf = font("sans_xb", 108)
    rgb = ACCENT if c.get("tone") == "red" else INK
    e = ease_out_cubic(pn)
    txt = c["prefix"] + fmt_num(val) + (c["suffix"] if val >= c["steps"][-1]["value"] - 1 else "")
    # keep the anchored edge still while digits roll: measure the final string for right alignment
    if align == "right":
        draw_text(cv, txt, x, TOP_Y + 150 + (1 - e) * 24, nf, rgb, e * fade, blur=(1 - e) * 12, align="right", glow=0.9,
                  tracking=-2)
    else:
        draw_text(cv, txt, x, TOP_Y + 150 + (1 - e) * 24, nf, rgb, e * fade, blur=(1 - e) * 12, glow=0.9, tracking=-2)
    last = c["steps"][-1]["at"]
    ps = prog(t, last + 0.35, 0.4)
    if ps > 0 and c.get("sub"):
        sf = font("serif", 64)
        es = ease_out_cubic(ps)
        draw_text(cv, c["sub"], x, TOP_Y + 228 + (1 - es) * 16, sf, INK, es * fade, blur=(1 - es) * 8, align=align, glow=0.85)


TEXT_DRAW = {"stack": draw_stack, "wordlist": draw_wordlist, "marker": draw_marker, "chips": draw_chips,
             "counter": draw_counter}


# ---------------------------------------------------------------- graphics
def strike(cv, x0, y, x1, p, rgb=ACCENT, width=12, alpha=1.0):
    if p > 0:
        line(cv, x0, y, x0 + (x1 - x0) * ease_out_cubic(p), y, rgb, width, alpha)


def g_offscript_title(cv, t, g):
    P = g["params"]
    pin, pout = env(t, g["start"], g["end"], 0.3, 0.25)
    if pout >= 1:
        return
    fade = 1 - ease_in_cubic(pout)
    x = SIDE_X
    # "SCRIPT" typed in screenplay Courier
    mf = font("mono", 170)
    word = "SCRIPT"
    n = int(c01((t - g["start"]) / 0.32) * len(word) + 0.999)
    y_script = 560
    shown = word[:n]
    draw_text(cv, shown, x, y_script, mf, INK, fade, glow=0.9, tracking=4)
    full_w = text_width(word, mf, 4)
    ps = prog(t, P["strike_at"] - 0.05, 0.22)
    strike(cv, x - 10, y_script - 52, x + full_w + 14, ps, width=16, alpha=fade)
    # "off" pops in red serif
    po = prog(t, P["strike_at"] - 0.02, 0.42)
    if po > 0:
        of = font("serif", 230)
        s = 0.7 + 0.3 * ease_out_back(po)
        cv.save()
        cv.translate(x + 40, y_script - 170); cv.rotate(-7); cv.scale(s, s)
        draw_text(cv, "off", 0, 0, of, ACCENT, ease_out_cubic(po) * fade, blur=(1 - po) * 10, glow=0.9)
        cv.restore()
    pw = prog(t, P["welcome_at"] - 0.05, 0.35)
    if pw > 0:
        lf = font("sans", 42)
        e = ease_out_cubic(pw)
        draw_text(cv, "welcome to", x + 6, 250 + (1 - e) * 18, lf, INK, e * fade, blur=(1 - e) * 6, tracking=1, glow=0.85)


def paper_bg(cv, a=1.0, lines=True, margin=True):
    cv.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Color=col(PAPER, a)))
    if lines:
        p = skia.Paint(AntiAlias=True, Color=col(PAPER_LINE, a * 0.9), StrokeWidth=2)
        for yy in range(150, H, 64):
            cv.drawLine(0, yy, W, yy, p)
    if margin:
        line(cv, 230, 0, 230, H, MARGIN, 3, a * 0.8, cap=False)
    # screenplay page number, top right ("1.")
    draw_text(cv, "1.", W - 150, 96, font("mono_reg", 40), INK, a * 0.55)


def page_transform(cv, t, g, slide="up"):
    """Slide the full-screen page in/out; returns visibility (0..1) or None when gone."""
    pin, pout = env(t, g["start"], g["end"], 0.42, 0.32)
    if pout >= 1 or t < g["start"]:
        return None
    e_in, e_out = ease_out_cubic(pin), ease_in_cubic(pout)
    hold = prog(t, g["start"], max(0.1, g["end"] - g["start"]))
    s = 1.0 + 0.035 * hold
    dy = (1 - e_in) * H
    dx = -e_out * W
    cv.translate(dx, dy)
    cv.translate(W / 2, H / 2); cv.rotate((1 - e_in) * 3.0); cv.scale(s, s); cv.translate(-W / 2, -H / 2)
    return 1.0


def g_script_page(cv, t, g):
    P = g["params"]
    cv.save()
    if page_transform(cv, t, g) is None:
        cv.restore(); return
    paper_bg(cv)
    hf = font("mono", 54)
    ht = P["header"]
    n = int(c01((t - g["start"] - 0.2) / 0.6) * len(ht) + 0.999)
    hx = W / 2 - text_width(ht, hf) / 2
    draw_text(cv, ht[:n], hx, 200, hf, INK, 1.0)
    if n >= len(ht):
        line(cv, hx, 218, hx + text_width(ht, hf), 218, INK, 4, 0.9, cap=False)
    sf, nf = font("mono", 62), font("mono_reg", 44)
    for i, sc in enumerate(P["scenes"]):
        y = 340 + i * 128
        k = int(c01((t - sc["at"] + 0.05) / 0.035 / max(1, len(sc["text"]))) * len(sc["text"]) + 0.999) if t >= sc["at"] - 0.05 else 0
        if k <= 0:
            continue
        draw_text(cv, f"{i + 1}", 140, y, nf, INK, 0.6, align="center")
        draw_text(cv, f"{i + 1}", W - 140, y, nf, INK, 0.6, align="center")
        draw_text(cv, sc["text"][:k], 300, y, sf, INK, 1.0)
        # caret on the line being typed
        nxt = P["scenes"][i + 1]["at"] if i + 1 < len(P["scenes"]) else P["strike_at"]
        if t < nxt and int(t * 3) % 2 == 0:
            cx = 300 + text_width(sc["text"][:k], sf) + 6
            cv.drawRect(skia.Rect.MakeXYWH(cx, y - 48, 30, 58), skia.Paint(Color=col(INK, 0.8)))
        ps = prog(t, P["strike_at"] + i * 0.07, 0.22)
        strike(cv, 280, y - 20, 320 + text_width(sc["text"], sf), ps, width=10)
    cv.restore()


def g_split(cv, t, g):
    P = g["params"]
    cv.save()
    if page_transform(cv, t, g) is None:
        cv.restore(); return
    paper_bg(cv, lines=False, margin=False)
    pd = prog(t, g["start"] + 0.2, 0.45)
    line(cv, W / 2, 140, W / 2, 140 + (H - 280) * ease_out_cubic(pd), INK, 3, 0.35, cap=False)
    tf, sf = font("sans_xb", 104), font("serif", 84)
    for side, cx, rgb in (("left", W * 0.25, INK), ("right", W * 0.75, ACCENT)):
        s = P[side]
        pt = prog(t, s["at"] - 0.06, 0.4)
        if pt > 0:
            e = ease_out_cubic(pt)
            draw_text(cv, s["title"], cx, 520 + (1 - e) * 30, tf, rgb, e, blur=(1 - e) * 12, tracking=(1 - e) * 20 + 2,
                      align="center")
        pu = prog(t, s["sub_at"] - 0.06, 0.4)
        if pu > 0:
            e = ease_out_cubic(pu)
            draw_text(cv, "= " + s["sub"], cx, 640 + (1 - e) * 20, sf, INK, e, blur=(1 - e) * 10, align="center")
    cv.restore()


def draw_x(cv, x, y, s, p, rgb=ACCENT, width=11):
    p1, p2 = prog(p, 0, 0.5), prog(p, 0.5, 0.5)
    if p1 > 0:
        line(cv, x, y, x + s * ease_out_cubic(p1), y + s * ease_out_cubic(p1), rgb, width)
    if p2 > 0:
        line(cv, x + s, y, x + s - s * ease_out_cubic(p2), y + s * ease_out_cubic(p2), rgb, width)


def g_checklist(cv, t, g):
    P = g["params"]
    cv.save()
    if page_transform(cv, t, g) is None:
        cv.restore(); return
    paper_bg(cv)
    hf = font("mono", 58)
    ht = P["header"]
    n = int(c01((t - P["header_at"] - 0.15) / 0.7) * len(ht) + 0.999)
    draw_text(cv, ht[:n], 300, 260, hf, INK, 1.0)
    rf = font("sans", 72)
    for i, r in enumerate(P["rows"]):
        y = 440 + i * 170
        p = prog(t, r["at"] - 0.06, 0.4)
        if p <= 0:
            continue
        e = ease_out_cubic(p)
        dim = 1.0 - 0.45 * prog(t, r["x_at"] + 0.2, 0.3)
        rrect(cv, 300, y - 66 + (1 - e) * 20, 84, 84, 12, INK, e * 0.9, stroke=6)
        draw_text(cv, r["text"], 440, y + (1 - e) * 20, rf, INK, e * dim, blur=(1 - e) * 10)
        px = prog(t, r["x_at"] - 0.05, 0.32)
        if px > 0:
            draw_x(cv, 318, y - 48, 48, px)
            strike(cv, 430, y - 24, 450 + text_width(r["text"], rf), prog(t, r["x_at"] + 0.12, 0.3), width=8, alpha=0.9)
    cv.restore()


def g_guarantee(cv, t, g):
    P = g["params"]
    pin, pout = env(t, g["start"], g["end"], 0.35, 0.25)
    if pout >= 1:
        return
    fade = 1 - ease_in_cubic(pout)
    x, align = side_x(P.get("side", "L"))
    lf = font("sans", 42)
    a = ease_out_cubic(pin) * fade
    draw_text(cv, "I hold your hand", x, TOP_Y, lf, INK, a, blur=(1 - pin) * 6, align=align, glow=0.85)
    ph = prog(t, P["line_at"] - 0.06, 0.45)
    if ph > 0:
        e = ease_out_cubic(ph)
        hf = font("serif", 112)
        draw_text(cv, "until you make money.", x, TOP_Y + 130 + (1 - e) * 22, hf, INK, e * fade, blur=(1 - e) * 14,
                  tracking=(1 - e) * 18, align=align, glow=0.9)
    pb = prog(t, P["badge_at"] - 0.05, 0.45)
    if pb > 0:
        bf = font("sans_xb", 40)
        bw = text_width(P["badge"], bf, 2) + 150
        bx = x if align == "left" else x - bw
        by = TOP_Y + 200
        s = 0.6 + 0.4 * ease_out_back(pb)
        cv.save()
        cv.translate(bx + bw / 2, by + 52); cv.scale(s, s); cv.translate(-(bx + bw / 2), -(by + 52))
        rrect(cv, bx, by, bw, 104, 52, INK, fade * ease_out_cubic(pb), shadow=0.25)
        # check seal
        cp = skia.Paint(AntiAlias=True, Color=col(GOLD, fade), StrokeWidth=6, Style=skia.Paint.kStroke_Style,
                        StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join)
        cv.drawCircle(bx + 62, by + 52, 28, cp)
        path = skia.Path(); path.moveTo(bx + 49, by + 53); path.lineTo(bx + 58, by + 63); path.lineTo(bx + 76, by + 42)
        cv.drawPath(path, cp)
        draw_text(cv, P["badge"], bx + 112, by + 66, bf, WHITE, fade * ease_out_cubic(pb), tracking=2)
        cv.restore()


def cursor(cv, x, y, s=1.0, alpha=1.0):
    path = skia.Path()
    pts = [(0, 0), (0, 64), (16, 49), (28, 76), (40, 71), (28, 45), (50, 45)]
    path.moveTo(x + pts[0][0] * s, y + pts[0][1] * s)
    for px, py in pts[1:]:
        path.lineTo(x + px * s, y + py * s)
    path.close()
    cv.drawPath(path, skia.Paint(AntiAlias=True, Color=col((0, 0, 0), 0.25 * alpha),
                                 MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6)))
    cv.drawPath(path, skia.Paint(AntiAlias=True, Color=col(WHITE, alpha)))
    cv.drawPath(path, skia.Paint(AntiAlias=True, Color=col(INK, alpha), Style=skia.Paint.kStroke_Style, StrokeWidth=4,
                                 StrokeJoin=skia.Paint.kRound_Join))


def g_apply_button(cv, t, g):
    P = g["params"]
    pin, pout = env(t, g["start"], g["end"], 0.35, 0.25)
    if pout >= 1:
        return
    fade = 1 - ease_in_cubic(pout)
    x = SIDE_X
    lf = font("sans", 42)
    a = ease_out_cubic(pin) * fade
    draw_text(cv, "Click below", x, TOP_Y, lf, INK, a, blur=(1 - pin) * 6, glow=0.85)
    bf = font("sans_xb", 56)
    label = "APPLY NOW  →"
    bw, bh = text_width(label, bf, 2) + 120, 132
    by = TOP_Y + 50
    pc = prog(t, P["click_at"] - 0.05, 0.25)
    press = 1 - 0.07 * math.sin(math.pi * pc) if 0 < pc < 1 else 1.0
    s = (0.6 + 0.4 * ease_out_back(pin)) * press
    cv.save()
    cv.translate(x + bw / 2, by + bh / 2); cv.scale(s, s); cv.translate(-(x + bw / 2), -(by + bh / 2))
    rrect(cv, x, by, bw, bh, bh / 2, ACCENT, a, shadow=0.3)
    draw_text(cv, label, x + 60, by + bh / 2 + 20, bf, WHITE, a, tracking=2)
    cv.restore()
    # ripple
    pr = prog(t, P["click_at"], 0.5)
    if 0 < pr < 1:
        rp = skia.Paint(AntiAlias=True, Color=col(ACCENT, (1 - pr) * 0.6 * fade), Style=skia.Paint.kStroke_Style,
                        StrokeWidth=6)
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - 30 * pr, by - 30 * pr, bw + 60 * pr, bh + 60 * pr),
                                           bh / 2 + 30 * pr, bh / 2 + 30 * pr), rp)
    # cursor glides in and clicks
    pm = ease_in_out_cubic(prog(t, g["start"] + 0.15, max(0.2, P["click_at"] - g["start"] - 0.2)))
    tx, ty = x + bw * 0.72, by + bh * 0.55
    sx, sy = x + bw + 260, by + bh + 240
    cs = 1.0 - 0.12 * (math.sin(math.pi * pc) if 0 < pc < 1 else 0)
    cursor(cv, sx + (tx - sx) * pm, sy + (ty - sy) * pm, 1.25 * cs, a)


def g_endcard(cv, t, g):
    P = g["params"]
    pin = prog(t, g["start"], 0.4)
    if pin <= 0:
        return
    e = ease_out_cubic(pin)
    cv.save()
    paper_bg(cv, a=e, lines=False, margin=False)
    lf = font("sans", 46)
    pw = prog(t, P["welcome_at"] - 0.1, 0.35)
    ew = ease_out_cubic(pw)
    draw_text(cv, "welcome to", W / 2, 360 + (1 - ew) * 16, lf, INK, ew * e, align="center", tracking=1)
    mf = font("mono", 190)
    of = font("serif", 250)
    total = text_width("off", of) + 30 + text_width("SCRIPT", mf, 4)
    x0 = W / 2 - total / 2
    po = prog(t, g["start"] + 0.05, 0.5)
    s = 0.92 + 0.08 * ease_out_back(po)
    cv.translate(W / 2, 600); cv.scale(s, s); cv.translate(-W / 2, -600)
    draw_text(cv, "off", x0, 650, of, ACCENT, ease_out_cubic(po) * e, blur=(1 - po) * 10)
    sx = x0 + text_width("off", of) + 30
    draw_text(cv, "SCRIPT", sx, 650, mf, INK, ease_out_cubic(po) * e, tracking=4)
    strike(cv, sx - 8, 650 - 58, sx + text_width("SCRIPT", mf, 4) + 10, prog(t, g["start"] + 0.35, 0.3), width=16)
    cv.restore()


GFX_DRAW = {"offscript_title": g_offscript_title, "script_page": g_script_page, "split": g_split,
            "checklist": g_checklist, "guarantee": g_guarantee, "apply_button": g_apply_button, "endcard": g_endcard}


# ---------------------------------------------------------------- video sources
class FrameReader:
    def __init__(self, path, start, dur, vf, size=(W, H)):
        cmd = ["ffmpeg", "-v", "error", "-ss", f"{start:.3f}", "-i", path, "-t", f"{dur:.3f}", "-vf", vf,
               "-f", "rawvideo", "-pix_fmt", "rgba", "-"]
        self.w, self.h = size
        self.p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=self.w * self.h * 4 * 2)
        self.last = None

    def read(self):
        n = self.w * self.h * 4
        buf = self.p.stdout.read(n)
        if len(buf) == n:
            self.last = np.frombuffer(buf, np.uint8).reshape(self.h, self.w, 4)
        return self.last

    def close(self):
        try:
            self.p.stdout.close(); self.p.kill(); self.p.wait()
        except Exception:
            pass


SPLIT_W = 1150
COVER_VF = f"fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase:flags=bicubic,crop={W}:{H},format=rgba"


class Broll:
    def __init__(self, edl, broll_dir):
        self.items = edl["broll"]
        self.dir = broll_dir
        self.active, self.reader = None, None

    def frame(self, t):
        cur = next((b for b in self.items if b["start"] <= t < b["end"]), None)
        if cur is not self.active:
            if self.reader:
                self.reader.close()
            self.reader = None
            self.active = cur
            if cur:
                if cur.get("mode") == "split":
                    pw = SPLIT_W
                    vf = f"fps={FPS},scale={pw}:{H}:force_original_aspect_ratio=increase:flags=bicubic,crop={pw}:{H},format=rgba"
                    self.reader = FrameReader(os.path.join(self.dir, cur["clip"] + ".mp4"), cur["clip_in"] + (t - cur["start"]),
                                              cur["end"] - t + 0.5, vf, size=(pw, H))
                else:
                    self.reader = FrameReader(os.path.join(self.dir, cur["clip"] + ".mp4"), cur["clip_in"] + (t - cur["start"]),
                                              cur["end"] - t + 0.5, COVER_VF)
        if not cur:
            return None, None
        f = self.reader.read()
        if f is None:
            return None, None
        if cur.get("mode") == "split":
            return f, cur
        # entry settle + slow Ken Burns (alternate push/pull per clip)
        i = self.items.index(cur)
        p = prog(t, cur["start"], cur["end"] - cur["start"])
        z = (1.0 + 0.09 * p) if i % 2 == 0 else (1.09 - 0.09 * p)
        z *= 1 + 0.10 * (1 - ease_out_cubic(prog(t, cur["start"], 0.35)))
        M = np.float32([[z, 0, W / 2 * (1 - z)], [0, z, H / 2 * (1 - z)]])
        return cv2.warpAffine(f, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT), cur


class Aroll:
    """Zoom/punch-in camera on the talking head."""

    def __init__(self, edl):
        self.shots = edl["shots"]
        self.starts = [s["start"] for s in self.shots]
        self.bumps = edl.get("bumps", [])

    def params(self, s, t):
        p = prog(t, s["start"], s["end"] - s["start"])
        z = s["z0"] + (s["z1"] - s["z0"]) * ease_in_out_sine(p)
        return z, s

    def window(self, s, z):
        fx, fy = s["cx"], s["cy"]
        off = min(250.0, (z - 1) * W / 2 * 0.95)
        fox = W / 2 - s.get("shift", 0.0) * off      # text on the left -> speaker sits right of centre
        if s.get("face_x") is not None:
            fox = s["face_x"]
        foy = H * (0.37 if z > 1.12 else 0.31)
        x0 = fx - fox / z
        y0 = fy - foy / z
        x0 = min(max(0.0, x0), W - W / z)
        y0 = min(max(0.0, y0), H - H / z)
        return x0, y0

    def transform(self, t):
        i = max(0, bisect.bisect_right(self.starts, t) - 1)
        s = self.shots[i]
        z, _ = self.params(s, t)
        x0, y0 = self.window(s, z)
        if s.get("ease_in") and i > 0 and self.shots[i - 1]["frame"] != "hidden" and t - s["start"] < 0.5:
            ps = self.shots[i - 1]
            zp = ps["z1"]
            xp, yp = self.window(ps, zp)
            k = ease_in_out_cubic((t - s["start"]) / 0.5)
            z, x0, y0 = zp + (z - zp) * k, xp + (x0 - xp) * k, yp + (y0 - yp) * k
        # pulse on hero words
        j = bisect.bisect_right(self.bumps, t) - 1
        if j >= 0 and 0 <= t - self.bumps[j] < 0.32:
            q = (t - self.bumps[j]) / 0.32
            bz = 1 + 0.03 * math.sin(math.pi * q)
            cx, cy = x0 + W / z / 2, y0 + H / z / 2
            z *= bz
            x0 = min(max(0.0, cx - W / z / 2), W - W / z)
            y0 = min(max(0.0, cy - H / z / 2), H - H / z)
        return z, x0, y0

    def face_out(self, t):
        i = max(0, bisect.bisect_right(self.starts, t) - 1)
        s = self.shots[i]
        z, x0, y0 = self.transform(t)
        return (s["cx"] - x0) * z, (s["cy"] - y0) * z

    def apply(self, frame, t):
        z, x0, y0 = self.transform(t)
        if abs(z - 1) < 1e-4 and abs(x0) < 1e-3 and abs(y0) < 1e-3:
            return frame.copy()
        M = np.float32([[z, 0, -x0 * z], [0, z, -y0 * z]])
        return cv2.warpAffine(frame, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)


def draw_broll_overlays(cv, t, b):
    has = b.get("caption") or b.get("chips")
    if not has:
        return
    pin, pout = env(t, b["start"], b["end"], 0.3, 0.15)
    fade = 1 - ease_in_cubic(pout)
    # bottom gradient for legibility
    shader = skia.GradientShader.MakeLinear([skia.Point(0, H - 380), skia.Point(0, H)],
                                            [col((0, 0, 0), 0), col((0, 0, 0), 0.62 * fade)])
    cv.drawRect(skia.Rect.MakeXYWH(0, H - 380, W, 380), skia.Paint(Shader=shader))
    y = H - 120
    if b.get("chips"):
        chip_row(cv, t, b["chips"], SIDE_X, H - 200, "left", 1200, dark=True, fade=fade, size=42)
        y = H - 230
    if b.get("caption"):
        cf = font("mono", 46)
        txt = b["caption"]
        n = int(c01((t - b["start"] - 0.1) / 0.45) * len(txt) + 0.999)
        bar_w = 60 * ease_out_cubic(prog(t, b["start"], 0.3))
        line(cv, SIDE_X, y - 16, SIDE_X + bar_w, y - 16, ACCENT, 10, fade, cap=False)
        draw_text(cv, txt[:n], SIDE_X + 84, y, cf, WHITE, fade, tracking=6, shadow=0.6)


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--edl", required=True)
    ap.add_argument("--raw", required=True)
    ap.add_argument("--broll", required=True)
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float, default=None)
    ap.add_argument("--master", default=None, help="1080p video-only output (H.264)")
    ap.add_argument("--preview", default=None, help="720p preview with audio")
    ap.add_argument("--stills", default=None, help="comma separated times; writes JPGs instead of video")
    ap.add_argument("--stills-dir", default=".")
    ap.add_argument("--mattes", default=None, help="directory with matte_*.npy from matte.py")
    a = ap.parse_args()
    edl = json.load(open(a.edl))
    end = min(a.end if a.end is not None else edl["meta"]["duration"], edl["meta"]["duration"])
    aroll, broll = Aroll(edl), Broll(edl, a.broll)
    mattes = Mattes(a.mattes)

    if a.stills:
        times = [float(x) for x in a.stills.split(",")]
        for ts in times:
            rd = FrameReader(a.raw, ts, 0.2, f"fps={FPS},format=rgba")
            src = rd.read(); rd.close()
            out = compose(src, ts, aroll, broll, edl, mattes)
            if broll.reader:
                broll.reader.close()
            broll.active, broll.reader = None, None
            cv2.imwrite(os.path.join(a.stills_dir, f"still_{ts:07.2f}.jpg"), cv2.cvtColor(out, cv2.COLOR_RGBA2BGR),
                        [cv2.IMWRITE_JPEG_QUALITY, 88])
        return

    n_frames = int(round((end - a.start) * FPS))
    reader = FrameReader(a.raw, a.start, end - a.start + 0.2, f"fps={FPS},format=rgba")
    outs = []
    if a.master:
        outs += ["-map", "0:v", "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p",
                 "-movflags", "+faststart", a.master]
    if a.preview:
        outs += ["-map", "[p]", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "24", "-maxrate", "2600k",
                 "-bufsize", "5200k", "-pix_fmt", "yuv420p", "-g", "60", "-c:a", "aac", "-b:a", "128k", "-ac", "2",
                 "-movflags", "+faststart", "-shortest", a.preview]
    enc_cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS),
               "-i", "-", "-ss", f"{a.start:.3f}", "-t", f"{end - a.start:.3f}", "-i", a.raw]
    if a.preview:
        enc_cmd += ["-filter_complex", "[0:v]scale=1280:720:flags=lanczos[p]"]
    enc = subprocess.Popen(enc_cmd + outs, stdin=subprocess.PIPE)
    t0 = time.time()
    for n in range(n_frames):
        t = a.start + n / FPS
        src = reader.read()
        if src is None:
            break
        out = compose(src, t, aroll, broll, edl, mattes)
        enc.stdin.write(out.tobytes())
        if n % 150 == 0:
            el = time.time() - t0
            print(f"[{a.start:.0f}-{end:.0f}] frame {n}/{n_frames} t={t:.1f}s {n / max(el, 1e-6):.1f} fps", flush=True)
    enc.stdin.close(); enc.wait(); reader.close()
    if broll.reader:
        broll.reader.close()
    print(f"done {a.start:.1f}-{end:.1f} in {time.time() - t0:.0f}s", flush=True)


def side_wash(cv, t, items):
    """Soft light wash behind side text so dark type reads over the busy skyline."""
    for side in ("L", "R"):
        v = 0.0
        for c in items:
            sd = c.get("side") or c.get("params", {}).get("side")
            if sd != side or not (c["start"] - 0.05 <= t <= c["end"] + 0.05):
                continue
            pin, pout = env(t, c["start"], c["end"], 0.35, 0.25)
            v = max(v, ease_out_cubic(pin) * (1 - ease_in_cubic(pout)))
        if v <= 0.01:
            continue
        x0, x1 = (0, 1080) if side == "L" else (W, W - 1080)
        sh = skia.GradientShader.MakeLinear([skia.Point(x0, 0), skia.Point(x1, 0)],
                                            [col(WHITE, 0.46 * v), col(WHITE, 0.30 * v), col(WHITE, 0)], [0, 0.45, 1])
        cv.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Shader=sh))


class Mattes:
    """Pre-computed speaker mattes (matte.py) looked up by time."""

    def __init__(self, d):
        self.items = []
        if d and os.path.isdir(d):
            for fn in sorted(os.listdir(d)):
                if fn.startswith("matte_") and fn.endswith(".npy"):
                    a, b = (float(x) for x in fn[6:-4].split("_"))
                    self.items.append((a, b, np.load(os.path.join(d, fn), mmap_mode="r")))

    def get(self, t):
        for a, b, arr in self.items:
            if a <= t < b:
                k = int(round((t - a) * FPS))
                if 0 <= k < len(arr):
                    return np.asarray(arr[k])
        return None


SIDE_TEXT = {"stack", "chips", "counter", "wordlist", "numchips"}


def draw_split(cv, t, b, panel):
    p = ease_out_cubic(prog(t, b["start"], 0.42))
    x = W - SPLIT_W * p
    cv.drawRect(skia.Rect.MakeXYWH(x - 30, 0, 30, H), skia.Paint(Shader=skia.GradientShader.MakeLinear(
        [skia.Point(x - 30, 0), skia.Point(x, 0)], [col((0, 0, 0), 0), col((0, 0, 0), 0.35)])))
    MO.draw_image(cv, panel, skia.Rect.MakeXYWH(x, 0, SPLIT_W, H))
    if b.get("word"):
        pin, pout = env(t, b["start"], b["end"], 0.3, 0.2)
        fo = 1 - ease_in_cubic(pout)
        MO.bottom_shade(cv, fo, 420, 0.45)
        wf = font("serif", 190)
        pw_ = prog(t, b.get("word_at", b["start"] + 0.2) - 0.05, 0.45)
        ww = text_width(b["word"], wf)
        if b.get("lead"):
            draw_text(cv, b["lead"], W / 2 - ww / 2 + 20, H - 250, font("sans_med", 36), WHITE,
                      ease_out_cubic(pin) * fo, shadow=0.55)
        if pw_ > 0:
            e = ease_out_cubic(pw_)
            draw_text(cv, b["word"], W / 2, H - 110, wf, ACCENT, e * fo, blur=(1 - e) * 12, tracking=(1 - e) * 18,
                      align="center", shadow=0.35)
        if b.get("tail"):
            pt = prog(t, b.get("tail_at", b["end"] - 0.6), 0.3)
            draw_text(cv, b["tail"], W / 2 + ww / 2 - 10, H - 60, font("sans_med", 34), WHITE, ease_out_cubic(pt) * fo,
                      align="right", shadow=0.55)


def compose(src, t, aroll, broll, edl, mattes):
    texts, gfx, fx = edl["texts"], edl["graphics"], edl.get("fx", [])
    a_frame = aroll.apply(src, t)                     # clean, zoomed talking head
    bf, bcur = broll.frame(t)
    split = bcur is not None and bcur.get("mode") == "split"
    frame = np.ascontiguousarray(bf if (bf is not None and not split) else a_frame.copy())
    frame[..., 3] = 255
    ctx = {"aroll": a_frame, "face_out": aroll.face_out(t)}

    def active(c):
        return c["start"] - 0.05 <= t <= c["end"] + 0.05

    surf = skia.Surface(frame, colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kPremul_AlphaType)
    cv = surf.getCanvas()
    behind = [c for c in texts if c["type"] in MO.BEHIND_MOTIONS and active(c)]
    if behind and (bf is None or split):
        for c in behind:
            MO.BEHIND_MOTIONS[c["type"]](cv, t, c, ctx)
        m = mattes.get(t)
        if m is not None:                               # put the speaker back in front of the graphics
            z, x0, y0 = aroll.transform(t)
            M = np.float32([[2 * z, 0, -x0 * z], [0, 2 * z, -y0 * z]])
            al = cv2.warpAffine(m, M, (W, H), flags=cv2.INTER_LINEAR)
            a3 = (al.astype(np.float32) * (1 / 255.0))[..., None]
            frame[..., :3] = (frame[..., :3] * (1 - a3) + a_frame[..., :3] * a3).astype(np.uint8)
    if split:
        draw_split(cv, t, bcur, bf)
    full_on = False
    for g in gfx:
        if g["fullscreen"] and g["start"] - 0.05 <= t <= g["end"] + 0.05:
            full_on = full_on or (g["start"] <= t <= g["end"])
            if g["type"] in MO.FULL_MOTIONS:
                MO.FULL_MOTIONS[g["type"]](cv, t, {**g["params"], **g}, ctx)
            else:
                GFX_DRAW[g["type"]](cv, t, g)
    if bcur is not None and not split:
        draw_broll_overlays(cv, t, bcur)
    elif not full_on and not split:
        side_wash(cv, t, [c for c in texts if c["type"] in SIDE_TEXT] + [g for g in gfx if not g["fullscreen"]])
    for c in texts:
        if not active(c):
            continue
        if c["type"] in MO.BEHIND_MOTIONS:
            if c.get("front"):
                MO.m_behind_front(cv, t, c, ctx)
        elif c["type"] in MO.TEXT_MOTIONS:
            MO.TEXT_MOTIONS[c["type"]](cv, t, c, ctx)
        else:
            TEXT_DRAW[c["type"]](cv, t, c)
    for g in gfx:
        if not g["fullscreen"] and g["start"] - 0.05 <= t <= g["end"] + 0.05:
            (MO.FULL_MOTIONS[g["type"]](cv, t, {**g["params"], **g}, ctx) if g["type"] in MO.FULL_MOTIONS else GFX_DRAW[g["type"]](cv, t, g))
    for f in fx:
        if f["at"] - 0.05 <= t <= f["at"] + 1.6:
            MO.FX_MOTIONS[f["type"]](cv, t, f, ctx)
    del cv, surf
    return frame


if __name__ == "__main__":
    main()
