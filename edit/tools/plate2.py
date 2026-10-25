"""Shelf-only background plate: median of shelf area (person/graphics removed), then shelf rows tiled down to fill the frame."""
import sys, numpy as np, cv2, onnxruntime as ort
src, dst = sys.argv[1], sys.argv[2]
so = ort.SessionOptions(); so.intra_op_num_threads = 4
sess = ort.InferenceSession('/home/user/work/models/modnet.onnx', so)
cap = cv2.VideoCapture(src); n = int(cap.get(7)); W = int(cap.get(3)); H = int(cap.get(4))
TOP = int(H * 0.46)
stack = []
for i in np.linspace(0, n - 1, 120).astype(int):
    cap.set(1, int(i)); ok, fr = cap.read()
    if not ok: continue
    hsv = cv2.cvtColor(fr[:TOP], cv2.COLOR_BGR2HSV)
    if fr[:TOP].mean() > 150 or hsv[:, :, 1].mean() < 60: continue   # skip white graphic screens
    x = cv2.resize(fr, (288, 512))[:, :, ::-1].astype(np.float32) / 255.0
    m = sess.run(None, {"input": ((x - 0.5) / 0.5).transpose(2, 0, 1)[None]})[0][0, 0]
    m = cv2.dilate((cv2.resize(m, (W, H)) > 0.2).astype(np.uint8), np.ones((51, 51), np.uint8)).astype(bool)
    f = fr[:TOP].astype(np.float32); f[m[:TOP]] = np.nan; stack.append(f)
top = np.nanmedian(np.stack(stack), axis=0)
hole = np.isnan(top).any(axis=2).astype(np.uint8) * 255
top = cv2.inpaint(np.nan_to_num(top).astype(np.uint8), hole, 9, cv2.INPAINT_TELEA)
cv2.imwrite(dst.replace('.png', '_top.png'), top)
print("frames used", len(stack), "hole share", round((hole > 0).mean(), 3))
