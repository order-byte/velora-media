# Reference frames at key moments, upscaled to the 1440x1014 output size, with a 120px grid for measuring.
import sys, cv2
from PIL import Image, ImageDraw
ref, out, times = sys.argv[1], sys.argv[2], [float(x) for x in sys.argv[3].split(",")]
cap = cv2.VideoCapture(ref)
tiles = []
for t in times:
    cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000); ok, fr = cap.read()
    im = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)).resize((1440, 1014)).resize((480, 338))
    d = ImageDraw.Draw(im)
    for x in range(120, 1440, 120):
        d.line([(x / 3, 0), (x / 3, 338)], fill=(255, 255, 0) if x % 360 else (255, 80, 80), width=1)
    for y in range(120, 1014, 120):
        d.line([(0, y / 3), (480, y / 3)], fill=(0, 255, 255) if y % 360 else (255, 80, 80), width=1)
    for x in range(360, 1440, 360): d.text((x / 3 + 2, 2), str(x), fill=(255, 80, 80))
    for y in range(360, 1014, 360): d.text((2, y / 3 + 2), str(y), fill=(255, 80, 80))
    d.rectangle([0, 322, 60, 338], fill="black"); d.text((3, 324), f"{t:.2f}", fill="white")
    tiles.append(im)
cols = 5; rows = (len(tiles) + cols - 1) // cols
s = Image.new("RGB", (cols * 480, rows * 338))
for i, im in enumerate(tiles): s.paste(im, ((i % cols) * 480, (i // cols) * 338))
s.save(out, quality=88)
