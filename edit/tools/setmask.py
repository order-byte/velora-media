"""Exact mask of the static set from the median frame: the Monster can (non-magenta pixels in its columns) + the table below its top edge."""
import numpy as np, cv2
TABLE = 1690
cap = cv2.VideoCapture('/home/user/work/final/cut.mp4'); n = int(cap.get(7)); fr = []
for i in np.linspace(0, n - 1, 60).astype(int):
    cap.set(1, int(i)); ok, f = cap.read()
    if ok: fr.append(f)
med = np.median(np.stack(fr), axis=0).astype(np.uint8)
hsv = cv2.cvtColor(med, cv2.COLOR_BGR2HSV); h, s = hsv[..., 0].astype(int), hsv[..., 1]
wall = (h >= 130) & (s > 45)                                       # magenta wall incl. its shadow side
H, W = med.shape[:2]; yy, xx = np.mgrid[0:H, 0:W]
can = ((xx >= 668) & (xx <= 878) & (yy >= 1150) & (yy < TABLE) & ~wall).astype(np.uint8)
can = cv2.morphologyEx(can, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8)); can = cv2.morphologyEx(can, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
n_, lab, st, _ = cv2.connectedComponentsWithStats(can); keep = np.zeros_like(can)
for i in range(1, n_):
    if st[i, cv2.CC_STAT_AREA] > 4000: keep[lab == i] = 1
keep = cv2.erode(keep, np.ones((3, 3), np.uint8)); keep[TABLE:, :] = 1
np.save('/home/user/work/final/setmask.npy', cv2.GaussianBlur(keep.astype(np.float32), (0, 0), 1.5))
np.save('/home/user/work/final/tabletop.npy', np.full(W, TABLE))
print("set share", keep.mean().round(3))
