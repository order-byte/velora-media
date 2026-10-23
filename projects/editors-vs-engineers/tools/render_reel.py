"""Render the reel, frame by frame, from the edit plan.

Usage:
  python3 render_reel.py CONFIG.json OUT.mp4 [--start F --end F]   (one chunk)
  python3 render_reel.py CONFIG.json OUT.mp4 --jobs 4              (split, render in parallel, join)

CONFIG.json lists the inputs (selects + alpha, reel-1 + its alpha and track,
room plate, can holdout, paper plate, edl, selects map).
"""
import argparse
import json
import os
import subprocess
import sys

import cv2
import numpy as np

cv2.setNumThreads(1)   # several render workers run side by side
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "edit"))
import plan  # noqa: E402
from barchart import BarChart  # noqa: E402
from captions import CaptionTrack  # noqa: E402
from clean_plate import push_pull  # noqa: E402
from composite import Compositor, hand_mask, zoom  # noqa: E402
from path_graphic import PathGraphic  # noqa: E402
from timeline import Timeline  # noqa: E402

W, H = 1080, 1920
FPS = 24000 / 1001
V1_FPS = 11987 / 500
MORPH = 0.25          # seconds of optical-flow blend across every join between takes
RIM = (212 / 255, 54 / 255, 62 / 255)


class Reader:
    """Forward-only frame reader with a small cache; reopens if asked to go back."""

    def __init__(self, path, pix="rgb24"):
        self.path, self.pix = path, pix
        self.ch = 3 if pix == "rgb24" else 1
        self.p, self.i, self.cache = None, -1, {}

    def _open(self):
        if self.p:
            self.p.kill()
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", self.path, "-f", "rawvideo", "-pix_fmt", self.pix, "-"],
                                  stdout=subprocess.PIPE)
        self.i = -1

    def get(self, n):
        if n in self.cache:
            return self.cache[n]
        if self.p is None or n < self.i:
            self._open()
        size = W * H * self.ch
        frame = None
        while self.i < n:
            b = self.p.stdout.read(size)
            if len(b) < size:
                break
            self.i += 1
            frame = np.frombuffer(b, np.uint8).reshape(H, W, self.ch)
            if self.ch == 1:
                frame = frame[..., 0]
            self.cache[self.i] = frame
            if len(self.cache) > 96:     # morph cuts need both takes at once; they sit ~2 s apart
                self.cache.pop(min(self.cache))
        return self.cache.get(n, frame if frame is not None else self.cache[max(self.cache)])


def smooth_track(d, keys, win=2):
    idx = sorted(int(k) for k in d if d[k])
    out = {}
    for i in idx:
        near = [d[str(j)] for j in range(i - win, i + win + 1) if str(j) in d and d[str(j)]]
        out[i] = {k: float(np.median([n[k] for n in near])) for k in keys}
    return out


