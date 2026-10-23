"""Build the "warm lamp-lit room" look as a 3D LUT (.cube, 33 points).

The look: crushed warm blacks, no pure whites (highlights roll off to cream),
blues pulled out of the shadows and mids, everything tinted amber/brown,
skin kept natural. Input is normal Rec.709 footage (phone / camera, not LOG).

Usage: python3 make_lut.py OUT.cube [--strength 1.0]
"""
import argparse

import numpy as np

# hue of the look at shadow / mid / highlight luma (R, G, B ratios)
HUE_STOPS = np.array([0.0, 0.08, 0.45, 0.85, 1.0], np.float32)
HUE = np.array([
    [1.00, 0.55, 0.30],
    [1.00, 0.62, 0.32],
    [1.00, 0.80, 0.52],
    [1.00, 0.89, 0.66],
    [1.00, 0.92, 0.74],
], np.float32)
LUMA = np.array([0.2126, 0.7152, 0.0722], np.float32)


def tone(l):
    l = np.clip((l - 0.035) / 0.965, 0, 1)        # crush the blacks
    l = l ** 1.15                                  # slightly heavier mids (moody)
    l = 1.0 - (1.0 - l) ** 1.35                    # soft shoulder
    return 0.015 + 0.86 * l                        # lifted-but-dark floor, no pure white


def grade(rgb, strength=1.0):
    l = rgb @ LUMA
    lt = tone(l)
    chroma = rgb - l[..., None]
    # tint target: palette hue at the new luma, scaled so its luma equals lt
    hue = np.stack([np.interp(lt, HUE_STOPS, HUE[:, c]) for c in range(3)], -1)
    tint = hue * (lt / np.maximum(hue @ LUMA, 1e-6))[..., None]
    # keep some of the scene's own colour (skin, clothes), drop most of its blue
    keep = chroma * np.array([0.70, 0.60, 0.45], np.float32)
    out = tint + keep
    # skin protection: keep a little more of the original in orange-ish pixels
    skin = np.clip(1 - np.abs((rgb[..., 0] - rgb[..., 2]) - 0.22) / 0.18, 0, 1) * (l > 0.2)
    out = out * (1 - 0.15 * skin[..., None]) + (lt[..., None] + chroma * 0.9) * (0.15 * skin[..., None])
    out = np.clip(out, 0, 1)
    return rgb + (out - rgb) * strength


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--strength", type=float, default=1.0)
    ap.add_argument("--size", type=int, default=33)
    args = ap.parse_args()
    n = args.size
    v = np.linspace(0, 1, n, dtype=np.float32)
    # .cube order: red changes fastest, then green, then blue
    b, g, r = np.meshgrid(v, v, v, indexing="ij")
    rgb = np.stack([r, g, b], -1).reshape(-1, 3)
    out = grade(rgb, args.strength)
    with open(args.out, "w") as f:
        f.write('TITLE "Velora Warm Lamp Room"\n')
        f.write(f"LUT_3D_SIZE {n}\n")
        f.write("DOMAIN_MIN 0.0 0.0 0.0\nDOMAIN_MAX 1.0 1.0 1.0\n")
        for px in out:
            f.write(f"{px[0]:.6f} {px[1]:.6f} {px[2]:.6f}\n")


if __name__ == "__main__":
    main()
