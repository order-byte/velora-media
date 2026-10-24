"""Portrait-mode background blur: MODNet person matte + static mask for table/can, light Gaussian blur on the wall."""
import sys, subprocess, numpy as np, cv2, onnxruntime as ort
src, dst = sys.argv[1], sys.argv[2]
SIGMA = float(sys.argv[3]) if len(sys.argv) > 3 else 7.0
LIMIT = int(sys.argv[4]) if len(sys.argv) > 4 else 10**9
so = ort.SessionOptions(); so.intra_op_num_threads = 4
sess = ort.InferenceSession('/home/user/work/models/modnet.onnx', so)
cap = cv2.VideoCapture(src); W = int(cap.get(3)); H = int(cap.get(4)); fps = cap.get(5)
# static foreground: table edge + energy can stay sharp (same depth as the subject)
static = np.zeros((H, W), np.float32)
static[1675:, :] = 1.0
static[1170:, 640:900] = 1.0
static = cv2.GaussianBlur(static, (0, 0), 18)
ff = None
if not dst.endswith('.png'):
    ff = subprocess.Popen(["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","bgr24","-s",f"{W}x{H}","-r",str(fps),"-i","-",
        "-i",src,"-map","0:v","-map","1:a","-c:v","libx264","-preset","medium","-crf","16","-pix_fmt","yuv420p","-c:a","copy",dst], stdin=subprocess.PIPE)
prev = None; n = 0
while n < LIMIT:
    ok, fr = cap.read()
    if not ok: break
    x = cv2.resize(fr, (288, 512), interpolation=cv2.INTER_AREA)[:, :, ::-1].astype(np.float32) / 255.0
    x = ((x - 0.5) / 0.5).transpose(2, 0, 1)[None]
    m = sess.run(None, {"input": x})[0][0, 0]
    m = cv2.resize(m, (W, H), interpolation=cv2.INTER_LINEAR)
    m = prev * 0.45 + m * 0.55 if prev is not None else m   # temporal smoothing against flicker
    prev = m
    a = np.clip(np.maximum(m, static), 0, 1)
    a = cv2.GaussianBlur(a, (0, 0), 2.0)[:, :, None]
    bg = cv2.GaussianBlur(fr, (0, 0), SIGMA)
    out = (fr.astype(np.float32) * a + bg.astype(np.float32) * (1 - a)).astype(np.uint8)
    if ff: ff.stdin.write(out.tobytes())
    else:
        cv2.imwrite(dst, np.hstack([fr, out, (np.repeat(a, 3, 2) * 255).astype(np.uint8)])[::2, ::2]); break
    n += 1
if ff: ff.stdin.close(); ff.wait()
print("frames", n)
