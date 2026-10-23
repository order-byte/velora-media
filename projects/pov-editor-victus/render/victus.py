"""HP Victus 15 (black, Intel/NVIDIA, B&O) textures, matched to a photo of
the owner's laptop.

- lid: thin top/side bezels, webcam top-centre, a deep chin with the grey
  Victus "V" chevron in the middle
- deck: black chassis, rear hinge bar, black keycaps with white backlit
  squared legends (Orbitron stands in for HP's gaming face), short function
  row with the power key after F12, full numpad with tall + / ENTER,
  half-height arrow cluster, touchpad under the main block, VICTUS and B&O
  marks on the palm rest

Both are flat textures. The renderer maps them onto the tracked screen plane
and the fitted deck plane, so proportions here are physical millimetres.
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(__file__)
ORBITRON = os.path.join(HERE, "fonts", "Orbitron.ttf")


def orbitron(px, weight="Bold"):
    f = ImageFont.truetype(ORBITRON, max(6, int(px)))
    f.set_variation_by_name(weight)
    return f


# ------------------------------------------------------------------ lid
DISPLAY_W, DISPLAY_H = 1920, 1080
PANEL_MM_W = 344.2
PX_PER_MM_LID = DISPLAY_W / PANEL_MM_W

# Screen-plane units are the tracked reference-frame pixels. The display keeps
# the reference laptop's top edge; the deeper Victus chin then ends exactly at
# the fitted hinge line (Y = 539.8).
PLANE_DISPLAY_Y = (-220.0, 450.0)
PLANE_PER_PX = (PLANE_DISPLAY_Y[1] - PLANE_DISPLAY_Y[0]) / DISPLAY_H
PLANE_DISPLAY_X = (-DISPLAY_W / 2 * PLANE_PER_PX, DISPLAY_W / 2 * PLANE_PER_PX)
BEZEL_TOP = round(7.0 * PX_PER_MM_LID)
BEZEL_SIDE = round(6.0 * PX_PER_MM_LID)
BEZEL_BOTTOM = round((539.8 - PLANE_DISPLAY_Y[1]) / PLANE_PER_PX)
LID_W = DISPLAY_W + 2 * BEZEL_SIDE
LID_H = DISPLAY_H + BEZEL_TOP + BEZEL_BOTTOM
DISPLAY_ORIGIN = (BEZEL_SIDE, BEZEL_TOP)


def lid_to_plane():
    """3x3 mapping lid-texture pixels -> screen-plane coordinates."""
    s = PLANE_PER_PX
    return np.array([
        [s, 0, PLANE_DISPLAY_X[0] - BEZEL_SIDE * s],
        [0, s, PLANE_DISPLAY_Y[0] - BEZEL_TOP * s],
        [0, 0, 1.0],
    ])


def victus_chevron(d, cx, top, w, h, fill):
    """The chin logo: a down-pointing chevron with thick arms (V cut from a triangle)."""
    d.polygon([(cx - w / 2, top), (cx + w / 2, top), (cx, top + h)], fill=fill)
    notch_w, notch_h = w * 0.46, h * 0.52
    d.polygon([(cx - notch_w / 2, top - 1), (cx + notch_w / 2, top - 1), (cx, top + notch_h)], fill=(11, 11, 13))


def build_lid():
    """Returns (rgb uint8 HxWx3, alpha float HxW) of the lid's front face."""
    ss = 2
    W, H = LID_W * ss, LID_H * ss
    r = round(4.0 * PX_PER_MM_LID * ss)
    a = Image.new("L", (W, H), 0)
    ImageDraw.Draw(a).rounded_rectangle([0, 0, W - 1, H - 1], radius=r, fill=255)
    yy = np.linspace(0, 1, H)[:, None, None]
    bez = np.ones((H, W, 3), np.float32) * np.array([11, 11, 13], np.float32) + yy * 3
    img = Image.fromarray(np.clip(bez, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    # rim of the lid catching a little light, brightest along the top edge
    d.rounded_rectangle([0, 0, W - 1, H - 1], radius=r, outline=(40, 40, 43), width=3 * ss)
    d.line([r, 1 * ss, W - r, 1 * ss], fill=(84, 80, 78), width=2 * ss)
    # webcam
    cx, cy = W / 2, BEZEL_TOP * ss * 0.5
    rr = 1.5 * PX_PER_MM_LID * ss
    d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=(18, 18, 22))
    rr2 = rr * 0.55
    d.ellipse([cx - rr2, cy - rr2, cx + rr2, cy + rr2], fill=(24, 26, 46))
    d.ellipse([cx - rr2 * 0.1, cy - rr2 * 0.75, cx + rr2 * 0.45, cy - rr2 * 0.2], fill=(70, 74, 100))
    # display cut-out (the renderer pastes the screen here) and the panel's edge line
    ox, oy = DISPLAY_ORIGIN
    d.rectangle([ox * ss, oy * ss, (ox + DISPLAY_W) * ss - 1, (oy + DISPLAY_H) * ss - 1], fill=(4, 4, 6))
    d.line([ox * ss, (oy + DISPLAY_H) * ss + 2 * ss, (ox + DISPLAY_W) * ss, (oy + DISPLAY_H) * ss + 2 * ss], fill=(24, 24, 27), width=2 * ss)
    # grey V chevron centred on the chin
    chin_top = (oy + DISPLAY_H) * ss
    logo_w, logo_h = 16.0 * PX_PER_MM_LID * ss, 7.0 * PX_PER_MM_LID * ss
    victus_chevron(d, W / 2, chin_top + (BEZEL_BOTTOM * ss - logo_h) * 0.46, logo_w, logo_h, (50, 50, 56))
    arr = np.array(img).astype(np.float32)
    # shade where the chin drops behind the hinge bar
    ramp = np.clip((np.arange(H) - (LID_H - 14) * ss) / (14 * ss), 0, 1)[:, None, None]
    arr *= 1 - 0.55 * ramp
    img = Image.fromarray(arr.astype(np.uint8)).resize((LID_W, LID_H), Image.LANCZOS)
    return np.array(img), np.array(a.resize((LID_W, LID_H), Image.LANCZOS)).astype(np.float32) / 255.0


# ------------------------------------------------------------------ deck
DECK_MM_W, DECK_MM_D = 360.0, 255.0
PX_PER_MM_DECK = 4
DECK_W, DECK_H = int(DECK_MM_W * PX_PER_MM_DECK), int(DECK_MM_D * PX_PER_MM_DECK)
# deck-plane units per mm; depth is calibrated against the reference laptop's key rows
U_PER_MM = PLANE_PER_PX * PX_PER_MM_LID
V_PER_MM = U_PER_MM * 0.574


def deck_to_plane():
    """3x3 mapping deck-texture pixels -> fitted deck-plane (u, v)."""
    return np.array([
        [U_PER_MM / PX_PER_MM_DECK, 0, -DECK_MM_W / 2 * U_PER_MM],
        [0, V_PER_MM / PX_PER_MM_DECK, 0],
        [0, 0, 1.0],
    ])


PITCH = 17.4
CAP_GAP = 2.2
KB_X0 = -168.3
NUM_X0 = KB_X0 + 15 * PITCH + 6.1
KB_X1 = NUM_X0 + 4 * PITCH - CAP_GAP
HINGE_BAR = 9.0
FROW_Y, FROW_H = 16.5, 8.0
ROW_Y0 = FROW_Y + FROW_H + 2.2
CAP = PITCH - CAP_GAP

FROW = ["ESC"] + [f"F{i}" for i in range(1, 13)] + ["power", "DELETE", "omen", "calc", "INSERT", "PRT SC"]
FN_ICON = {"F1": "display", "F2": "sun_lo", "F3": "sun_hi", "F4": "dual", "F5": "mute", "F6": "vol_dn",
           "F7": "vol_up", "F8": "prev", "F9": "play", "F10": "next", "F11": "kbd", "F12": "plane"}


def key_rows():
    """Yield (x_mm, y_mm, w_mm, h_mm, legend, sub, kind) for every key."""
    keys = []
    slot = (KB_X1 + CAP_GAP - KB_X0) / len(FROW)
    for i, k in enumerate(FROW):
        keys.append((KB_X0 + i * slot, FROW_Y, slot - CAP_GAP, FROW_H, k, "", "f"))

    def row(r, spec):
        x = KB_X0
        y = ROW_Y0 + r * PITCH
        for leg, w, *rest in spec:
            sub = rest[0] if rest else ""
            keys.append((x, y, w * PITCH - CAP_GAP, CAP, leg, sub, "k"))
            x += w * PITCH

    row(0, [("`", 1, "~"), ("1", 1, "!"), ("2", 1, "@"), ("3", 1, "#"), ("4", 1, "$"), ("5", 1, "%"), ("6", 1, "^"),
            ("7", 1, "&"), ("8", 1, "*"), ("9", 1, "("), ("0", 1, ")"), ("-", 1, "_"), ("=", 1, "+"), ("BACKSPACE", 2)])
    row(1, [("TAB", 1.5)] + [(c, 1) for c in "QWERTYUIOP"] + [("[", 1, "{"), ("]", 1, "}"), ("\\", 1.5, "|")])
    row(2, [("CAPS LOCK", 1.75)] + [(c, 1) for c in "ASDFGHJKL"] + [(";", 1, ":"), ("'", 1, '"'), ("ENTER", 2.25)])
    row(3, [("SHIFT", 2.25)] + [(c, 1) for c in "ZXCVBNM"] + [(",", 1, "<"), (".", 1, ">"), ("/", 1, "?"), ("RSHIFT", 2.75)])
    # bottom row: full-height modifiers, then the half-height arrow cluster
    x = KB_X0
    y = ROW_Y0 + 4 * PITCH
    for leg, w in (("CTRL", 1.1), ("FN", 1), ("win", 1), ("ALT", 1), ("", 5.9), ("ALT", 1), ("CTRL", 1)):
        keys.append((x, y, w * PITCH - CAP_GAP, CAP, leg, "", "k"))
        x += w * PITCH
    half = (CAP - 1.0) / 2
    keys.append((x, y + half + 1.0, CAP, half, "left", "", "a"))
    keys.append((x + PITCH, y, CAP, half, "up", "", "a"))
    keys.append((x + PITCH, y + half + 1.0, CAP, half, "down", "", "a"))
    keys.append((x + 2 * PITCH, y + half + 1.0, CAP, half, "right", "", "a"))
    # numpad
    nk = [[("NUM LOCK", ""), ("/", ""), ("*", ""), ("-", "")],
          [("7", "HOME"), ("8", "up"), ("9", "PG UP"), ("+", "")],
          [("4", "left"), ("5", ""), ("6", "right"), None],
          [("1", "END"), ("2", "down"), ("3", "PG DN"), ("NENTER", "")],
          [("0", "INS"), None, (".", "DEL"), None]]
    for r, cols in enumerate(nk):
        for c, item in enumerate(cols):
            if item is None:
                continue
            leg, sub = item
            w, h = CAP, CAP
            if leg == "0":
                w = 2 * PITCH - CAP_GAP
            if leg in ("+", "NENTER"):
                h = 2 * PITCH - CAP_GAP
            cx = NUM_X0 + (c if leg != "." else 2) * PITCH
            keys.append((cx, ROW_Y0 + r * PITCH, w, h, leg, sub, "n"))
    return keys


def mm(x, y):
    return ((x + DECK_MM_W / 2) * PX_PER_MM_DECK, y * PX_PER_MM_DECK)


def chevron(d, cx, cy, size, direction, col, width=2):
    s = size
    pts = {"up": [(cx - s, cy + s * 0.5), (cx, cy - s * 0.5), (cx + s, cy + s * 0.5)],
           "down": [(cx - s, cy - s * 0.5), (cx, cy + s * 0.5), (cx + s, cy - s * 0.5)],
           "left": [(cx + s * 0.5, cy - s), (cx - s * 0.5, cy), (cx + s * 0.5, cy + s)],
           "right": [(cx - s * 0.5, cy - s), (cx + s * 0.5, cy), (cx - s * 0.5, cy + s)]}[direction]
    d.line(pts, fill=col, width=width, joint="curve")


def icon(d, cx, cy, u, name, col):
    """Small function-row glyphs from primitives (u = 1 mm in texture px)."""
    w = max(1, int(u * 0.35))
    if name in ("sun_lo", "sun_hi"):
        rad = u * (0.55 if name == "sun_lo" else 0.7)
        d.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], outline=col, width=w)
        for k in range(8):
            ang = k * np.pi / 4
            r0, r1 = rad * 1.5, rad * (2.0 if name == "sun_hi" else 1.75)
            d.line([cx + r0 * np.cos(ang), cy + r0 * np.sin(ang), cx + r1 * np.cos(ang), cy + r1 * np.sin(ang)], fill=col, width=w)
    elif name == "display":
        d.rectangle([cx - 1.2 * u, cy - 0.9 * u, cx + 1.2 * u, cy + 0.7 * u], outline=col, width=w)
    elif name == "dual":
        d.rectangle([cx - 1.6 * u, cy - 0.8 * u, cx - 0.2 * u, cy + 0.7 * u], outline=col, width=w)
        d.rectangle([cx + 0.2 * u, cy - 0.8 * u, cx + 1.6 * u, cy + 0.7 * u], outline=col, width=w)
    elif name in ("mute", "vol_dn", "vol_up"):
        d.polygon([(cx - 1.4 * u, cy - 0.4 * u), (cx - 0.8 * u, cy - 0.4 * u), (cx - 0.1 * u, cy - 1.0 * u),
                   (cx - 0.1 * u, cy + 1.0 * u), (cx - 0.8 * u, cy + 0.4 * u), (cx - 1.4 * u, cy + 0.4 * u)], fill=col)
        if name == "mute":
            d.line([cx + 0.3 * u, cy - 0.5 * u, cx + 1.3 * u, cy + 0.5 * u], fill=col, width=w)
            d.line([cx + 1.3 * u, cy - 0.5 * u, cx + 0.3 * u, cy + 0.5 * u], fill=col, width=w)
        else:
            d.line([cx + 0.3 * u, cy, cx + 1.3 * u, cy], fill=col, width=w)
            if name == "vol_up":
                d.line([cx + 0.8 * u, cy - 0.5 * u, cx + 0.8 * u, cy + 0.5 * u], fill=col, width=w)
    elif name in ("prev", "next"):
        sg = -1 if name == "prev" else 1
        for k in (0, 1):
            ox = cx + sg * (k * 0.9 * u - 0.4 * u)
            d.polygon([(ox - sg * 0.7 * u, cy - 0.8 * u), (ox + sg * 0.2 * u, cy), (ox - sg * 0.7 * u, cy + 0.8 * u)], fill=col)
    elif name == "play":
        d.polygon([(cx - 1.2 * u, cy - 0.8 * u), (cx - 0.2 * u, cy), (cx - 1.2 * u, cy + 0.8 * u)], fill=col)
        d.rectangle([cx + 0.1 * u, cy - 0.8 * u, cx + 0.45 * u, cy + 0.8 * u], fill=col)
        d.rectangle([cx + 0.8 * u, cy - 0.8 * u, cx + 1.15 * u, cy + 0.8 * u], fill=col)
    elif name == "kbd":
        d.rectangle([cx - 1.3 * u, cy - 0.2 * u, cx + 1.3 * u, cy + 0.9 * u], outline=col, width=w)
        for k in (-1, 0, 1):
            d.line([cx + k * 0.8 * u, cy - 0.5 * u, cx + k * 1.0 * u, cy - 1.0 * u], fill=col, width=w)
    elif name == "plane":
        d.polygon([(cx - 1.5 * u, cy + 0.1 * u), (cx + 1.3 * u, cy - 0.25 * u), (cx + 1.6 * u, cy), (cx + 1.3 * u, cy + 0.25 * u)], fill=col)
        d.polygon([(cx - 0.1 * u, cy - 0.1 * u), (cx + 0.5 * u, cy - 0.1 * u), (cx - 0.5 * u, cy - 1.1 * u)], fill=col)
        d.polygon([(cx - 0.1 * u, cy + 0.2 * u), (cx + 0.5 * u, cy + 0.2 * u), (cx - 0.5 * u, cy + 1.2 * u)], fill=col)
    elif name == "power":
        rr = 1.0 * u
        d.arc([cx - rr, cy - rr, cx + rr, cy + rr], -60, 240, fill=col, width=w)
        d.line([cx, cy - 1.3 * u, cx, cy - 0.1 * u], fill=col, width=w)
    elif name == "omen":
        d.polygon([(cx, cy - 1.0 * u), (cx + 1.0 * u, cy), (cx, cy + 1.0 * u), (cx - 1.0 * u, cy)], fill=col)
    elif name == "calc":
        d.rectangle([cx - 0.8 * u, cy - 1.0 * u, cx + 0.8 * u, cy + 1.0 * u], outline=col, width=w)
        d.rectangle([cx - 0.45 * u, cy - 0.65 * u, cx + 0.45 * u, cy - 0.25 * u], fill=col)


