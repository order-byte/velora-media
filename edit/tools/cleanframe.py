"""Sharp, text-free frame of the reference set: align several sharp frames (ECC affine on the shelf area) and take the median."""
import cv2, numpy as np, sys
cap = cv2.VideoCapture('/home/user/work/final/refs/ig_bg.mp4')
def grab(t):
    cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000); ok, f = cap.read(); return f
times = [24.5, 13.0, 77.0, 31.5, 59.5, 69.0, 27.0, 46.5, 18.0, 36.0, 52.0, 64.0]
ref = grab(times[0]); g0 = cv2.cvtColor(ref[:700], cv2.COLOR_BGR2GRAY).astype(np.float32)
out = [ref.astype(np.float32)]
for t in times[1:]:
    f = grab(t)
    if f is None: continue
    hsv = cv2.cvtColor(f[:700], cv2.COLOR_BGR2HSV)
    if f[:700].mean() > 140 or (hsv[..., 1] > 80).mean() < 0.3: continue
    g = cv2.cvtColor(f[:700], cv2.COLOR_BGR2GRAY).astype(np.float32)
    M = np.eye(2, 3, dtype=np.float32)
    try:
        _, M = cv2.findTransformECC(g0, g, M, cv2.MOTION_AFFINE, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 100, 1e-5), None, 5)
    except cv2.error:
        continue
    al = cv2.warpAffine(f, M, (1080, 1920), flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REPLICATE)
    out.append(al.astype(np.float32)); print(t, np.round(M, 3).tolist())
st = np.stack(out); med = np.median(st, axis=0)
med[480:660] = np.percentile(st[:, 480:660], 15, axis=0)      # caption band: white words are brighter than the set -> low percentile drops them
med = med.astype(np.uint8)
cv2.imwrite(sys.argv[1], med); print("frames", len(out))
