"""Low-key 'studio' grade: separate looks for subject (warm, contrasty), set pieces (darker) and wall (near-black teal, soft)."""
import sys, subprocess, numpy as np, cv2, onnxruntime as ort
src, dst = sys.argv[1], sys.argv[2]
LIMIT = int(sys.argv[3]) if len(sys.argv) > 3 else 10**9
so = ort.SessionOptions(); so.intra_op_num_threads = 4
sess = ort.InferenceSession('/home/user/work/models/modnet.onnx', so)
cap = cv2.VideoCapture(src); W = int(cap.get(3)); H = int(cap.get(4)); fps = cap.get(5)
setmask = np.zeros((H, W), np.float32); setmask[1675:, :] = 1; setmask[1170:, 640:900] = 1
setmask = cv2.GaussianBlur(setmask, (0, 0), 18)[:, :, None]
# tone curves (8-bit LUTs)
def curve(pts):
    x, y = zip(*pts); return np.clip(np.interp(np.arange(256) / 255.0, x, y) * 255, 0, 255).astype(np.uint8)
SUBJ = curve([(0, 0.0), (0.12, 0.06), (0.3, 0.24), (0.55, 0.56), (0.8, 0.84), (1, 0.97)])
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
vign = 1 - 0.55 * np.clip(((xx - W * 0.46) / (W * 0.75)) ** 2 + ((yy - H * 0.40) / (H * 0.62)) ** 2, 0, 1) ** 1.3
vign = vign[:, :, None]
def sat(img, s):
    g = img.mean(2, keepdims=True); return g + (img - g) * s
ff = None if dst.endswith('.png') else subprocess.Popen(["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","bgr24","-s",f"{W}x{H}","-r",str(fps),"-i","-",
    "-i",src,"-map","0:v","-map","1:a","-c:v","libx264","-preset","medium","-crf","15","-pix_fmt","yuv420p","-c:a","copy",dst], stdin=subprocess.PIPE)
prev = None; n = 0
while n < LIMIT:
    ok, fr = cap.read()
    if not ok: break
    x = cv2.resize(fr, (288, 512), interpolation=cv2.INTER_AREA)[:, :, ::-1].astype(np.float32) / 255.0
    m = sess.run(None, {"input": ((x - 0.5) / 0.5).transpose(2, 0, 1)[None]})[0][0, 0]
    m = cv2.resize(m, (W, H)); m = prev * 0.45 + m * 0.55 if prev is not None else m; prev = m
    a = cv2.GaussianBlur(cv2.erode(np.clip(m, 0, 1), np.ones((7, 7), np.uint8)), (0, 0), 2.4)[:, :, None]
    # subject: sharpen, warm, contrast curve, slightly reduced saturation
    sh = cv2.addWeighted(fr, 1.55, cv2.GaussianBlur(fr, (0, 0), 1.6), -0.55, 0)
    s = cv2.LUT(sh, SUBJ).astype(np.float32) / 255
    s[:, :, 2] *= 1.05; s[:, :, 1] *= 1.0; s[:, :, 0] *= 0.93
    s = sat(s, 0.86)
    # wall: soft, near-black, desaturated, teal shadows
    b = cv2.GaussianBlur(fr, (0, 0), 9).astype(np.float32) / 255
    b = sat(b, 0.22) * 0.30
    b[:, :, 0] += 0.022; b[:, :, 1] += 0.016; b[:, :, 2] *= 0.85
    # table + can: darker, keep detail
    t = sat(cv2.LUT(fr, SUBJ).astype(np.float32) / 255, 0.4) * 0.42
    bg = b * (1 - setmask) + t * setmask
    out = (s * a + bg * (1 - a)) * vign
    out = np.clip(out * 255, 0, 255).astype(np.uint8)
    if ff: ff.stdin.write(out.tobytes())
    else: cv2.imwrite(dst, np.hstack([fr, out])[::2, ::2]); break
    n += 1
if ff: ff.stdin.close(); ff.wait()
print("frames", n)
