"""Fiverr gallery images for @aminur_rex, 1280x769 (Fiverr's recommended size)."""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path("/tmp/claude-0/-home-user-velora-media/4a14988d-28db-5a70-b10e-dd2bb40ffc21/scratchpad")
FD, ST = ROOT / "fonts", ROOT / "stills_hq"
OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
W, H = 1280, 769
INK = (12, 12, 10)
PAPER = (244, 245, 240)
MUTED = (92, 96, 88)


def font(name, size):
    return ImageFont.truetype(str(FD / f"{name}.ttf"), size)


def rounded(im, r):
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), r, fill=255)
    out = im.convert("RGBA")
    out.putalpha(m)
    return out


def still(name, w, h):
    im = Image.open(ST / f"{name}.jpg").convert("RGB")
    return im.resize((w, h), Image.LANCZOS)


def shadow_paste(base, tile, x, y, r=12, blur=16, alpha=70):
    sh = Image.new("L", (tile.width + blur * 4, tile.height + blur * 4), 0)
    ImageDraw.Draw(sh).rounded_rectangle((blur * 2, blur * 2 + 8, blur * 2 + tile.width, blur * 2 + tile.height + 8), r, fill=alpha)
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    base.paste((0, 0, 0), (x - blur * 2, y - blur * 2), sh)
    base.paste(tile, (x, y), tile)


photo_src = Image.open(ROOT.parent / "images/1.webp").convert("RGB")
LIME = tuple(int(v) for v in np.median(np.asarray(photo_src)[:150, :300].reshape(-1, 3), 0))

# ---------------------------------------------------------------- 1. thumbnail
img = Image.new("RGB", (W, H), LIME)
ph_h = H
ph_w = round(photo_src.width * ph_h / photo_src.height)
ph = photo_src.resize((ph_w, ph_h), Image.LANCZOS).convert("RGBA")
a = np.full((ph_h, ph_w), 255, np.uint8)
ramp = 50
a[:, :ramp] = (a[:, :ramp] * np.linspace(0, 1, ramp)[None, :]).astype(np.uint8)
ph.putalpha(Image.fromarray(a))
img.paste(ph, (W - ph_w + 8, 0), ph)
d = ImageDraw.Draw(img)
x = 64
d.text((x, 66), "AMINUR RAHMAN — ANIMATION STUDIO, KOLKATA", font=font("PlexMono-Medium", 17), fill=INK)
hf = font("ArchivoExp-ExtraBold", 100)
for i, line in enumerate(["SaaS", "explainer", "videos"]):
    d.text((x - 4, 112 + i * 104), line, font=hf, fill=INK)
d.text((x, 438), "Product demos · UI animation · Launch ads", font=font("Archivo-Medium", 27), fill=INK)
strip = [("commas_checkout", "Commas"), ("offline_box", "OfflineIQ"), ("nano_physics", "NanoSyllabus")]
tw, th = 196, 110
for i, (nm, cap) in enumerate(strip):
    tx = x + i * (tw + 16)
    shadow_paste(img, rounded(still(nm, tw, th), 10), tx, 520, r=10, blur=10, alpha=60)
    d.text((tx, 642), cap.upper(), font=font("PlexMono-Medium", 14), fill=INK)
img.save(OUT / "gig-image-1-thumbnail.jpg", quality=93)

# ---------------------------------------------------------------- 2. recent work
img = Image.new("RGB", (W, H), INK)
d = ImageDraw.Draw(img)
d.text((40, 52), "Recent client work", font=font("ArchivoExp-ExtraBold", 50), fill=PAPER)
d.text((W - 40, 76), "2025 — 2026", font=font("PlexMono-Medium", 18), fill=LIME, anchor="ra")
tiles = [("commas_checkout", "Commas · SaaS launch"), ("offline_box", "OfflineIQ · Product film"),
         ("nano_physics", "NanoSyllabus · Ed-tech promo"), ("hive_built", "Neural Hive · Launch ad"),
         ("offline_doc", "OfflineIQ · Healthcare scene"), ("noor_story", "Noor Motion · Studio reel")]
