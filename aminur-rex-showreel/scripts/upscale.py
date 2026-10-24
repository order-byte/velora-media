#!/usr/bin/env python3
"""4x upscale small images with Real-ESRGAN (x4plus weights) on CPU.

The profile picture and banner only exist as screenshot crops (~160 px and
~680 px wide), and the 3D profile card shows the photo several times larger.

usage: python3 upscale.py <RealESRGAN_x4plus.pth> <in.png> <out.png> [<in.png> <out.png> ...]
requires: torch (CPU build), spandrel
"""
import sys

import numpy as np
import torch
from PIL import Image
from spandrel import ModelLoader


def main():
    weights = sys.argv[1]
    # weights_only: never unpickle arbitrary objects from a downloaded checkpoint
    state = torch.load(weights, map_location="cpu", weights_only=True)
    if "params_ema" in state:
        state = state["params_ema"]
    model = ModelLoader().load_from_state_dict(state).eval()
    pairs = sys.argv[2:]
    for src, dst in zip(pairs[::2], pairs[1::2]):
        im = np.asarray(Image.open(src).convert("RGB"), dtype=np.float32) / 255.0
        x = torch.from_numpy(im).permute(2, 0, 1).unsqueeze(0)
        with torch.no_grad():
            y = model(x).clamp(0, 1)
        out = (y[0].permute(1, 2, 0).numpy() * 255).round().astype(np.uint8)
        Image.fromarray(out).save(dst)
        print(src, "->", dst, out.shape[1], "x", out.shape[0])


if __name__ == "__main__":
    main()
