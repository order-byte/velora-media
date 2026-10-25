"""Speaker cut-out in RAW colours (no grade) as VP9 alpha + per-frame face track for camera tracking.
Exact can/table mask, old magenta wall spill removed from edges, table reflection recoloured to the new set, light wrap from the new set."""
import sys, json, subprocess, numpy as np, cv2, onnxruntime as ort
src, dst, plate_p, track_p = sys.argv[1:5]
so = ort.SessionOptions(); so.intra_op_num_threads = 4
sess = ort.InferenceSession('/home/user/work/models/modnet.onnx', so)
cap = cv2.VideoCapture(src); W = int(cap.get(3)); H = int(cap.get(4)); fps = cap.get(5); step = max(1, round(fps / 30))
setm = np.load('/home/user/work/final/setmask.npy'); TABLE = int(np.load('/home/user/work/final/tabletop.npy')[0])
pb = cv2.GaussianBlur(cv2.imread(plate_p).astype(np.float32), (0, 0), 30)
rowsY = np.arange(H)[:, None]
ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", "30", "-i", "-",
    "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "9M", "-deadline", "realtime", "-cpu-used", "6", "-row-mt", "1", "-auto-alt-ref", "0", dst], stdin=subprocess.PIPE)
prev = None; i = -1; track = []
while True:
    ok, fr = cap.read(); i += 1
    if not ok: break
    if i % step: continue
    x = cv2.resize(fr, (288, 512), interpolation=cv2.INTER_AREA)[:, :, ::-1].astype(np.float32) / 255.0
    m = sess.run(None, {"input": ((x - 0.5) / 0.5).transpose(2, 0, 1)[None]})[0][0, 0]
    m = cv2.resize(m, (W, H)); m = prev * 0.4 + m * 0.6 if prev is not None else m; prev = m
    m = cv2.GaussianBlur(cv2.erode(np.clip(m, 0, 1), np.ones((5, 5), np.uint8)), (0, 0), 1.6)
    # face track: top of the head + centroid of the head band
    rows = np.where((m[:1400] > 0.5).sum(1) > 40)[0]; top = int(rows[0]) if len(rows) else 520
    band = m[top:top + 260] > 0.5; cx = float((band.sum(0) * np.arange(W)).sum() / max(1, band.sum()))
    track.append([round(cx, 1), top + 230])
    a = np.maximum(m, setm)
    hsv = cv2.cvtColor(fr, cv2.COLOR_BGR2HSV)
    tab = (rowsY >= TABLE) & (hsv[..., 0] >= 130) & (hsv[..., 1] > 35) & (hsv[..., 2] < 90) & (m < 0.3)
    if tab.any():
        h2 = hsv.copy(); h2[..., 0][tab] = 62; h2[..., 1][tab] = (h2[..., 1][tab] * 0.7).astype(np.uint8)
        fr = cv2.cvtColor(h2, cv2.COLOR_HSV2BGR)
    g = fr.astype(np.float32)
    edge = np.clip(cv2.GaussianBlur(1 - a, (0, 0), 6) * 2.5, 0, 1)[..., None] * (a[..., None] > 0.02)
    mag = (((hsv[..., 0] >= 135) | (hsv[..., 0] <= 6)) & (hsv[..., 1] > 50)).astype(np.float32)[..., None]
    gray = g.mean(2, keepdims=True); g = g * (1 - edge * mag) + (gray + (g - gray) * 0.2) * edge * mag
    wrap = np.clip(cv2.GaussianBlur(1 - a, (0, 0), 9) * a * 2.2, 0, 1)[..., None] * 0.4
    g = g * (1 - wrap) + pb * wrap
    ff.stdin.write(np.dstack([np.clip(g, 0, 255).astype(np.uint8), (a * 255).astype(np.uint8)]).tobytes())
ff.stdin.close(); ff.wait()
json.dump(track, open(track_p, 'w')); print("frames", len(track))