tw, th, gap = 384, 216, 24
for i, (nm, cap) in enumerate(tiles):
    cx, cy = 40 + (i % 3) * (tw + gap), 150 + (i // 3) * (th + 66)
    t = rounded(still(nm, tw, th), 12)
    img.paste(t, (cx, cy), t)
    d.text((cx, cy + th + 14), cap, font=font("PlexMono-Medium", 16), fill=(206, 208, 200))
d.text((40, H - 52), "@aminur_rex", font=font("PlexMono-Medium", 16), fill=(150, 152, 144))
d.text((W - 40, H - 52), "Designed and animated by our team in Kolkata.", font=font("PlexMono-Medium", 16), fill=(150, 152, 144), anchor="ra")
img.save(OUT / "gig-image-2-recent-work.jpg", quality=93)

# ---------------------------------------------------------------- 3. how we work
img = Image.new("RGB", (W, H), PAPER)
d = ImageDraw.Draw(img)
x = 64
d.text((x, 64), "HOW WE WORK", font=font("PlexMono-Medium", 17), fill=MUTED)
d.text((x - 3, 98), "No", font=font("ArchivoExp-ExtraBold", 76), fill=INK)
d.text((x - 3, 180), "middlemen.", font=font("ArchivoExp-ExtraBold", 76), fill=INK)
d.rectangle((x, 286, x + 64, 292), fill=LIME)
body = ["You talk to the people who", "make your video. Message me", "before you order and I'll tell", "you what kind of video will", "actually work for your product."]
bf = font("Archivo-Medium", 25)
for i, line in enumerate(body):
    d.text((x, 320 + i * 36), line, font=bf, fill=INK)
facts = ["2,000+ videos delivered", "English & Bengali", "After Effects · Premiere Pro", "Kolkata, India · IST"]
mf = font("PlexMono-Medium", 17)
for i, ftxt in enumerate(facts):
    fy = 540 + i * 34
    d.rectangle((x, fy + 6, x + 8, fy + 14), fill=INK)
    d.text((x + 22, fy), ftxt, font=mf, fill=INK)

# right: the four steps (a real order, so they are numbered)
rx, rw = 640, 576
d.rounded_rectangle((rx - 24, 64, rx + rw, H - 64), 14, fill=(255, 255, 255))
d.text((rx + 12, 96), "A typical 60-second video", font=font("Archivo-Medium", 22), fill=MUTED)
steps = [("01", "Brief", "Goal, length and style agreed.", "DAY 1"),
         ("02", "Script & storyboard", "You approve every frame first.", "DAY 1–3"),
         ("03", "Animation & sound", "Motion, voice over, music, SFX.", "DAY 3–6"),
         ("04", "Delivery", "1080p or 4K, revisions included.", "DAY 7")]
for i, (n, title, line, day) in enumerate(steps):
    sy = 150 + i * 132
    if i:
        d.line((rx + 12, sy - 22, rx + rw - 36, sy - 22), fill=(222, 224, 216), width=2)
    d.rounded_rectangle((rx + 12, sy, rx + 64, sy + 52), 10, fill=LIME)
    d.text((rx + 38, sy + 26), n, font=font("PlexMono-Medium", 20), fill=INK, anchor="mm")
    d.text((rx + 88, sy - 2), title, font=font("ArchivoExp-ExtraBold", 28), fill=INK)
    d.text((rx + 88, sy + 40), line, font=font("Archivo-Medium", 21), fill=MUTED)
    d.text((rx + rw - 36, sy + 4), day, font=font("PlexMono-Medium", 15), fill=INK, anchor="ra")
img.save(OUT / "gig-image-3-how-we-work.jpg", quality=93)
print("ok", LIME)
