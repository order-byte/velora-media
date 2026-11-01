import sys, os, cv2, numpy as np
from PIL import Image, ImageDraw
P = sys.argv[1]; out = sys.argv[2]
shots = [("R1", "IMG_4960", 6.2), ("R2", "IMG_4962", 14.5), ("R3", "IMG_4976", 1.0), ("R4", "IMG_4963", 3.9), ("R5", "IMG_4965", 5.0),
         ("R6", "IMG_4962", 23.6), ("R7", "IMG_4969", 1.0), ("R8", "IMG_4972", 3.2), ("R9", "IMG_4974", 2.6), ("R10", "IMG_4977", 1.0),
         ("R11", "AI_06a_film", 1.0), ("R12", "AI_06b_phone", 1.0), ("R13", "AI_kb_edit", 0.8), ("R14", "IMG_4966", 8.0), ("R17", "IMG_4978", 3.1),
         ("R18a", "IMG_4979", 7.8), ("R18b", "IMG_4979", 8.6), ("R18c", "IMG_4979", 9.4), ("R19", "IMG_4967", 7.0), ("R20", "IMG_4980", 6.5), ("R21a", "IMG_4982", 3.5),
         ("R21b", "IMG_4982", 7.5), ("R22", "IMG_4965", 0.8), ("R23", "AI_13_talk", 1.5), ("R24", "IMG_4962", 15.0), ("R25", "AI_kb_edit", 5.0),
         ("R26a", "AI_16_hand", 3.9), ("R26b", "AI_16_hand", 5.0), ("R27", "IMG_4960", 9.4), ("R29", "AI_18_eye", 1.0), ("R30", "IMG_4962", 16.5),
         ("R33", "AI_hp_work", 2.5), ("R34", "IMG_4985", 2.0), ("R25b", "AI_kb_edit", 3.4)]
tiles = []
for name, src, t in shots:
    cap = cv2.VideoCapture(os.path.join(P, src + ".mp4")); cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
    ok, fr = cap.read(); cap.release()
    im = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)).resize((270, 480))
    d = ImageDraw.Draw(im)
    for k in range(1, 6):
        x = k * 180 / 4; d.line([(x, 0), (x, 480)], fill=(255, 255, 0), width=1); d.text((x + 2, 2), str(k * 180), fill=(255, 255, 0))
    for k in range(1, 11):
        y = k * 180 / 4; d.line([(0, y), (270, y)], fill=(0, 255, 255), width=1); d.text((2, y + 2), str(k * 180), fill=(0, 255, 255))
    d.rectangle([0, 460, 270, 480], fill=(0, 0, 0)); d.text((4, 464), f"{name} {src} @{t}", fill=(255, 255, 255))
    tiles.append(im)
cols = 9; rows = (len(tiles) + cols - 1) // cols
sheet = Image.new("RGB", (cols * 270, rows * 480))
for i, im in enumerate(tiles): sheet.paste(im, ((i % cols) * 270, (i // cols) * 480))
sheet.save(out, quality=85)
