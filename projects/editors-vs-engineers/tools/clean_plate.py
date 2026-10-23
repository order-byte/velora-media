"""Recover an empty-room background plate from a locked-off talking-head clip.

For every pixel, average the frames where it is neither covered by the speaker
(from a matte) nor by on-screen graphics (white text, the brown waveform strip).
Pixels that are never visible are filled with a smooth push-pull interpolation,
then given grain that matches the footage, so the fill reads as wall.

Usage: python3 clean_plate.py IN.mp4 ALPHA.mkv OUT.png [--step 2]
"""
import argparse
import subprocess

import cv2
import numpy as np
from PIL import Image, ImageFilter


def frames(path, w, h, pix="rgb24", step=1):
    ch = 3 if pix == "rgb24" else 1
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", pix, "-"],
                         stdout=subprocess.PIPE)
    i = 0
    while True:
        buf = p.stdout.read(w * h * ch)
        if len(buf) < w * h * ch:
            break
        if i % step == 0:
            a = np.frombuffer(buf, np.uint8).reshape(h, w, ch)
            yield a if ch == 3 else a[..., 0]
        i += 1
    p.wait()


def dilate(mask, px):
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * px + 1, 2 * px + 1))
    return cv2.dilate(mask.astype(np.uint8), k) > 0


def overlay_mask(rgb):
    h, w = rgb.shape[:2]
    text = rgb[..., 2] > 140                        # white/cream captions and waveform lines
    band = np.zeros_like(text)
    band[int(0.22 * h):int(0.46 * h)] = True        # graphics only ever sit in this band
    mask = dilate(text & band, 10)
    # the brown waveform strip: a fixed rectangle, present when its sample patch turns pink-brown
    patch = rgb[int(0.32 * h):int(0.39 * h), int(0.26 * w):int(0.40 * w)].reshape(-1, 3).astype(np.float32)
    r, g = patch[:, 0].mean(), patch[:, 1].mean()
    if g / max(r, 1) < 0.76:
        mask[int(0.298 * h):int(0.418 * h), int(0.20 * w):] = True
    return mask


def push_pull(img, known):
    """Fill unknown pixels from known ones through an image pyramid."""
    levels = []
    cur, w = img * known[..., None], known.astype(np.float32)
    while min(cur.shape[:2]) > 4:
        levels.append((cur, w))
        h2, w2 = cur.shape[0] // 2, cur.shape[1] // 2
        c = cur[:h2 * 2, :w2 * 2].reshape(h2, 2, w2, 2, 3).sum((1, 3))
        ww = w[:h2 * 2, :w2 * 2].reshape(h2, 2, w2, 2).sum((1, 3))
        cur, w = c, ww
    est = cur / np.maximum(w, 1e-6)[..., None]
    for cur, w in reversed(levels):
        up = np.asarray(Image.fromarray(np.clip(est, 0, 255).astype(np.uint8)).resize(
            (cur.shape[1], cur.shape[0]), Image.BILINEAR)).astype(np.float32)
        mine = cur / np.maximum(w, 1e-6)[..., None]
        a = np.clip(w, 0, 1)[..., None]
        est = mine * a + up * (1 - a)
    return est


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("alpha")
    ap.add_argument("out")
    ap.add_argument("--step", type=int, default=2)
    args = ap.parse_args()
    out = subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                   "stream=width,height", "-of", "csv=p=0", args.src]).decode().split(",")
    w, h = int(out[0]), int(out[1])

    stack, masks = [], []
    for rgb, a in zip(frames(args.src, w, h, step=args.step), frames(args.alpha, w, h, "gray", args.step)):
        person = dilate(a > 4, 48)
        stack.append(rgb.copy())
        masks.append(~(person | overlay_mask(rgb)))
    stack, masks = np.stack(stack), np.stack(masks)
    cnt = masks.sum(0)
    known = cnt >= 3
    # under the frames the strip sat on plain wall in almost every frame: rebuild that wall smoothly
    known[int(0.312 * h):int(0.42 * h), int(0.20 * w):] = False
    # per-pixel median of the clean samples: robust to the odd frame the matte missed
    mean = np.zeros((h, w, 3), np.float64)
    for y0 in range(0, h, 64):
        blk = stack[:, y0:y0 + 64].astype(np.float32)
        blk[~masks[:, y0:y0 + 64]] = np.nan
        with np.errstate(all="ignore"):
            med = np.nanmedian(blk, axis=0)
        mean[y0:y0 + 64] = np.nan_to_num(med)
    del stack
    print(f"visible pixels: {known.mean() * 100:.1f}%")

    # thin gaps (text that always overlapped the frames' edges): structure-aware inpaint
    big = cv2.morphologyEx((~known).astype(np.uint8), cv2.MORPH_OPEN,
                           cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (41, 41))) > 0
    small = ~known & ~big
    mean8 = np.clip(mean, 0, 255).astype(np.uint8)
    mean8 = cv2.inpaint(mean8, small.astype(np.uint8), 7, cv2.INPAINT_TELEA)
    known = known | small
    mean = mean8.astype(np.float64)
    # large hole (the speaker): smooth membrane fill
    fill = push_pull(mean.astype(np.float32), known)
    # soften the seam between recovered and filled regions (blend only inside the known area)
    mean = np.where(known[..., None], mean, fill)
    k = np.asarray(Image.fromarray(known.astype(np.uint8) * 255).filter(ImageFilter.GaussianBlur(12))) / 255.0
    k = np.where(known, k, 0.0)
    plate = mean * k[..., None] + fill * (1 - k[..., None])
    # averaging removed the footage grain; put matching grain back everywhere
    rng = np.random.default_rng(5)
    plate += rng.normal(0, 2.2, (h, w))[..., None]
    Image.fromarray(np.clip(plate, 0, 255).astype(np.uint8)).save(args.out)
    Image.fromarray((known * 255).astype(np.uint8)).save(args.out.replace(".png", "_known.png"))


if __name__ == "__main__":
    main()
