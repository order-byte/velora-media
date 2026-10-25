"""Cut-out of the speaker + table/can as VP9 alpha video (30 fps), warm bright soft grade, magenta edge despill."""
import sys, subprocess, numpy as np, cv2, onnxruntime as ort
src, dst = sys.argv[1], sys.argv[2]
so = ort.SessionOptions(); so.intra_op_num_threads = 4
sess = ort.InferenceSession('/home/user/work/models/modnet.onnx', so)
cap = cv2.VideoCapture(src); W = int(cap.get(3)); H = int(cap.get(4)); fps = cap.get(5)
step = max(1, round(fps / 30))
setm = np.zeros((H, W), np.float32); setm[1680:, :] = 1; setm[1165:, 645:895] = 1
setm = cv2.GaussianBlur(setm, (0, 0), 6)
def curve(pts):
    x, y = zip(*pts); return np.clip(np.interp(np.arange(256) / 255.0, x, y) * 255, 0, 255).astype(np.uint8)
LUT = curve([(0, 0.035), (0.2, 0.25), (0.45, 0.53), (0.7, 0.78), (1, 0.97)])
ff = subprocess.Popen(["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","bgra","-s",f"{W}x{H}","-r","30","-i","-",
    "-c:v","libvpx-vp9","-pix_fmt","yuva420p","-b:v","9M","-deadline","realtime","-cpu-used","6","-row-mt","1","-auto-alt-ref","0",dst], stdin=subprocess.PIPE)
prev = None; i = -1; n = 0
while True:
    ok, fr = cap.read(); i += 1
    if not ok: break
    if i % step: continue
    x = cv2.resize(fr, (288, 512), interpolation=cv2.INTER_AREA)[:, :, ::-1].astype(np.float32) / 255.0
    m = sess.run(None, {"input": ((x - 0.5) / 0.5).transpose(2, 0, 1)[None]})[0][0, 0]
    m = cv2.resize(m, (W, H)); m = prev * 0.4 + m * 0.6 if prev is not None else m; prev = m
    m = cv2.GaussianBlur(cv2.erode(np.clip(m, 0, 1), np.ones((5, 5), np.uint8)), (0, 0), 1.6)
    a = np.maximum(m, setm)
    g = cv2.LUT(cv2.addWeighted(fr, 1.35, cv2.GaussianBlur(fr, (0, 0), 1.4), -0.35, 0), LUT).astype(np.float32)
    g[:, :, 2] *= 1.05; g[:, :, 0] *= 0.94
    gl = cv2.GaussianBlur(np.clip(g - 170, 0, None), (0, 0), 18); g = g + gl * 0.35       # soft highlight glow
    edge = ((a > 0.03) & (a < 0.97))[:, :, None]                                          # despill magenta fringe
    gray = g.mean(2, keepdims=True); g = np.where(edge, gray + (g - gray) * 0.25, g)
    out = np.dstack([np.clip(g, 0, 255).astype(np.uint8), (a * 255).astype(np.uint8)])
    ff.stdin.write(out.tobytes()); n += 1
ff.stdin.close(); ff.wait(); print("frames", n)
