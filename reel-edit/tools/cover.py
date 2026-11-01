# Reel cover: scene-17 frame, dark grade, text behind the subject, floating profile card.
import os, sys, numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
os.environ.setdefault("REEL_FONTS", os.path.join(os.environ.get("REEL_WORK", os.path.join(ROOT, "work")), "fonts"))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "tools"))
import fx, render
from seg import Segmenter
cap = cv2.VideoCapture(os.path.join(ROOT, "work", "proxy", "IMG_4960.mp4")); cap.set(cv2.CAP_PROP_POS_MSEC, 9400)
ok, fr = cap.read(); fr = cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)
fr = fx.zoom(fr, 1.12, 0.5, 0.45)
fr = fx.grade(fr, "dark")
m = Segmenter(os.path.join(ROOT, "work", "models", "selfie_multiclass.tflite")).person(fr)
m = np.clip((cv2.GaussianBlur(m, (0, 0), 3) - 0.35) / 0.3, 0, 1)[..., None]
base = fr.copy(); out = fr.copy()
fx.place_center(out, render.L("HOW TO GET CLIENTS AS A", "W", 96), 540, 300)
fx.place_center(out, render.L("VIDEO", "WG", 420), 540, 600)
fx.place_center(out, render.L("EDITOR", "B", 330), 540, 930)
out = (base * m + out * (1 - m)).astype(np.uint8)
render.g_profile_card(out, 99, {"t0": 0}, {})
out = fx.grain(fx.sharpen(out, 0.3), 1, 5)
cv2.imwrite(sys.argv[1], cv2.cvtColor(out, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 93])
print("cover ok")
