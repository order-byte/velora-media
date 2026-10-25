"""Raw-colour composite test: speaker (MODNet matte + exact can/table mask, magenta edge cleanup, light wrap) over a plate."""
import sys, numpy as np, cv2, onnxruntime as ort
plate_p, out_p = sys.argv[1], sys.argv[2]; times = [float(t) for t in sys.argv[3].split(',')]
sess = ort.InferenceSession('/home/user/work/models/modnet.onnx')
plate = cv2.imread(plate_p).astype(np.float32); pb = cv2.GaussianBlur(plate, (0, 0), 30)
cap = cv2.VideoCapture('/home/user/work/final/cut.mp4'); H, W = 1920, 1080
setm = np.load('/home/user/work/final/setmask.npy')
outs = []
for t in times:
    cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000); ok, fr = cap.read()
    x = cv2.resize(fr, (288, 512), interpolation=cv2.INTER_AREA)[:, :, ::-1].astype(np.float32) / 255.0
    m = sess.run(None, {"input": ((x - 0.5) / 0.5).transpose(2, 0, 1)[None]})[0][0, 0]
    m = cv2.GaussianBlur(cv2.erode(np.clip(cv2.resize(m, (W, H)), 0, 1), np.ones((5, 5), np.uint8)), (0, 0), 1.6)
    a = np.maximum(m, setm)
    g = fr.astype(np.float32)
    hsv0 = cv2.cvtColor(fr, cv2.COLOR_BGR2HSV); tt = np.load('/home/user/work/final/tabletop.npy')
    tab = (np.arange(H)[:, None] >= tt[None, :]) & (hsv0[..., 0] >= 130) & (hsv0[..., 1] > 35) & (hsv0[..., 2] < 90) & (cv2.resize(m, (W, H)) < 0.3)
    if tab.any():
        h2 = hsv0.copy(); h2[..., 0] = np.where(tab, 62, h2[..., 0]); h2[..., 1] = np.where(tab, (h2[..., 1] * 0.7).astype(np.uint8), h2[..., 1])
        g = cv2.cvtColor(h2, cv2.COLOR_HSV2BGR).astype(np.float32)
    edge = np.clip(cv2.GaussianBlur(1 - a, (0, 0), 6) * 2.5, 0, 1)[..., None] * (a[..., None] > 0.02)
    hsv = cv2.cvtColor(fr, cv2.COLOR_BGR2HSV); mag = (((hsv[..., 0] >= 135) | (hsv[..., 0] <= 6)) & (hsv[..., 1] > 50)).astype(np.float32)[..., None]
    gray = g.mean(2, keepdims=True); g = g * (1 - edge * mag) + (gray + (g - gray) * 0.2) * edge * mag   # kill magenta wall spill on edges
    wrap = np.clip(cv2.GaussianBlur(1 - a, (0, 0), 9) * a * 2.2, 0, 1)[..., None] * 0.4
    g = g * (1 - wrap) + pb * wrap
    comp = plate * (1 - a[..., None]) + g * a[..., None]
    outs.append(cv2.resize(comp, (432, 768), interpolation=cv2.INTER_AREA))
cv2.imwrite(out_p, np.hstack(outs).astype(np.uint8))
