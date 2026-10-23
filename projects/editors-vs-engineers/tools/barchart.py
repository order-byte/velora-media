"""The opening "ENGINEERS vs EDITORS" salary bars, redrawn in the reel-1 design.

Two bars rise from the bottom of frame with a little overshoot while their
dollar figures count up, hold, then tip over and drop out of frame.
"""
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
FONT = os.path.join(os.path.dirname(__file__), "..", "fonts", "LuckiestGuy-Regular.ttf")

BARS = [
    # label, final value, start value, x0, x1, top y, colour (top), colour (bottom)
    ("ENGINEERS", 26000, 3808, 160, 496, 1270, (226, 79, 82), (150, 60, 66)),
    ("EDITORS", 53630, 0, 584, 920, 1030, (234, 186, 88), (150, 118, 60)),
]


def _ease_out_back(k, s=1.4):
    k = np.clip(k, 0, 1) - 1
    return 1 + (s + 1) * k ** 3 + s * k ** 2


def _ease_out_cubic(k):
    return 1 - (1 - np.clip(k, 0, 1)) ** 3


class BarChart:
    def __init__(self, t_in=0.17, rise=0.36, count=1.35, t_out=None, out_len=0.34):
        self.t_in, self.rise, self.count = t_in, rise, count
        self.t_out, self.out_len = t_out, out_len
        self.f_label = ImageFont.truetype(FONT, 56)
        self.f_num = ImageFont.truetype(FONT, 70)

    def _bar(self, label, value, x0, x1, top, c_top, c_bot):
        """One bar as an RGBA layer covering the whole frame."""
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        h = H - top
        # vertical gradient, fading out toward the bottom of frame like the reference
        g = np.linspace(0, 1, h, dtype=np.float32)[:, None]
        col = (np.array(c_top, np.float32) * (1 - g) + np.array(c_bot, np.float32) * g)
        alpha = (1.0 - 0.45 * g ** 1.5) * 255
        strip = np.concatenate([np.repeat(col[:, None, :], x1 - x0, 1),
                                np.repeat(alpha[:, None, :], x1 - x0, 1)], -1).astype(np.uint8)
        img.paste(Image.fromarray(strip, "RGBA"), (x0, top))
        # hard black shadow down the right edge
        d.rectangle([x1, top + 8, x1 + 9, H], fill=(10, 8, 8, 235))
        # label: white with a black outline; figure: black
        cx = (x0 + x1) / 2
        d.text((cx, top + 18), label, font=self.f_label, fill=(255, 250, 240, 255), anchor="mt",
               stroke_width=5, stroke_fill=(15, 12, 12, 255))
        d.text((cx, top + 84), f"${value:,.0f}", font=self.f_num, fill=(18, 14, 14, 255), anchor="mt")
        return np.asarray(img).astype(np.float32) / 255

    def render(self, t, frame):
        """Draw the bars for local time t onto frame (H x W x 3 float 0..1)."""
        if t < self.t_in:
            return frame
        k_rise = _ease_out_back((t - self.t_in) / self.rise)
        k_cnt = _ease_out_cubic((t - self.t_in) / self.count)
        layer = np.zeros((H, W, 4), np.float32)
        for label, v1, v0, x0, x1, top, ct, cb in BARS:
            y = int(H - (H - top) * k_rise)
            b = self._bar(label, v0 + (v1 - v0) * k_cnt, x0, x1, max(y, 0), ct, cb)
            a = b[..., 3:4]
            layer[..., :3] = b[..., :3] * a + layer[..., :3] * (1 - a)
            layer[..., 3:4] = a + layer[..., 3:4] * (1 - a)
        if self.t_out is not None and t > self.t_out:
            # exit: tip back and fall out of frame with motion blur
            k = np.clip((t - self.t_out) / self.out_len, 0, 1)
            e = k ** 2
            m = cv2.getRotationMatrix2D((W / 2, H), -9 * e, 1 - 0.08 * e)
            m[1, 2] += H * 0.75 * e
            layer = cv2.warpAffine(layer, m, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
            blur = int(2 + 60 * e) | 1
            layer = cv2.blur(layer, (1, blur))
            layer[..., 3] *= 1 - 0.3 * e
        a = layer[..., 3:4]
        return frame * (1 - a) + layer[..., :3] * a
