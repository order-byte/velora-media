"""Word-by-word captions in the reel-1 style.

White Playfair Display for ordinary words, a big black-italic yellow gradient for
the keyword of a card, soft drop shadow under everything. Each word blurs and
rises into place when it is spoken.

A card is {"start": t0, "end": t1, "lines": [[word, ...], ...]} where each word is
{"text": str, "t": appear_time, "style": "reg" | "key" | "big" | "so"}.
"""
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT_DIR = os.path.join(os.path.dirname(__file__), "..", "fonts")
W, H = 1080, 1920

STYLES = {
    # font file, size px, fill
    "reg": ("PlayfairDisplay-Roman-400.ttf", 100, "white"),
    "big": ("PlayfairDisplay-Roman-400.ttf", 136, "white"),
    "key": ("PlayfairDisplay-Italic-900.ttf", 176, "yellow"),
    "so": ("PlayfairDisplay-Italic-700.ttf", 190, "white"),
}
REVEAL = 0.14      # seconds for a word to settle
LEAD = 0.07        # a word starts appearing this much before it is spoken
CENTER_Y = 0.68    # caption block centre: below the chin, clear of Instagram's bottom UI


def _font(name, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size)


def _sprite(text, style, theme="light"):
    """RGBA sprite of one word with its shadow (and glow for keywords).
    theme "dark": ink-coloured words with a soft light halo, for the cream B-roll scenes."""
    fname, size, fill = STYLES[style]
    font = _font(fname, size)
    l, _, r, _ = font.getbbox(text, anchor="ls")
    ascent, descent = font.getmetrics()
    pad = 40
    # every sprite shares the same baseline offset so words in a line line up
    w, h = int(r - l) + 2 * pad, ascent + descent + 2 * pad
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).text((pad - l, pad + ascent), text, font=font, fill=255, anchor="ls")
    adv = font.getlength(text)
    if fill == "yellow":
        # the reference keyword face is narrower than Playfair: condense it, and cap very long words
        sx = min(0.80, 0.70 * W / max(w - 2 * pad, 1))
        nw = int((w - 2 * pad) * sx) + 2 * pad
        mask = mask.resize((nw, h), Image.LANCZOS)
        adv *= nw / w
        w = nw
    m = np.asarray(mask).astype(np.float32) / 255

    if theme == "dark":
        ink = (205, 140, 0) if fill == "yellow" else (24, 22, 20)
        col = np.full((h, w, 3), ink, np.float32)
    elif fill == "yellow":
        g = np.linspace(0, 1, h, dtype=np.float32)[:, None]
        col = np.stack([np.full_like(g, 255) * np.ones((1, w)),
                        (246 - 50 * g) * np.ones((1, w)),
                        (60 - 60 * g) * np.ones((1, w))], -1)
    else:
        col = np.full((h, w, 3), 255, np.float32)

    shadow = np.asarray(mask.filter(ImageFilter.GaussianBlur(9))).astype(np.float32) / 255
    rgba = np.zeros((h, w, 4), np.float32)
    if theme == "dark":
        # light halo instead of a drop shadow
        rgba[..., :3] = 250
        rgba[..., 3] = np.clip(np.asarray(mask.filter(ImageFilter.GaussianBlur(7))).astype(np.float32) / 255 * 1.6, 0, 0.85)
    else:
        rgba[..., 3] = np.roll(np.roll(shadow, 7, 0), 4, 1) * 0.62
    # shadow first, then optional glow, then the letters
    if fill == "yellow" and theme != "dark":
        glow = np.asarray(mask.filter(ImageFilter.GaussianBlur(18))).astype(np.float32) / 255 * 0.45
        a = glow + rgba[..., 3] * (1 - glow)
        rgba[..., :3] = (np.array([255, 214, 0], np.float32) * glow[..., None]) / np.maximum(a, 1e-6)[..., None]
        rgba[..., 3] = a
    a = m + rgba[..., 3] * (1 - m)
    rgba[..., :3] = (col * m[..., None] + rgba[..., :3] * (rgba[..., 3] * (1 - m))[..., None]) / np.maximum(a, 1e-6)[..., None]
    rgba[..., 3] = a
    # ink extents inside the sprite, for layout
    return rgba, pad, adv, size, ascent


class CaptionTrack:
    def __init__(self, cards):
        self.cards = cards
        self.cache = {}
        self.layouts = [self._layout(c) for c in cards]

    def _get(self, text, style, theme="light"):
        k = (text, style, theme)
        if k not in self.cache:
            self.cache[k] = _sprite(text, style, theme)
        return self.cache[k]

    def _layout(self, card):
        """Position every word: lines centred, keyword lines tucked tight like the reference."""
        placed, y = [], 0.0
        line_boxes = []
        for line in card["lines"]:
            sprites = [self._get(w["text"], w["style"], card.get("theme", "light")) for w in line]
            size = max(s[3] for s in sprites)
            asc = max(s[4] for s in sprites)
            space = size * 0.24
            width = sum(s[2] for s in sprites) + space * (len(line) - 1)
            line_boxes.append((line, sprites, size, space, width, asc))
        heights = [b[2] * (0.78 if b[2] > 140 else 0.90) for b in line_boxes]
        total = sum(heights)
        y = card.get("y", CENTER_Y) * H - total / 2
        for (line, sprites, size, space, width, asc), lh in zip(line_boxes, heights):
            x = W / 2 - width / 2
            baseline = y + lh * 0.86
            for w, s in zip(line, sprites):
                placed.append((w, s, x, baseline - s[4]))
                x += s[2] + space
            y += lh
        return placed

    def render(self, t, out):
        """Composite captions active at time t onto out (H x W x 3 float 0..1)."""
        for card, placed in zip(self.cards, self.layouts):
            if not (card["start"] <= t < card["end"]):
                continue
            fade_out = np.clip((card["end"] - t) / 0.08, 0, 1)
            for w, (rgba, pad, adv, size, _asc), x, y in placed:
                k = (t - (w["t"] - LEAD)) / REVEAL
                if k <= 0:
                    continue
                k = min(k, 1.0)
                e = 1 - (1 - k) ** 3
                spr = rgba
                blur = (1 - e) * 9
                if blur > 0.5:
                    spr = cv2.GaussianBlur(spr, (0, 0), blur)
                dy = (1 - e) * 22
                alpha = e * fade_out
                self._blit(out, spr, int(round(x - pad)), int(round(y - pad + dy)), alpha)
        return out

    @staticmethod
    def _blit(out, spr, x, y, alpha):
        h, w = spr.shape[:2]
        x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
        if x0 >= x1 or y0 >= y1:
            return
        s = spr[y0 - y:y1 - y, x0 - x:x1 - x]
        a = s[..., 3:4] * alpha
        out[y0:y1, x0:x1] = out[y0:y1, x0:x1] * (1 - a) + s[..., :3] / 255 * a
