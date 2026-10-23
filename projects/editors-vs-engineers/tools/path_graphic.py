"""'The right path' animation, drawn in the style of reel 1's smiley scenes.

Replaces reel 1's photo montage under "so you can trust that you choose the
right path": a yellow smiley stands at a fork in the road, a signpost pops up
(9 TO 5 / EDITING), EDITING lights up, the smiley sets off down that road and
"THE RIGHT PATH" lands on the words.
"""
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
FONT_DIR = os.path.join(os.path.dirname(__file__), "..", "fonts")
INK = (28, 26, 24)
YELLOW = (250, 200, 78)
ROAD = (34, 32, 30)


def _ease(k):
    k = min(max(k, 0.0), 1.0)
    return k * k * (3 - 2 * k)


def _pop(k):
    """0 -> overshoot -> 1 over k in [0, 1]."""
    k = min(max(k, 0.0), 1.0)
    return 1 + 0.12 * np.sin(np.pi * k) - (1 - k) ** 3


def _background():
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((x - 540) / 900) ** 2 + ((y - 900) / 1100) ** 2)
    c0, c1 = np.array([247, 241, 231], np.float32), np.array([176, 164, 140], np.float32)
    k = np.clip(r, 0, 1)[..., None] ** 1.3
    img = c0 * (1 - k) + c1 * k
    low = np.clip((y - 1450) / 470, 0, 1)[..., None] ** 1.4
    img = img * (1 - 0.6 * low) + np.array([70, 66, 58], np.float32) * 0.6 * low
    return img


def _branch(p0, p1, p2, n=60):
    """Quadratic curve points."""
    t = np.linspace(0, 1, n)[:, None]
    return (1 - t) ** 2 * np.array(p0) + 2 * (1 - t) * t * np.array(p1) + t ** 2 * np.array(p2)


def _road_poly(center, w0, w1):
    d = np.gradient(center, axis=0)
    nrm = np.stack([-d[:, 1], d[:, 0]], 1)
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-6
    w = np.linspace(w0, w1, len(center))[:, None] / 2
    return np.concatenate([center + nrm * w, (center - nrm * w)[::-1]])