def build_deck():
    """Returns (ambient, screenlit, emissive, alpha) float32 textures.

    ambient: the warm room lamp from the front (the reference shot is lit the
    same way); screenlit: cool spill from the display, scaled per frame by
    the screen's brightness; emissive: the white key backlight.
    """
    s = PX_PER_MM_DECK
    yy = (np.arange(DECK_H) / s)[:, None] * np.ones((1, DECK_W))
    xx = (np.arange(DECK_W) / s - DECK_MM_W / 2)[None, :] * np.ones((DECK_H, 1))

    alb = Image.new("RGB", (DECK_W, DECK_H), (54, 54, 58))  # black chassis
    d = ImageDraw.Draw(alb)
    em = Image.new("L", (DECK_W, DECK_H), 0)
    de = ImageDraw.Draw(em)
    bleed = Image.new("L", (DECK_W, DECK_H), 0)
    db = ImageDraw.Draw(bleed)

    # rear hinge bar with its light lower edge
    hx0, _ = mm(-150, 0)
    hx1, _ = mm(150, 0)
    d.rectangle([0, 0, DECK_W, int(4 * s)], fill=(40, 40, 44))
    d.rectangle([hx0, 0, hx1, int(HINGE_BAR * s)], fill=(30, 30, 33))
    d.line([hx0, int(HINGE_BAR * s), hx1, int(HINGE_BAR * s)], fill=(120, 120, 124), width=3)
    # keyboard well
    x0, y0 = mm(KB_X0 - 2.6, FROW_Y - 2.4)
    x1, y1 = mm(KB_X1 + 2.6, ROW_Y0 + 4 * PITCH + CAP + 2.4)
    d.rounded_rectangle([x0, y0, x1, y1], radius=int(2 * s), fill=(36, 36, 39))

    f_letter = orbitron(4.2 * s, "Bold")
    f_num = orbitron(3.6 * s, "Bold")
    # Orbitron has no ^ ~ ` | { } and a boxy @, so punctuation uses Inter
    f_sym = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", int(2.9 * s))
    f_word = orbitron(1.75 * s, "SemiBold")
    f_fn = orbitron(1.6 * s, "SemiBold")
    for kx, ky, kw, kh, leg, sub, kind in key_rows():
        px, py = mm(kx, ky)
        box = [px, py, px + kw * s, py + kh * s]
        d.rounded_rectangle(box, radius=int(1.1 * s), fill=(24, 24, 27))
        # backlight leaks out under the cap, mostly along its lower edge
        db.rounded_rectangle([box[0] - 2, box[1] - 2, box[2] + 2, box[3] + 2], radius=int(1.4 * s), outline=110, width=3)
        db.line([box[0] + 3, box[3] + 3, box[2] - 3, box[3] + 3], fill=255, width=5)
        cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
        if kind == "f":
            if leg in FN_ICON:
                icon(de, box[0] + kw * s * 0.3, cy, s, FN_ICON[leg], 255)
                de.text((box[0] + kw * s * 0.5, cy), leg, font=f_fn, fill=245, anchor="lm")
            elif leg in ("power", "omen", "calc"):
                icon(de, cx, cy, s, leg, 255)
                if leg == "power":
                    de.ellipse([cx + 2.0 * s, cy - 1.6 * s, cx + 2.6 * s, cy - 1.0 * s], fill=255)
            else:
                de.text((cx, cy), leg, font=f_fn, fill=245, anchor="mm")
            continue
        if kind == "a":
            chevron(de, cx, cy, 1.1 * s, leg, 255, width=int(0.5 * s))
            continue
        if leg == "win":
            g, q = 0.45 * s, 1.35 * s
            for i in (0, 1):
                for j in (0, 1):
                    de.rectangle([cx - q - g / 2 + i * (q + g), cy - q - g / 2 + j * (q + g),
                                  cx - g / 2 + i * (q + g), cy - g / 2 + j * (q + g)], fill=255)
        elif leg == "BACKSPACE":
            chevron(de, box[0] + 3.0 * s, cy, 0.9 * s, "left", 255, width=int(0.45 * s))
            de.text((box[0] + 5.0 * s, cy), "BACKSPACE", font=f_word, fill=240, anchor="lm")
        elif leg == "ENTER":
            de.line([box[0] + 3.0 * s, cy, box[0] + 7.0 * s, cy], fill=255, width=int(0.45 * s))
            chevron(de, box[0] + 3.2 * s, cy, 0.8 * s, "left", 255, width=int(0.45 * s))
            de.text((box[2] - 2.0 * s, cy), "ENTER", font=f_word, fill=240, anchor="rm")
        elif leg == "SHIFT":
            de.text((box[0] + 2.5 * s, cy), "SHIFT", font=f_word, fill=240, anchor="lm")
            chevron(de, box[0] + 12.5 * s, cy, 0.9 * s, "up", 255, width=int(0.45 * s))
        elif leg == "RSHIFT":
            de.text((box[0] + 2.0 * s, box[1] + 2.4 * s), "PAUSE", font=f_word, fill=225, anchor="lm")
            chevron(de, box[2] - 12.5 * s, cy, 0.9 * s, "up", 255, width=int(0.45 * s))
            de.text((box[2] - 2.5 * s, cy), "SHIFT", font=f_word, fill=240, anchor="rm")
        elif leg == "TAB":
            de.text((box[0] + 2.5 * s, cy), "TAB", font=f_word, fill=240, anchor="lm")
        elif leg == "NENTER":
            de.text((cx, cy), "ENTER", font=f_word, fill=240, anchor="mm")
        elif leg == "NUM LOCK":
            de.text((cx, cy - 1.1 * s), "NUM", font=f_word, fill=240, anchor="mm")
            de.text((cx, cy + 1.1 * s), "LOCK", font=f_word, fill=240, anchor="mm")
        elif len(leg) > 1:  # CAPS LOCK, CTRL, FN, ALT
            anchor_x = box[0] + 2.5 * s if kw > 1.3 * PITCH else cx
            de.text((anchor_x, cy), leg, font=f_word, fill=240, anchor="lm" if kw > 1.3 * PITCH else "mm")
        elif kind == "n":
            de.text((cx, cy - (1.2 * s if sub else 0)), leg, font=f_num, fill=255, anchor="mm")
            if sub in ("up", "down", "left", "right"):
                chevron(de, cx, cy + 2.6 * s, 0.7 * s, sub, 235, width=int(0.4 * s))
            elif sub:
                de.text((cx, cy + 2.7 * s), sub, font=f_word, fill=225, anchor="mm")
        elif sub:  # symbol over number / punctuation
            de.text((box[0] + 3.0 * s, box[1] + 3.2 * s), sub, font=f_sym, fill=230, anchor="mm")
            de.text((cx + 1.0 * s, cy + 1.0 * s), leg, font=f_num if leg.isdigit() else f_sym, fill=255, anchor="mm")
        elif leg:
            de.text((cx - 1.2 * s, cy), leg, font=f_letter, fill=255, anchor="mm")

    # touchpad under the main block
    tcx = KB_X0 + 7.5 * PITCH + 8.0
    ty0 = ROW_Y0 + 4 * PITCH + CAP + 12.0
    t0, t1 = mm(tcx - 64, ty0), mm(tcx + 64, ty0 + 80)
    d.rounded_rectangle([t0[0] - 3, t0[1] - 3, t1[0] + 3, t1[1] + 3], radius=int(3 * s), fill=(78, 78, 82))
    d.rounded_rectangle([t0[0], t0[1], t1[0], t1[1]], radius=int(3 * s), fill=(44, 44, 48))
    # palm-rest marks: VICTUS bottom-left, B&O bottom-right, Intel / NVIDIA stickers
    f_brand = orbitron(4.0 * s, "Regular")
    bx, by = mm(-171, ty0 + 38)
    for ch in "VICTUS":
        d.text((bx, by), ch, font=f_brand, fill=(150, 150, 156), anchor="lm")
        bx += d.textlength(ch, font=f_brand) + 2.2 * s
    f_bo = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(6 * s))
    ox, oy = mm(152, ty0 + 30)
    d.text((ox, oy), "B&O", font=f_bo, fill=(150, 150, 156), anchor="mm")
    sx, sy = mm(118, DECK_MM_D - 22)
    d.rectangle([sx, sy, sx + 16 * s, sy + 18 * s], fill=(40, 90, 190))
    d.rectangle([sx + 20 * s, sy, sx + 38 * s, sy + 18 * s], fill=(110, 180, 40))
    d.rectangle([sx + 21 * s, sy + 1 * s, sx + 37 * s, sy + 12 * s], fill=(30, 30, 32))

    alb = np.array(alb).astype(np.float32) / 255.0
    rng = np.random.default_rng(7)
    alb *= 1 + rng.normal(0, 0.02, alb.shape[:2])[:, :, None]

    # warm lamp from the front, falling off towards the hinge (as in the reference shot)
    lamp = np.clip((yy - 18) / 95, 0, 1) ** 1.6
    lamp *= 1 - 0.18 * np.clip(np.abs(xx) / 180, 0, 1) ** 2
    ambient = alb * lamp[:, :, None] * np.array([235, 215, 185], np.float32)
    # cool spill from the display, strongest near the hinge
    spill = np.exp(-yy / 45.0) * 0.9 + 0.1
    screenlit = alb * spill[:, :, None] * np.array([90, 100, 125], np.float32)

    leg = np.array(em.filter(ImageFilter.GaussianBlur(0.6))).astype(np.float32) / 255.0
    glow = np.array(em.filter(ImageFilter.GaussianBlur(5))).astype(np.float32) / 255.0
    bl = np.array(bleed.filter(ImageFilter.GaussianBlur(3))).astype(np.float32) / 255.0
    emis = (leg * 1.0 + glow * 0.30 + bl * 0.55)[:, :, None] * np.array([232, 238, 255], np.float32)
    alpha = np.ones((DECK_H, DECK_W), np.float32)
    return ambient, screenlit, emis, alpha
