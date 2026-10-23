"""Generate the warm "living-room" background plate (9:16) for the talking-head reel.

Layout and palette follow the reference look: warm beige wall, two black picture
frames hung high, a glowing drum-shade lamp on the left, a dark cabinet edge,
shallow depth of field. Everything is drawn procedurally, so the plate is ours.

Usage: python3 make_background.py OUT_DIR [--seed N]
Writes background_4k.png (2160x3840), background_1080.png (1080x1920),
background_1080.jpg and background_sharp_1080.png (no depth-of-field blur).
"""
import argparse
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 2160, 3840


def grid():
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    return x / W, y / H  # normalised 0..1


def gauss(x, y, cx, cy, sx, sy, amp=1.0):
    # sx/sy in width units so blobs stay round on a 9:16 canvas
    dx = (x - cx) / sx
    dy = (y - cy) * (H / W) / sy
    return amp * np.exp(-0.5 * (dx * dx + dy * dy))


def smoothstep(e0, e1, v):
    t = np.clip((v - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def gradient_map(lum):
    """Map 0..1 luminance onto the reference palette (dark brown -> amber -> cream)."""
    stops = np.array([0.00, 0.18, 0.40, 0.62, 0.82, 1.00], np.float32)
    cols = np.array([
        [8, 3, 1],
        [62, 40, 18],
        [118, 86, 46],
        [160, 132, 84],
        [190, 162, 104],
        [232, 208, 156],
    ], np.float32)
    out = np.empty(lum.shape + (3,), np.float32)
    for c in range(3):
        out[..., c] = np.interp(lum, stops, cols[:, c])
    return out


def wall(x, y):
    lum = np.full_like(x, 0.60)
    # ceiling falloff: top of frame is darker
    lum *= 0.55 + 0.45 * smoothstep(0.0, 0.40, y)
    # floor falloff
    lum *= 1.0 - 0.35 * smoothstep(0.70, 1.0, y)
    # lamp spill on the wall (tight + wide), and a vertical cone above/below the shade
    lum += gauss(x, y, 0.19, 0.585, 0.24, 0.24, 0.20)
    lum += gauss(x, y, 0.22, 0.56, 0.50, 0.50, 0.12)
    lum += gauss(x, y, 0.19, 0.50, 0.12, 0.26, 0.07)
    lum += gauss(x, y, 0.19, 0.68, 0.12, 0.18, 0.04)
    # soft key light washing the right wall
    lum += gauss(x, y, 0.78, 0.48, 0.30, 0.40, 0.10)
    # wall corner at x~0.34 above the lamp: the left plane sits in shade
    corner = 1.0 - 0.12 * (1 - smoothstep(0.31, 0.37, x)) * (1 - smoothstep(0.30, 0.48, y))
    lum *= corner
    # faint low-frequency plaster texture so the wall doesn't look CG-flat
    rng = np.random.default_rng(3)
    tex = Image.fromarray((rng.random((H // 16, W // 16)) * 255).astype(np.uint8))
    tex = tex.resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(40))
    lum *= 1 + 0.06 * (np.asarray(tex).astype(np.float32) / 255 - 0.5)
    return np.clip(lum, 0, 1)


def draw_frames(img, light):
    """Two black frames with original abstract art, lit by the local wall light."""
    d = ImageDraw.Draw(img)
    s = W / 1080.0

    def frame(box, mat_col, art_fn, border=16):
        x0, y0, x1, y1 = [int(v * s) for v in box]
        # soft drop shadow down-right
        sh = Image.new("L", img.size, 0)
        ImageDraw.Draw(sh).rectangle([x0 + 14 * s, y0 + 22 * s, x1 + 14 * s, y1 + 22 * s], fill=150)
        sh = sh.filter(ImageFilter.GaussianBlur(18 * s))
        dark = Image.new("RGB", img.size, (20, 10, 4))
        img.paste(dark, (0, 0), sh)
        d.rectangle([x0, y0, x1, y1], fill=(14, 10, 8))
        b = int(border * s)
        d.rectangle([x0 + b, y0 + b, x1 - b, y1 - b], fill=mat_col)
        m = b + int(0.12 * (x1 - x0))
        art_fn(d, (x0 + m, y0 + m, x1 - m, y1 - m))
        # thin highlight on the frame's top edge
        d.line([x0, y0, x1, y0], fill=(70, 55, 40), width=max(2, int(3 * s)))

    def art_left(d, box):
        x0, y0, x1, y1 = box
        d.rectangle(box, fill=(52, 30, 18))
        cx, w = (x0 + x1) / 2, (x1 - x0)
        # terracotta arch + small sun
        d.rounded_rectangle([cx - w * 0.28, y0 + (y1 - y0) * 0.38, cx + w * 0.28, y1 - (y1 - y0) * 0.08],
                            radius=int(w * 0.28), fill=(150, 72, 36))
        r = w * 0.11
        d.ellipse([cx - r, y0 + (y1 - y0) * 0.18 - r, cx + r, y0 + (y1 - y0) * 0.18 + r], fill=(205, 150, 82))

    def art_right(d, box):
        x0, y0, x1, y1 = box
        d.rectangle(box, fill=(168, 160, 146))
        cx, w, h = (x0 + x1) / 2, (x1 - x0), (y1 - y0)
        # vase
        d.ellipse([cx - w * 0.20, y0 + h * 0.50, cx + w * 0.20, y0 + h * 0.86], fill=(206, 98, 34))
        d.rectangle([cx - w * 0.07, y0 + h * 0.42, cx + w * 0.07, y0 + h * 0.56], fill=(190, 88, 30))
        # white blooms
        rng = np.random.default_rng(7)
        for _ in range(9):
            fx = cx + rng.uniform(-0.30, 0.30) * w
            fy = y0 + h * rng.uniform(0.12, 0.42)
            r = w * rng.uniform(0.07, 0.12)
            d.ellipse([fx - r, fy - r, fx + r, fy + r], fill=(236, 230, 218))
        for _ in range(5):
            fx = cx + rng.uniform(-0.25, 0.25) * w
            fy = y0 + h * rng.uniform(0.18, 0.40)
            d.line([fx, fy, cx, y0 + h * 0.45], fill=(92, 98, 60), width=max(2, int(w * 0.012)))

    # coordinates in 1080x1920 space (scaled by s)
    frame((448, 118, 578, 566), (196, 186, 168), art_left, border=14)
    frame((636, -30, 876, 540), (214, 208, 196), art_right, border=18)

    # relight the frames by the wall's local illumination
    a = np.asarray(img).astype(np.float32)
    return a * (0.35 + 0.80 * light[..., None])


def draw_lamp_and_cabinet(a, x, y):
    s = W / 1080.0
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    # stem + base (dark, in front of the wall)
    d.rectangle([200 * s, 1200 * s, 212 * s, 1430 * s], fill=(28, 16, 8))
    d.ellipse([150 * s, 1420 * s, 262 * s, 1450 * s], fill=(22, 12, 6))
    # cabinet on the far left
    d.rectangle([0, 1270 * s, 92 * s, H], fill=(9, 4, 2))
    d.line([0, 1270 * s, 92 * s, 1270 * s], fill=(58, 34, 16), width=int(4 * s))
    d.line([92 * s, 1270 * s, 92 * s, H], fill=(30, 16, 7), width=int(3 * s))
    a = np.asarray(img).astype(np.float32)

    # drum shade, slightly tapered, lit from inside (brighter toward the bottom rim)
    top, bot = 0.545, 0.625
    t = np.clip((y - top) / (bot - top), 0, 1)
    half_w = 0.095 + 0.025 * t
    inside = (y >= top) & (y <= bot) & (np.abs(x - 0.19) <= half_w)
    shade_lum = 0.76 + 0.14 * t - 0.18 * (np.abs(x - 0.19) / half_w) ** 2
    shade = gradient_map(np.clip(shade_lum, 0, 1)) * np.array([1.0, 0.98, 0.92], np.float32)
    a = np.where(inside[..., None], shade, a)
    return a


def bloom(a, radius, strength):
    lum = a.mean(axis=2)
    hi = np.clip((lum - 165) / 90, 0, 1)[..., None] * a
    hi_img = Image.fromarray(np.clip(hi, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(radius))
    return a + strength * np.asarray(hi_img).astype(np.float32)


def vignette(a, x, y, amount=0.38):
    r = np.sqrt(((x - 0.5) / 0.75) ** 2 + ((y - 0.52) / 0.85) ** 2)
    return a * (1 - amount * smoothstep(0.35, 1.0, r))[..., None]


def grain(a, seed, amount=3.0):
    rng = np.random.default_rng(seed)
    n = rng.normal(0, amount, a.shape[:2]).astype(np.float32)
    return a + n[..., None]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir")
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    x, y = grid()
    light = wall(x, y)
    base = Image.fromarray(gradient_map(light).astype(np.uint8))
    a = draw_frames(base, light)
    a = draw_lamp_and_cabinet(a, x, y)
    sharp = vignette(bloom(a, 60, 0.35), x, y)

    # depth of field: the wall sits ~2 m behind the speaker
    dof = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(11))
    a = np.asarray(dof).astype(np.float32)
    a = bloom(a, 110, 0.40)
    a = vignette(a, x, y)
    a = grain(a, args.seed)

    out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    out.save(os.path.join(args.out_dir, "background_4k.png"))
    small = out.resize((1080, 1920), Image.LANCZOS)
    small.save(os.path.join(args.out_dir, "background_1080.png"))
    small.save(os.path.join(args.out_dir, "background_1080.jpg"), quality=95)
    Image.fromarray(np.clip(sharp, 0, 255).astype(np.uint8)).resize((1080, 1920), Image.LANCZOS).save(
        os.path.join(args.out_dir, "background_sharp_1080.png"))


if __name__ == "__main__":
    main()