class PathGraphic:
    def __init__(self, duration, t_trust, t_choose, t_right):
        self.d, self.t_trust, self.t_choose, self.t_right = duration, t_trust, t_choose, t_right
        self.f_board = ImageFont.truetype(os.path.join(FONT_DIR, "GochiHand-Regular.ttf"), 60)
        self.f_title = ImageFont.truetype(os.path.join(FONT_DIR, "GochiHand-Regular.ttf"), 150)
        self.trunk = _branch((540, 1990), (540, 1500), (540, 1170))
        self.left = _branch((540, 1170), (470, 930), (170, 760))
        self.right = _branch((540, 1170), (610, 930), (910, 760))
        self.bg = self._static()

    def _static(self):
        img = Image.fromarray(_background().astype(np.uint8)).convert("RGBA")
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        for c, w0, w1 in ((self.trunk, 430, 190), (self.left, 190, 70), (self.right, 190, 70)):
            poly = [tuple(p) for p in _road_poly(c, w0, w1)]
            sh = [(x + 12, y + 10) for x, y in poly]
            d.polygon(sh, fill=YELLOW + (255,))            # the yellow offset edge of reel 1's boxes
        for c, w0, w1 in ((self.trunk, 430, 190), (self.left, 190, 70), (self.right, 190, 70)):
            d.polygon([tuple(p) for p in _road_poly(c, w0, w1)], fill=ROAD + (255,))
        for c, w0, w1 in ((self.trunk, 16, 9), (self.left, 9, 4), (self.right, 9, 4)):
            pts = c[3:-3]
            for i in range(0, len(pts) - 4, 6):        # dashed centre line
                d.line([tuple(pts[i]), tuple(pts[i + 3])], fill=(236, 226, 200, 230),
                       width=int(np.interp(i, [0, len(pts)], [w0, w1])))
        shadow = layer.split()[3].filter(ImageFilter.GaussianBlur(14))
        soft = Image.new("RGBA", (W, H), (40, 34, 26, 0))
        soft.putalpha(shadow.point(lambda v: int(v * 0.35)))
        img = Image.alpha_composite(img, soft)
        return Image.alpha_composite(img, layer)

    def _board(self, text, fill, ink, point_right, glow=0.0):
        tw = int(self.f_board.getlength(text))
        bw, bh = tw + 96, 96
        im = Image.new("RGBA", (bw + 60, bh + 60), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        x0, y0 = 30, 30
        if point_right:
            poly = [(x0, y0), (x0 + bw - 46, y0), (x0 + bw, y0 + bh / 2), (x0 + bw - 46, y0 + bh), (x0, y0 + bh)]
        else:
            poly = [(x0 + 46, y0), (x0 + bw, y0), (x0 + bw, y0 + bh), (x0 + 46, y0 + bh), (x0, y0 + bh / 2)]
        d.polygon([(x + 8, y + 9) for x, y in poly], fill=(20, 18, 16, 150))
        d.polygon(poly, fill=fill + (255,))
        tx = x0 + (30 if point_right else 70) + 8
        d.text((tx, y0 + bh / 2 + 4), text, font=self.f_board, fill=ink + (255,), anchor="lm")
        if glow > 0:
            g = im.split()[3].filter(ImageFilter.GaussianBlur(22)).point(lambda v: int(v * glow * 0.7))
            halo = Image.new("RGBA", im.size, YELLOW + (0,))
            halo.putalpha(g)
            im = Image.alpha_composite(halo, im)
        return im

    def _smiley(self, scale):
        s = scale
        size = int(380 * s) + 4
        im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        body = np.zeros((size, size, 4), np.float32)
        yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
        cx, base = size / 2, size - 2
        bw, bh = 120 * s, 205 * s
        inside = ((xx - cx) / bw) ** 2 + ((yy - base) / bh) ** 2 <= 1
        g = np.clip((yy - (base - bh)) / bh, 0, 1)
        col = np.array([252, 196, 70], np.float32) * (1 - g[..., None] ** 2) + np.array([255, 236, 190], np.float32) * g[..., None] ** 2
        body[..., :3] = col
        body[..., 3] = inside * (1 - np.clip((g - 0.7) / 0.3, 0, 1) ** 1.5) * 255   # fades out, not to white
        im = Image.fromarray(body.astype(np.uint8), "RGBA")
        # soft contact shadow on the road
        sh = Image.new("L", im.size, 0)
        ImageDraw.Draw(sh).ellipse([cx - bw * 1.05, base - 26 * s, cx + bw * 1.05, base + 4 * s], fill=120)
        sh = sh.filter(ImageFilter.GaussianBlur(10 * s + 1))
        shadow = Image.new("RGBA", im.size, (0, 0, 0, 0))
        shadow.putalpha(sh)
        im = Image.alpha_composite(shadow, im)
        d = ImageDraw.Draw(im)
        hr, hy = 64 * s, base - bh - 74 * s
        d.ellipse([cx - hr, hy - hr, cx + hr, hy + hr], fill=(254, 222, 120, 255))
        e = 9 * s
        for ex in (-22 * s, 22 * s):
            d.ellipse([cx + ex - e, hy - 12 * s - e, cx + ex + e, hy - 12 * s + e], fill=INK + (255,))
        d.arc([cx - 30 * s, hy - 6 * s, cx + 30 * s, hy + 30 * s], 20, 160, fill=INK + (255,), width=max(2, int(5 * s)))
        return im

    def render(self, t):
        img = self.bg.copy()
        # the smiley walks off down the EDITING road (drawn first: the signpost stands in front of it)
        walk = _ease((t - self.t_choose) / max(self.d - self.t_choose, 0.3))
        path = np.concatenate([self.trunk[30:], self.right[1:34]])
        idx = walk * (len(path) - 1)
        i = int(idx)
        a_, b_ = path[min(i, len(path) - 1)], path[min(i + 1, len(path) - 1)]
        pos = a_ + (b_ - a_) * (idx - i)
        scale = 1.12 - 0.45 * walk
        pos = pos + np.array([0, -abs(np.sin(walk * np.pi * 5)) * 16 * scale])   # a little hop per step
        sm = self._smiley(scale)
        img.alpha_composite(sm, (int(pos[0] - sm.width / 2), int(pos[1] - sm.height + 20)))
        # signpost pops up on "trust"
        k = (t - self.t_trust) / 0.3
        if k > 0:
            sc = _pop(k)
            lit = _ease((t - self.t_choose) / 0.2)
            post = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            d = ImageDraw.Draw(post)
            d.rectangle([236, 760, 252, 1330], fill=(46, 40, 34, 255))    # on the verge, left of the road
            left = self._board("9 TO 5", (214, 206, 192), (70, 64, 58), False)
            right_fill = tuple(int(a + (b - a) * lit) for a, b in zip((44, 42, 40), YELLOW))
            right_ink = tuple(int(a + (b - a) * lit) for a, b in zip(YELLOW, INK))
            right = self._board("EDITING", right_fill, right_ink, True, glow=lit)
            post.alpha_composite(left, (252 - left.width + 30, 742))
            post.alpha_composite(right, (236 - 30, 848))
            if sc != 1:
                post = post.resize((int(W * sc), int(H * sc)), Image.BICUBIC)
                ox, oy = int(244 * sc - 244), int(1330 * sc - 1330)
                post = post.crop((ox, oy, ox + W, oy + H))
            img = Image.alpha_composite(img, post)
        # the title lands on "right path"
        k = (t - self.t_right) / 0.28
        if k > 0:
            title = Image.new("RGBA", (W, 420), (0, 0, 0, 0))
            d = ImageDraw.Draw(title)
            d.text((W / 2, 150), "THE RIGHT", font=self.f_title, fill=INK + (255,), anchor="mm")
            d.text((W / 2, 300), "PATH", font=self.f_title, fill=INK + (255,), anchor="mm")
            u = _ease((t - self.t_right - 0.15) / 0.3)
            if u > 0:
                x1 = 330 + (750 - 330) * u
                d.line([(330, 380), (x1, 372)], fill=YELLOW + (255,), width=16)
            sc = _pop(k)
            tw, th = int(W * sc), int(420 * sc)
            title = title.resize((tw, th), Image.BICUBIC)
            img.alpha_composite(title, (int(540 - tw / 2), int(390 - th / 2)))
        out = np.asarray(img.convert("RGB")).astype(np.float32) / 255
        # entrance: a quick settle-in zoom like reel 1's scene changes
        z = 1.06 - 0.06 * _ease(t / 0.3)
        if z > 1.0005:
            m = np.array([[z, 0, (1 - z) * 540], [0, z, (1 - z) * 960]], np.float32)
            out = cv2.warpAffine(out, m, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        return out
