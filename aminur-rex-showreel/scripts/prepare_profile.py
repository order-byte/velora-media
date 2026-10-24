#!/usr/bin/env python3
"""Build the profile assets from the (4x upscaled) X profile screenshot crops.

- person.png  : the person cut out of the lime background (for the 3D pop-out)
- avatar.png  : the round avatar as on X (lime background kept)
- banner.jpg  : the header image, resized for the profile card

The photo is black and white on a flat lime backdrop, so the key is simply
"how much greener than grey is this pixel"; edge spill is removed by
rebuilding colour from the red and blue channels.

usage: python3 prepare_profile.py <avatar_x4.png> <banner_x4.png> <out_dir>
"""
import os
import sys

import numpy as np
from PIL import Image

# circle of the avatar inside the 640 px crop (measured on the screenshot)
CX, CY, R = 318.0, 310.0, 281.0


def main():
    av_path, banner_path, out = sys.argv[1:4]
    os.makedirs(out, exist_ok=True)
    im = np.asarray(Image.open(av_path).convert("RGB"), dtype=np.float32)
    h, w, _ = im.shape
    r, g, b = im[..., 0], im[..., 1], im[..., 2]

    yy, xx = np.mgrid[0:h, 0:w]
    dist = np.hypot(xx - CX, yy - CY)
    inside = np.clip((R - dist) / 2.0, 0, 1)  # 2 px soft edge

    green = g - np.maximum(r * 0.55 + b * 0.45, b)  # lime ~ +130, grey ~ 0
    key = 1.0 - np.clip((green - 28.0) / (95.0 - 28.0), 0, 1)
    # the original circle cut through the hair; feather it so the head can
    # pop out of the frame without a hard arc on top
    feather = np.clip((R - 4 - dist) / 26.0, 0, 1)
    alpha = key * np.where(yy < CY, feather, inside)

    grey = (r + b) / 2.0  # B&W photo: drop the green spill entirely
    person = np.dstack([grey, grey, grey, alpha * 255]).clip(0, 255).astype(np.uint8)
    Image.fromarray(person, "RGBA").save(os.path.join(out, "person.png"))

    avatar = np.dstack([im, inside[..., None] * 255]).clip(0, 255).astype(np.uint8)
    Image.fromarray(avatar, "RGBA").save(os.path.join(out, "avatar.png"))

    banner = Image.open(banner_path).convert("RGB")
    banner = banner.resize((1600, round(banner.height * 1600 / banner.width)), Image.LANCZOS)
    banner.save(os.path.join(out, "banner.jpg"), quality=92)
    print("wrote person.png, avatar.png, banner.jpg to", out)


if __name__ == "__main__":
    main()
