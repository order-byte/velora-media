"""Render the "POV: you hire me as your editor" reel on an HP Victus 15
running Adobe After Effects, with the McLaren F1 edit playing in the comp.

The camera move is the one tracked from the reference reel (tools/), the
screen shows ae_ui.py, the laptop is victus.py, and the audio is the edit's
own soundtrack.

    python3 render.py --edit mclaren.mp4 --out ../output/reel.mp4
    python3 render.py --edit mclaren.mp4 --preview 0,30,200 --png /tmp/frames
"""
import argparse
import os
import shutil
import subprocess
import tempfile
from multiprocessing import Process

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import ae_ui
import victus
from camera import CameraPath

OUT_W, OUT_H, FPS = 1080, 1920, 30
SHUTTER = 0.35  # fraction of the frame interval the virtual shutter is open
SCALE = OUT_W / 720.0
CAPTION = "POV: you hire me as your editor"
# caption box of the reference reel, in its 720x1280 pixels
CAPTION_X0, CAPTION_X1, CAPTION_Y0 = 80, 640, 319


def caption_layer():
    """White Instagram-style caption; returns (y0, rgb patch, alpha patch)."""
    target = (CAPTION_X1 - CAPTION_X0 + 1) * SCALE
    fn = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
    size = 40
    while True:
        f = ImageFont.truetype(fn, size + 1)
        bb = f.getbbox(CAPTION)
        if bb[2] - bb[0] > target:
            break
        size += 1
    f = ImageFont.truetype(fn, size)
    bb = f.getbbox(CAPTION)
    band_y0 = int(CAPTION_Y0 * SCALE) - 20
    band = Image.new("L", (OUT_W, 110), 0)
    ImageDraw.Draw(band).text((CAPTION_X0 * SCALE - bb[0], CAPTION_Y0 * SCALE - band_y0 - bb[1]), CAPTION, font=f, fill=255)
    a = np.array(band).astype(np.float32) / 255.0
    rgb = np.full((110, OUT_W, 3), 246.0, np.float32)
    return band_y0, rgb, a[:, :, None]


