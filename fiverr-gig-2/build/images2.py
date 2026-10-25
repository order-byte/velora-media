"""Gig 2 gallery images for @aminur_rex (dark HiFi look), 1280x769."""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path("/tmp/claude-0/-home-user-velora-media/4a14988d-28db-5a70-b10e-dd2bb40ffc21/scratchpad")
FD, ST = ROOT / "fonts", ROOT / "stills_hq"
OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
W, H = 1280, 769
BG = (14, 15, 12)
PAPER = (240, 241, 235)
DIM = (150, 153, 144)
LINE = (44, 46, 40)

photo_src = Image.open(ROOT.parent / "images/1.webp").convert("RGB")
LIME = tuple(int(v) for v in np.median(np.asarray(photo_src)[:150, :300].reshape(-1, 3), 0))


def font(name, size):
    return ImageFont.truetype(str(FD / f"{name}.ttf"), size)


def still(name, w=None, h=None):
    im = Image.open(ST / f"{name}.jpg").convert("RGB")
    return im.resize((w, h), Image.LANCZOS) if w else im


def rounded_rgba(im, r):
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), r, fill=255)
    out = im.convert("RGBA")
    out.putalpha(m)
    return out


def perspective_card(im, w, quad, r=18):
    """Warp a rounded card into quad (4 points, TL TR BR BL) on a W x H RGBA layer."""
    h = round(w * im.height / im.width)
    card = rounded_rgba(im.resize((w, h), Image.LANCZOS), r)
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    M = cv2.getPerspectiveTransform(src, np.float32(quad))
    arr = np.asarray(card)
    warped = cv2.warpPerspective(arr, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    return Image.fromarray(warped, "RGBA")


def shadow_of(layer, blur=26, alpha=0.55, dy=18):
    a = np.asarray(layer)[..., 3].astype(np.float32) * alpha
    sh = Image.fromarray(a.astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur))
    out = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    out.paste((0, 0, 0, 255), (0, dy), sh)
    return out


def avatar(d):
    s = min(photo_src.size)
    crop = photo_src.crop((photo_src.width - s, 120, photo_src.width, 120 + s)).resize((d, d), Image.LANCZOS)
    m = Image.new("L", (d, d), 0)
    ImageDraw.Draw(m).ellipse((0, 0, d - 1, d - 1), fill=255)
    out = crop.convert("RGBA")
    out.putalpha(m)
    return out


def glow(base, color, box, radius):
    g = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(g).ellipse(box, fill=color + (60,))
    g = g.filter(ImageFilter.GaussianBlur(radius))
    base.alpha_composite(g)


# ---------------------------------------------------------------- 1. thumbnail
img = Image.new("RGBA", (W, H), BG + (255,))
glow(img, LIME, (760, 120, 1260, 620), 140)
back = perspective_card(still("offline_apps"), 640, [(705, 70), (1230, 40), (1250, 360), (720, 395)])
front = perspective_card(still("commas_dash"), 700, [(600, 300), (1180, 250), (1215, 640), (615, 700)])
for layer in (back, front):
    img.alpha_composite(shadow_of(layer))
    img.alpha_composite(layer)
d = ImageDraw.Draw(img)
x = 60
d.text((x, 62), "AMINUR RAHMAN — ANIMATION STUDIO, KOLKATA", font=font("PlexMono-Medium", 16), fill=DIM)
hf = font("ArchivoExp-ExtraBold", 78)
d.text((x - 3, 104), "SaaS demo", font=hf, fill=PAPER)
d.text((x - 3, 196), "videos &", font=hf, fill=PAPER)
d.text((x - 3, 288), "UI motion", font=hf, fill=LIME)
d.text((x, 404), "HiFi animation of your real product", font=font("Archivo-Medium", 26), fill=PAPER)
chips = ["4K", "15 – 90 SEC", "9:16 CUTS"]
cx = x
for c in chips:
    f = font("PlexMono-Medium", 17)
    tw = int(f.getlength(c))
    d.rounded_rectangle((cx, 456, cx + tw + 28, 492), 18, outline=LIME, width=2)
    d.text((cx + 14, 474), c, font=f, fill=LIME, anchor="lm")
    cx += tw + 40
av = avatar(92)
img.alpha_composite(av, (x, 600))
d.text((x + 112, 612), "Aminur", font=font("ArchivoExp-ExtraBold", 26), fill=PAPER)
d.text((x + 112, 652), "You talk to the animator, not a manager", font=font("Archivo-Medium", 19), fill=DIM)
img.convert("RGB").save(OUT / "gig2-image-1-thumbnail.jpg", quality=93)

# ---------------------------------------------------------------- 2. packages
img = Image.new("RGBA", (W, H), BG + (255,))
d = ImageDraw.Draw(img)
d.text((48, 50), "Pick your length", font=font("ArchivoExp-ExtraBold", 48), fill=PAPER)
d.text((W - 48, 72), "@aminur_rex", font=font("PlexMono-Medium", 17), fill=DIM, anchor="ra")
cols = [("FEATURE SPOT", "15 sec", "One feature, made to stop the scroll", "nano_physics", "3-day delivery",
         ["Real UI rebuilt in HiFi", "Music & sound design", "1080p"]),
        ("PRODUCT STORY", "60 sec", "Your full product, start to finish", "commas_checkout", "5-day delivery",
         ["Script & storyboard", "Voice over", "Subtitles"]),
        ("LAUNCH FILM", "90 sec", "Ready for launch day", "offline_box", "7-day delivery",
         ["4K master", "9:16 social cut", "After Effects source file"])]