class Renderer:
    def __init__(self, cfg):
        self.cfg = cfg
        self.tl = Timeline(cfg["edl"], cfg["selects_map"])
        self.seg, cards, self.end = plan.build(self.tl)
        self.caps = CaptionTrack(cards)
        room = cv2.cvtColor(cv2.imread(cfg["room_plate"]), cv2.COLOR_BGR2RGB)
        # the can is merged into the matte here, then moves with each take's reframing
        self.hold = cv2.imread(cfg["holdout"], cv2.IMREAD_GRAYSCALE)
        self.comp = Compositor(room, None)
        self.reframe = self._reframes(json.load(open(cfg["span_heads"])))
        self.hands = json.load(open(cfg["hands"]))["frames"] if cfg.get("hands") else None
        self.paper = cv2.cvtColor(cv2.imread(cfg["paper_plate"]), cv2.COLOR_BGR2RGB).astype(np.float32) / 255
        self.sel = Reader(cfg["selects"])
        self.sel_a = Reader(cfg["selects_alpha"], "gray")
        self.v1 = Reader(cfg["reel1"])
        self.v1_a = Reader(cfg["reel1_alpha"], "gray")
        tr = json.load(open(cfg["reel1_track"]))
        self.person = smooth_track(tr["person"], ["top", "cx"])
        self.monitor = self._monitor_quads(tr["monitor"])
        self.bars = BarChart(t_out=self.seg[0]["t"][1] - 0.62)
        self.user_ref = cfg["user_head"]          # median head top / centre of our speaker in reel framing
        self.joins = [sp["out"][1] for sp in self.tl.spans[:-1]]   # the cut happens as a take ends
        self.paths = {}

    # ---------- helpers ----------
    def _monitor_quads(self, mon):
        """Smoothed full quads (top edge rebuilt where the monitor runs off the top of frame)."""
        idx = sorted(int(k) for k in mon if mon[k] and int(k) / V1_FPS < 13.70)
        raw = {i: np.array(mon[str(i)]["quad"], np.float32) for i in idx}
        sharp = {i: mon[str(i)]["sharp"] for i in idx}
        out = {}
        for i in idx:
            near = np.stack([raw[j] for j in range(i - 2, i + 3) if j in raw])
            q = np.median(near, 0)
            tl_, tr_, br_, bl_ = q
            t = i / V1_FPS
            if t < 12.06:
                # flat on screen: trust the top edge, the picture is 9:16
                wdt = tr_[0] - tl_[0]
                bl_ = np.array([tl_[0], tl_[1] + wdt * 16 / 9])
                br_ = np.array([tr_[0], tr_[1] + wdt * 16 / 9])
            else:
                # tilted and cut by the frame top: extend the side lines up to a foreshortened height
                k = 1.0 if t < 12.14 else 0.8
                wb = br_[0] - bl_[0]
                ytop = (bl_[1] + br_[1]) / 2 - wb * 16 / 9 * k
                def along(p_top, p_bot):
                    if abs(p_bot[1] - p_top[1]) < 1:
                        return np.array([p_top[0], ytop])
                    s = (p_top[0] - p_bot[0]) / (p_top[1] - p_bot[1])
                    return np.array([p_bot[0] + s * (ytop - p_bot[1]), ytop])
                tl_, tr_ = along(tl_, bl_), along(tr_, br_)
            out[i] = (np.array([tl_, tr_, br_, bl_], np.float32), sharp[i])
        return out

    def _reframes(self, heads):
        """Per take: a small move/scale that puts the head where it sits in the median take,
        so joins between takes don't jump."""
        ref = heads["ref"]
        out = {}
        for r in heads["spans"]:
            s = 1 + 0.6 * (ref["headw"] / r["headw"] - 1)
            cx, cy = r["cx"] * W, (r["top"] + 0.10) * H
            tx_, ty_ = cx + 0.85 * (ref["cx"] * W - cx), cy + 0.85 * ((ref["top"] + 0.10) * H - cy)
            out[r["span"]] = np.float32([[s, 0, tx_ - s * cx], [0, s, ty_ - s * cy]])
        return out

    def _fetch(self, idx, k):
        f = self.sel.get(idx)
        a = np.maximum(self.sel_a.get(idx), self.hold)
        hm = hand_mask(self.hands[min(idx, len(self.hands) - 1)]) if self.hands else None
        m = self.reframe.get(k)
        if m is not None:
            f = cv2.warpAffine(f, m, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            a = cv2.warpAffine(a, m, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            if hm is not None:
                hm = cv2.warpAffine(hm, m, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
        return f, a, hm

    def _speaker_frame(self, t):
        return self._fetch(self.tl.select_frame(t), self.tl.span_at(t))

    def _v1(self, tau):
        return self.v1.get(int(round(tau * V1_FPS))).astype(np.float32) / 255

    def _aroll(self, t, seg):
        img = self.comp(*self._speaker_frame(t)).astype(np.float32) / 255
        # across a join between takes, morph from the outgoing take into the incoming one
        j = next((b for b in self.joins if abs(t - b) < MORPH / 2 and seg["t"][0] + 0.05 < b < seg["t"][1] - 0.05), None)
        if j is not None:
            k = self.joins.index(j) + 1
            w = (t - (j - MORPH / 2)) / MORPH
            w = w * w * (3 - 2 * w)
            A = self.comp(*self._fetch(self.tl.select_frame_in_span(k - 1, t), k - 1)).astype(np.float32) / 255
            B = self.comp(*self._fetch(self.tl.select_frame_in_span(k, t), k)).astype(np.float32) / 255
            img = morph(A, B, w)
        if seg.get("entrance"):
            k = (t - seg["t"][0]) / 0.16
            if k < 1:
                e = 1 - (1 - k) ** 2
                img = zoom(img, 1.14 - 0.14 * e, 0.5, 0.45)
                img = cv2.GaussianBlur(img, (0, 0), 0.5 + 9 * (1 - e))
        return img

    # ---------- segment kinds ----------
    def frame(self, t):
        seg = next((s for s in self.seg if s["t"][0] <= t < s["t"][1]), self.seg[-1])
        kind = seg["kind"]
        if kind == "aroll":
            img = self._aroll(t, seg)
        elif kind == "bars":
            img = self.bars.render(t - seg["t"][0], self._aroll(t, seg))
        elif kind == "broll":
            img = self._v1(plan.v1_time(seg, t))
        elif kind == "paper":
            img = self._paper(t, plan.v1_time(seg, t))
        elif kind == "monitor":
            img = self._monitor(t, plan.v1_time(seg, t), seg)
        elif kind == "path":
            key = seg["t"][0]
            if key not in self.paths:
                self.paths[key] = PathGraphic(seg["t"][1] - seg["t"][0], seg["t_trust"], seg["t_choose"], seg["t_right"])
            img = self.paths[key].render(t - seg["t"][0])
        img = self.caps.render(t, img)
        return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)

    def _paper(self, t, tau):
        n = int(round(tau * V1_FPS))
        bg = self.v1.get(n).astype(np.float32) / 255
        if tau >= 4.50:
            return bg
        za = self.v1_a.get(n)
        zm = cv2.dilate((za > 8).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31))) > 0
        if 2.55 <= tau <= 4.12:
            fillsrc = self.paper
        elif tau > 4.12:   # exit: the next frame without him shows what is behind
            fillsrc = self._v1(4.52)
        else:              # entrance: the paper itself is zooming in, rebuild from this frame's own pixels
            fillsrc = push_pull(bg * 255, ~zm) / 255
        k = cv2.GaussianBlur(zm.astype(np.float32), (0, 0), 4)[..., None]
        bg = bg * (1 - k) + fillsrc * k

        # our speaker, cut out and graded, following the original speaker's move
        g, al = self.comp.speaker(*self._speaker_frame(t))
        tr = self.person.get(n) or self.person[min(self.person, key=lambda j: abs(j - n))]
        target_top, target_cx = tr["top"] - 0.015, tr["cx"]
        if tau > 4.13:                              # exit: slide down out of frame
            e = min((tau - 4.13) / 0.37, 1.0) ** 1.6
            target_top = 0.355 + 0.55 * e
        p = np.clip((tr["top"] - 0.145) / (0.372 - 0.145), 0, 1) if tau < 2.6 else 1.0
        dy = (target_top - self.user_ref["top"]) * H * p
        dx = (target_cx - self.user_ref["cx"]) * W * p
        m = np.float32([[1, 0, dx], [0, 1, dy]])
        g = cv2.warpAffine(g, m, (W, H), borderValue=(0, 0, 0))
        al = cv2.warpAffine(al, m, (W, H), borderValue=0)
        # moving fast (entrance/exit): vertical motion blur
        speed = abs(target_top - (self.person.get(n - 1, tr)["top"] - 0.015)) if tau <= 4.13 else 0.05
        if speed > 0.01:
            kz = int(min(speed * H * 0.8, 90)) | 1
            g, al = cv2.blur(g, (1, kz)), cv2.blur(al, (1, kz))
        # the red cut-out outline the original has on its right side
        sh = cv2.warpAffine(al, np.float32([[1, 0, 9], [0, 1, 2]]), (W, H), borderValue=0)
        rim = np.clip(sh - al, 0, 1)[..., None]
        bg = bg * (1 - rim) + np.array(RIM, np.float32) * rim
        a3 = al[..., None]
        return g * a3 + bg * (1 - a3)

    def _monitor(self, t, tau, seg):
        n = int(round(tau * V1_FPS))
        bg = self.v1.get(n).astype(np.float32) / 255
        keys = sorted(self.monitor)
        j = min(keys, key=lambda k: abs(k - n))
        quad, sharp = self.monitor[j]
        content = self.comp(*self._speaker_frame(t)).astype(np.float32) / 255
        src = np.float32([[0, 0], [W, 0], [W, H], [0, H]])
        M = cv2.getPerspectiveTransform(src, quad)
        warped = cv2.warpPerspective(content, M, (W, H), flags=cv2.INTER_AREA)
        mask = np.zeros((H, W), np.float32)
        cv2.fillConvexPoly(mask, quad.astype(np.int32), 1.0, lineType=cv2.LINE_AA)
        # match the original's focus: pick the blur whose sharpness is closest to reel 1's
        x0, y0 = int(max(quad[:, 0].min(), 0)), int(max(quad[:, 1].min(), 0))
        x1, y1 = int(min(quad[:, 0].max(), W)), int(min(quad[:, 1].max(), H))
        if x1 - x0 > 20 and y1 - y0 > 20:
            best, bd = warped, 1e9
            for s in (0, 0.8, 1.5, 2.5, 4, 6, 9):
                cand = cv2.GaussianBlur(warped, (0, 0), s) if s else warped
                lum = cand[y0:y1, x0:x1] @ np.array([0.2126, 0.7152, 0.0722], np.float32) * 255
                v = cv2.Laplacian(lum, cv2.CV_32F).var()
                dd = abs(np.log(v + 1) - np.log(sharp + 1))
                if dd < bd:
                    best, bd = cand, dd
            warped = best
        # keep the yellow fx clips of the original on top
        r, g_, b = bg[..., 0], bg[..., 1], bg[..., 2]
        yellow = ((r > 0.59) & (g_ > 0.6 * r) & (b < 0.6 * r)).astype(np.float32)
        mask = mask * (1 - cv2.GaussianBlur(yellow, (0, 0), 1.5))
        m3 = mask[..., None]
        return warped * m3 + bg * (1 - m3)


