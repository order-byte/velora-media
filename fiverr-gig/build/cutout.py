# Key the lime background out of the profile photo -> RGBA PNG.
import sys, numpy as np
from PIL import Image, ImageFilter
src, dst, preview = sys.argv[1:4]
im = np.asarray(Image.open(src).convert("RGB")).astype(np.float32) / 255
R, G, B = im[..., 0], im[..., 1], im[..., 2]
Y = 0.299 * R + 0.587 * G + 0.114 * B
Cb = -0.1687 * R - 0.3313 * G + 0.5 * B
Cr = 0.5 * R - 0.4187 * G - 0.0813 * B
bg = np.median(im[:200, :400].reshape(-1, 3), 0)
kCb = -0.1687 * bg[0] - 0.3313 * bg[1] + 0.5 * bg[2]
kCr = 0.5 * bg[0] - 0.4187 * bg[1] - 0.0813 * bg[2]
d = np.sqrt((Cb - kCb) ** 2 + (Cr - kCr) ** 2)
a = np.clip((d - 0.13) / (0.30 - 0.13), 0, 1)
# small cleanup: blur alpha a touch, then re-contrast
ai = Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))
a = np.asarray(ai).astype(np.float32) / 255
a = np.clip((a - 0.04) / 0.92, 0, 1)
# unmix the lime from semi-transparent edge pixels
F = (im - (1 - a[..., None]) * bg) / np.maximum(a[..., None], 0.05)
F = np.clip(F, 0, 1)
# despill: pull residual yellow-green tint toward neutral
FY = 0.299 * F[..., 0] + 0.587 * F[..., 1] + 0.114 * F[..., 2]
F[..., 1] = np.minimum(F[..., 1], F[..., 0] * 1.0 + 0.01)
FY = 0.299 * F[..., 0] + 0.587 * F[..., 1] + 0.114 * F[..., 2]
k = np.clip((1 - a) * 1.6, 0, 1)[..., None] ** 0.6
F = F * (1 - k) + FY[..., None] * k * 0.85
FY = 0.299 * F[..., 0] + 0.587 * F[..., 1] + 0.114 * F[..., 2]
dark = np.clip((0.42 - FY) / 0.2, 0, 1)[..., None]
yellow = np.clip((F[..., 1] + F[..., 0]) / 2 - F[..., 2] - 0.06, 0, 1)[..., None] * 4
kk = np.clip(np.maximum(dark, np.minimum(yellow, 1) * (FY[..., None] < 0.55)), 0, 1)
F = F * (1 - kk) + FY[..., None] * kk
out = np.dstack([F, a])
Image.fromarray((out * 255).astype(np.uint8), "RGBA").save(dst)
print("bg lime", (bg * 255).round(), "alpha mean", a.mean().round(3))
# previews on dark and white
h, w = a.shape
can = Image.new("RGB", (w * 2, h), (14, 15, 12))
can.paste((240, 240, 235), (w, 0, w * 2, h))
rgba = Image.open(dst)
can.paste(rgba, (0, 0), rgba); can.paste(rgba, (w, 0), rgba)
can.thumbnail((1400, 1000)); can.save(preview, quality=88)