cw, gap, top = 376, 28, 140
for i, (name, length, line, nm, days, ticks) in enumerate(cols):
    cx = 48 + i * (cw + gap)
    d.rounded_rectangle((cx, top, cx + cw, H - 56), 16, fill=(24, 25, 21), outline=LINE, width=2)
    t = rounded_rgba(still(nm, cw - 32, round((cw - 32) * 9 / 16)), 10)
    img.alpha_composite(t, (cx + 16, top + 16))
    ty = top + 16 + t.height + 26
    d.text((cx + 20, ty), name, font=font("PlexMono-Medium", 17), fill=LIME)
    d.text((cx + 20, ty + 30), length, font=font("ArchivoExp-ExtraBold", 52), fill=PAPER)
    words, lines, cur = line.split(), [], ""
    bf = font("Archivo-Medium", 21)
    for w_ in words:
        test = (cur + " " + w_).strip()
        if bf.getlength(test) > cw - 40:
            lines.append(cur)
            cur = w_
        else:
            cur = test
    lines.append(cur)
    for j, ln in enumerate(lines):
        d.text((cx + 20, ty + 104 + j * 30), ln, font=bf, fill=(205, 207, 199))
    tf = font("Archivo-Medium", 19)
    for k, tk in enumerate(ticks):
        yy = ty + 150 + k * 32
        d.text((cx + 20, yy + 1), "✔", font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18), fill=LIME)
        d.text((cx + 46, yy), tk, font=tf, fill=PAPER)
    d.line((cx + 20, H - 112, cx + cw - 20, H - 112), fill=LINE, width=2)
    d.text((cx + 20, H - 96), days.upper(), font=font("PlexMono-Medium", 15), fill=DIM)
img.convert("RGB").save(OUT / "gig2-image-2-packages.jpg", quality=93)

# ---------------------------------------------------------------- 3. what HiFi means
img = Image.new("RGBA", (W, H), BG + (255,))
d = ImageDraw.Draw(img)
x = 60
d.text((x, 62), "WHAT HIFI MEANS", font=font("PlexMono-Medium", 16), fill=DIM)
d.text((x - 3, 98), "Sharp at", font=font("ArchivoExp-ExtraBold", 64), fill=PAPER)
d.text((x - 3, 174), "any zoom.", font=font("ArchivoExp-ExtraBold", 64), fill=LIME)
pts = [("Real UI, rebuilt", "Your screens recreated in After Effects, not screen-recorded."),
       ("Camera moves", "Push in on the feature that matters, glide across the rest."),
       ("Sound on every click", "Whooshes, clicks and hits timed to the motion."),
       ("Every format", "16:9 in 1080p or 4K, plus 9:16 and 1:1 cuts.")]
for i, (h_, b_) in enumerate(pts):
    py = 296 + i * 104
    d.rounded_rectangle((x, py + 4, x + 10, py + 14), 3, fill=LIME)
    d.text((x + 26, py - 4), h_, font=font("ArchivoExp-ExtraBold", 24), fill=PAPER)
    words, lines, cur = b_.split(), [], ""
    bf = font("Archivo-Medium", 19)
    for w_ in words:
        test = (cur + " " + w_).strip()
        if bf.getlength(test) > 440:
            lines.append(cur)
            cur = w_
        else:
            cur = test
    lines.append(cur)
    for j, ln in enumerate(lines):
        d.text((x + 26, py + 34 + j * 26), ln, font=bf, fill=(190, 192, 184))
# right: full frame + magnified detail from the 4K master
full = still("nano_ui")
fw = 620
fh = round(fw * 9 / 16)
fx, fy = 600, 110
card = rounded_rgba(full.resize((fw, fh), Image.LANCZOS), 14)
img.alpha_composite(card, (fx, fy))
# detail region in source coords (teacher-view card area)
sx0, sy0, sw, sh_ = 730, 470, 520, 290
src4k = Image.open(ST / "nano_ui_4k.jpg").convert("RGB")
det = src4k.crop((sx0 * 2, sy0 * 2, (sx0 + sw) * 2, (sy0 + sh_) * 2)).resize((520, 290), Image.LANCZOS)
rx0 = fx + sx0 * fw / 1920
ry0 = fy + sy0 * fh / 1080
rx1 = rx0 + sw * fw / 1920
ry1 = ry0 + sh_ * fh / 1080
d = ImageDraw.Draw(img)
d.rounded_rectangle((rx0, ry0, rx1, ry1), 6, outline=LIME, width=3)
dx, dy = 690, 420
dc = rounded_rgba(det, 14)
sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(sh).rounded_rectangle((dx, dy + 14, dx + dc.width, dy + dc.height + 14), 14, fill=(0, 0, 0, 160))
img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(22)))
img.alpha_composite(dc, (dx, dy))
d = ImageDraw.Draw(img)
d.rounded_rectangle((dx, dy, dx + dc.width, dy + dc.height), 14, outline=LIME, width=3)
d.line((rx0, ry1, dx, dy), fill=LIME, width=2)
d.line((rx1, ry1, dx + dc.width, dy), fill=LIME, width=2)
d.text((dx + dc.width, dy + dc.height + 18), "NANOSYLLABUS · DETAIL FROM THE 4K MASTER", font=font("PlexMono-Medium", 14), fill=DIM, anchor="ra")
img.convert("RGB").save(OUT / "gig2-image-3-what-hifi-means.jpg", quality=93)
print("ok")