def morph(A, B, w):
    """Optical-flow morph between two frames of the same shot (a 'morph cut')."""
    s = 0.25
    ga = cv2.cvtColor((cv2.resize(A, None, fx=s, fy=s) * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY)
    gb = cv2.cvtColor((cv2.resize(B, None, fx=s, fy=s) * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY)
    fl = cv2.calcOpticalFlowFarneback(ga, gb, None, 0.5, 4, 21, 4, 7, 1.5, 0)
    fl = cv2.resize(fl, (W, H)) / s
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    wa = cv2.remap(A, xx - w * fl[..., 0], yy - w * fl[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    wb = cv2.remap(B, xx + (1 - w) * fl[..., 0], yy + (1 - w) * fl[..., 1], cv2.INTER_LINEAR,
                   borderMode=cv2.BORDER_REPLICATE)
    return wa * (1 - w) + wb * w


def render(cfg, out, start, end):
    r = Renderer(cfg)
    total = int(np.ceil(r.end * FPS))
    end = min(end if end is not None else total, total)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", "24000/1001", "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "15",
                            "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for i in range(start, end):
        enc.stdin.write(r.frame(i / FPS).tobytes())
        if (i - start) % 48 == 0:
            print(f"{os.path.basename(out)}: frame {i}/{end}", flush=True)
    enc.stdin.close()
    enc.wait()
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("config")
    ap.add_argument("out")
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--end", type=int)
    ap.add_argument("--jobs", type=int, default=1)
    args = ap.parse_args()
    cfg = json.load(open(args.config))
    if args.jobs == 1:
        render(cfg, args.out, args.start, args.end)
        return
    tl = Timeline(cfg["edl"], cfg["selects_map"])
    _, _, end = plan.build(tl)
    total = int(np.ceil(end * FPS))
    cuts = np.linspace(0, total, args.jobs + 1).astype(int)
    base, ext = os.path.splitext(args.out)
    procs, parts = [], []
    for k in range(args.jobs):
        part = f"{base}.part{k}{ext}"
        parts.append(part)
        procs.append(subprocess.Popen([sys.executable, "-I", __file__, args.config, part,
                                       "--start", str(cuts[k]), "--end", str(cuts[k + 1])]))
    for p in procs:
        p.wait()
    lst = base + ".parts.txt"
    open(lst, "w").write("".join(f"file '{os.path.abspath(p)}'\n" for p in parts))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", args.out],
                   check=True)


if __name__ == "__main__":
    main()
