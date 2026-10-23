"""Measure what we need from reel 1 to swap its speaker for ours.

* person track (torn-paper segment): head top, head width and centre of the
  original speaker per frame, from his matte, so our speaker can follow the
  same move;
* monitor quads (editor-screen segment): the four corners of the program
  monitor per frame, so our footage can be warped into it.

Usage: python3 track_reel1.py REEL1.mp4 REEL1_ALPHA.mkv OUT.json
"""
import json
import subprocess
import sys

import cv2
import numpy as np

W, H = 1080, 1920
FPS = 11987 / 500
PERSON = (1.80, 4.70)
MONITOR = (11.20, 13.75)


def frames(path, pix):
    ch = 3 if pix == "rgb24" else 1
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", pix, "-"],
                         stdout=subprocess.PIPE)
    while True:
        b = p.stdout.read(W * H * ch)
        if len(b) < W * H * ch:
            break
        a = np.frombuffer(b, np.uint8).reshape(H, W, ch)
        yield a if ch == 3 else a[..., 0]
    p.wait()


def head_metrics(alpha):
    m = (alpha > 128).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m)
    if n < 2:
        return None
    k = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    if stats[k, cv2.CC_STAT_AREA] < 0.03 * W * H:
        return None
    body = lab == k
    widths = body.sum(1)
    rows = np.where(widths > 0.04 * W)[0]
    if not len(rows):
        return None
    top = rows[0]
    band = range(top + int(0.03 * H), min(top + int(0.08 * H), H))
    ws, cs = [], []
    for y in band:
        xs = np.where(body[y])[0]
        if len(xs):
            ws.append(xs[-1] - xs[0])
            cs.append((xs[-1] + xs[0]) / 2)
    if not ws:
        return None
    return dict(top=top / H, headw=float(np.median(ws)) / W, cx=float(np.median(cs)) / W)


def monitor_quad(rgb):
    f = rgb.astype(np.float32)
    lum = f @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    chroma = f.max(2) - f.min(2)
    yellow = (r > 150) & (g > 0.6 * r) & (b < 0.6 * r)          # the fx clips below the monitor
    # the editor UI is pure neutral grey; the monitor picture has colour or brightness
    m = (((lum > 62) | (chroma > 14)) & ~yellow).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m)
    if n < 2:
        return None
    k = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    if stats[k, cv2.CC_STAT_AREA] < 0.01 * W * H:
        return None
    cnts, _ = cv2.findContours((lab == k).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    hull = cv2.convexHull(max(cnts, key=cv2.contourArea))
    peri = cv2.arcLength(hull, True)
    for eps in np.linspace(0.01, 0.08, 15):
        q = cv2.approxPolyDP(hull, eps * peri, True)
        if len(q) == 4:
            break
    if len(q) != 4:
        x, y, w, h = cv2.boundingRect(hull)
        q = np.array([[[x, y]], [[x + w, y]], [[x + w, y + h]], [[x, y + h]]])
    pts = q[:, 0, :].astype(float)
    # order: top-left, top-right, bottom-right, bottom-left
    s, d = pts.sum(1), pts[:, 0] - pts[:, 1]
    tl, br = pts[np.argmin(s)], pts[np.argmax(s)]
    tr, bl = pts[np.argmax(d)], pts[np.argmin(d)]
    quad = np.array([tl, tr, br, bl])
    return dict(quad=quad.round(1).tolist(), touches_top=bool(quad[:2, 1].min() <= 2),
                sharp=float(cv2.Laplacian(lum[int(max(tl[1], 0)):int(bl[1]), int(tl[0]):int(tr[0])], cv2.CV_32F).var())
                if bl[1] - max(tl[1], 0) > 10 and tr[0] - tl[0] > 10 else 0.0)


def main():
    src, alpha, out = sys.argv[1:4]
    res = dict(person={}, monitor={})
    for i, (rgb, a) in enumerate(zip(frames(src, "rgb24"), frames(alpha, "gray"))):
        t = i / FPS
        if PERSON[0] <= t <= PERSON[1]:
            res["person"][i] = head_metrics(a)
        if MONITOR[0] <= t <= MONITOR[1]:
            res["monitor"][i] = monitor_quad(rgb)
    json.dump(res, open(out, "w"), indent=1)
    for k in ("person", "monitor"):
        for i, v in list(res[k].items()):
            print(k, i, f"{int(i) / FPS:.2f}", v if k == "person" else (v and (v["quad"], v["touches_top"], round(v["sharp"]))))


if __name__ == "__main__":
    main()