class Renderer:
    def __init__(self, thumb):
        self.cam = CameraPath()
        self.ui_base = ae_ui.build_base(thumb)
        self.drawer = ae_ui.FrameDrawer()
        lid, lid_a = victus.build_lid()
        self.lid = lid.astype(np.float32)
        self.lid_a = lid_a
        self.deck_A, self.deck_B, self.deck_E, _ = victus.build_deck()
        self.deck_a = np.ones(self.deck_A.shape[:2], np.float32)
        self.lid_probe = (victus.LID_W / 2, victus.LID_H / 2)
        self.deck_probe = (victus.DECK_W / 2, 75 * victus.PX_PER_MM_DECK)
        self.T_lid = victus.lid_to_plane()
        self.T_deck = victus.deck_to_plane()
        self.out = np.diag([SCALE, SCALE, 1.0])
        yy = np.linspace(0, 1, OUT_H)[:, None, None]
        self.bg = np.ones((OUT_H, OUT_W, 3), np.float32) * (np.array([13, 11, 12], np.float32) * (1 - 0.35 * yy))
        gy, gx = np.mgrid[0:OUT_H, 0:OUT_W].astype(np.float32)
        r = np.sqrt(((gx - OUT_W / 2) / (OUT_W * 0.75)) ** 2 + ((gy - OUT_H * 0.55) / (OUT_H * 0.7)) ** 2)
        self.vignette = (1 - 0.28 * np.clip(r, 0, 1.4) ** 2.2)[:, :, None]
        self.gx, self.gy = gx, gy
        self.cap_y0, self.cap_rgb, self.cap_a = caption_layer()

    # -- helpers
    def _warp(self, tex, H, probe=None, border=0.0):
        # pre-filter along each texture axis that gets minified, so UI text and
        # key legends don't alias (the deck is squeezed far more along its depth)
        if probe is not None:
            x, y = probe
            w = H[2, 0] * x + H[2, 1] * y + H[2, 2]
            q = (H[:2] @ np.array([x, y, 1.0])) / w
            J = (H[:2, :2] - np.outer(q, H[2, :2])) / w
            sig = [0.5 * (1 / sc - 1) + 0.2 if sc < 0.85 else 0 for sc in np.linalg.norm(J, axis=0)]
            if max(sig) > 0:
                tex = cv2.GaussianBlur(tex, (0, 0), sigmaX=max(sig[0], 0.01), sigmaY=max(sig[1], 0.01))
        return cv2.warpPerspective(tex, H, (OUT_W, OUT_H), flags=cv2.INTER_LINEAR,
                                   borderMode=cv2.BORDER_CONSTANT, borderValue=border)

    def _deck_valid(self, m):
        """Pixels whose camera ray hits the deck plane in front of the camera."""
        R, t = self.cam.pose(m)
        a = np.pi - self.cam.theta
        d = np.cos(a) * R[:, 1] - np.sin(a) * R[:, 2]
        n = np.cross(R[:, 0], d)
        p0 = self.cam.yh * R[:, 1] + t
        Kinv = np.linalg.inv(self.out @ self.cam.K)
        c = n @ Kinv  # n . (K^-1 [x y 1])
        side = c[0] * self.gx + c[1] * self.gy + c[2]
        return (side * np.dot(n, p0) > 0).astype(np.float32)

    def _plane_point(self, m, X, Y):
        p = self.out @ self.cam.screen_plane_to_image(m) @ np.array([X, Y, 1.0])
        return p[:2] / p[2]

    def render(self, k, viewer_rgb):
        t = k / FPS
        screen = self.drawer.draw(self.ui_base, k, viewer_rgb).astype(np.float32)
        # how the panel reads on a phone sensor: slightly cool, lifted blacks
        screen = screen * np.array([1.05, 1.07, 1.12], np.float32) + 2.5
        lid = self.lid.copy()
        ox, oy = victus.DISPLAY_ORIGIN
        lid[oy:oy + victus.DISPLAY_H, ox:ox + victus.DISPLAY_W] = screen
        light = 0.55 + 1.1 * viewer_rgb.mean() / 255.0
        deck = self.deck_A + self.deck_B * light + self.deck_E

        # ~125-degree shutter: integrate the camera move while it is open
        m0 = self.cam.ref_index(t - SHUTTER / 2 / FPS)
        m1 = self.cam.ref_index(t + SHUTTER / 2 / FPS)
        disp = np.linalg.norm(self._plane_point(m1, 0, 150) - self._plane_point(m0, 0, 150))
        disp = max(disp, np.linalg.norm(self._plane_point(m1, 0, 540) - self._plane_point(m0, 0, 540)))
        n = int(np.clip(np.ceil(disp / 1.2), 1, 16))
        acc = np.zeros((OUT_H, OUT_W, 3), np.float32)
        for j in range(n):
            tau = t if n == 1 else t + ((j + 0.5) / n - 0.5) * SHUTTER / FPS
            m = self.cam.ref_index(tau)
            Hl = self.out @ self.cam.screen_plane_to_image(m) @ self.T_lid
            Hd = self.out @ self.cam.deck_plane_to_image(m) @ self.T_deck
            frame = self.bg.copy()
            da = self._warp(self.deck_a, Hd)[:, :, None] * self._deck_valid(m)[:, :, None]
            if da.max() > 0:
                frame = frame * (1 - da) + self._warp(deck, Hd, self.deck_probe) * da
            la = self._warp(self.lid_a, Hl)[:, :, None]
            frame = frame * (1 - la) + self._warp(lid, Hl, self.lid_probe) * la
            acc += frame
        frame = acc / n

        # screen haze + highlight bloom in a dark room
        small = cv2.resize(frame, (OUT_W // 8, OUT_H // 8), interpolation=cv2.INTER_AREA)
        haze = cv2.resize(cv2.GaussianBlur(small, (0, 0), 7), (OUT_W, OUT_H), interpolation=cv2.INTER_LINEAR)
        hi = cv2.resize(np.maximum(frame - 185, 0), (OUT_W // 4, OUT_H // 4), interpolation=cv2.INTER_AREA)
        bloom = cv2.resize(cv2.GaussianBlur(hi, (0, 0), 4), (OUT_W, OUT_H), interpolation=cv2.INTER_LINEAR)
        frame = frame + 0.10 * haze + 0.30 * bloom
        frame = cv2.GaussianBlur(frame, (0, 0), 0.55)
        frame *= self.vignette
        # sensor noise, a touch blotchy like a phone's denoised video
        rng = np.random.default_rng(1000 + k)
        noise = cv2.resize(rng.normal(0, 2.4, (OUT_H // 2, OUT_W // 2)).astype(np.float32), (OUT_W, OUT_H))
        frame += noise[:, :, None] * (0.6 + 0.4 * (frame < 60))
        frame += rng.normal(0, 0.8, frame.shape).astype(np.float32)
        y0 = self.cap_y0
        band = frame[y0:y0 + self.cap_a.shape[0]]
        frame[y0:y0 + self.cap_a.shape[0]] = band * (1 - self.cap_a) + self.cap_rgb * self.cap_a
        return np.clip(frame, 0, 255).astype(np.uint8)


def edit_frames(path, start, stop):
    fx, fy, fw, fh = ae_ui.FRAME
    cap = cv2.VideoCapture(path)
    i = 0
    last = None
    while i < stop:
        ok, f = cap.read()
        if ok:
            last = cv2.resize(cv2.cvtColor(f, cv2.COLOR_BGR2RGB), (fw, fh), interpolation=cv2.INTER_AREA)
        if i >= start:
            yield i, last
        i += 1


def thumb_frame(path):
    cap = cv2.VideoCapture(path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, 880)
    ok, f = cap.read()
    return cv2.cvtColor(f, cv2.COLOR_BGR2RGB)


def worker(edit, start, stop, seg_path):
    r = Renderer(thumb_frame(edit))
    enc = subprocess.Popen([
        "ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OUT_W}x{OUT_H}",
        "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "10",
        "-pix_fmt", "yuv420p", seg_path], stdin=subprocess.PIPE)
    for k, viewer in edit_frames(edit, start, stop):
        enc.stdin.write(r.render(k, viewer).tobytes())
        if (k - start) % 40 == 0:
            print(f"[{os.path.basename(seg_path)}] frame {k}/{stop}", flush=True)
    enc.stdin.close()
    enc.wait()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--edit", required=True, help="the edit that plays inside After Effects")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "output", "pov_editor_hp_victus_after_effects.mp4"))
    ap.add_argument("--preview", help="comma-separated frame numbers to dump as PNG instead of encoding")
    ap.add_argument("--png", default=".")
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 4)
    args = ap.parse_args()

    total = ae_ui.TOTAL_FRAMES
    if args.preview:
        want = sorted(int(x) for x in args.preview.split(","))
        r = Renderer(thumb_frame(args.edit))
        for k, viewer in edit_frames(args.edit, 0, want[-1] + 1):
            if k in want:
                cv2.imwrite(os.path.join(args.png, f"preview_{k:04d}.png"), cv2.cvtColor(r.render(k, viewer), cv2.COLOR_RGB2BGR))
        return

    tmp = tempfile.mkdtemp(prefix="victus_reel_")
    bounds = np.linspace(0, total, args.workers + 1).astype(int)
    segs = [os.path.join(tmp, f"seg{w}.mp4") for w in range(args.workers)]
    procs = [Process(target=worker, args=(args.edit, bounds[w], bounds[w + 1], segs[w])) for w in range(args.workers)]
    for p in procs:
        p.start()
    for p in procs:
        p.join()
        if p.exitcode:
            raise SystemExit(f"worker failed with {p.exitcode}")
    lst = os.path.join(tmp, "list.txt")
    with open(lst, "w") as fh:
        fh.writelines(f"file '{s}'\n" for s in segs)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    subprocess.check_call([
        "ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-i", args.edit,
        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "libx264", "-preset", "slow", "-crf", "21", "-maxrate", "12M", "-bufsize", "24M",
        "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-movflags", "+faststart", args.out])
    shutil.rmtree(tmp)
    print("wrote", args.out)


if __name__ == "__main__":
    main()
