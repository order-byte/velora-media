"""Pre-compute the speaker's alpha matte (Robust Video Matting) for time ranges
that need graphics behind the speaker.

Usage: python3 matte.py <raw.mp4> <rvm.onnx> <out_dir> start:end [start:end ...]
Writes <out_dir>/matte_<start>_<end>.npy  (N, 540, 960) uint8, frame k = start + k/30 s.
Starts should be whole seconds so frames line up with the renderer's 30 fps grid.
"""
import os, subprocess, sys
import numpy as np, onnxruntime as ort, cv2

raw, model, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
W, H = 1920, 1080
sess = ort.InferenceSession(model, providers=["CPUExecutionProvider"])
for rng in sys.argv[4:]:
    a, b = (float(x) for x in rng.split(":"))
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{a:.3f}", "-i", raw, "-t", f"{b - a:.3f}", "-vf", "fps=30",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    rec = [np.zeros([1, 1, 1, 1], np.float32)] * 4
    dr = np.array([0.25], np.float32)
    frames = []
    while True:
        buf = p.stdout.read(W * H * 3)
        if len(buf) < W * H * 3:
            break
        f = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        src = (f.astype(np.float32) / 255).transpose(2, 0, 1)[None]
        _, pha, *rec = sess.run(None, {"src": src, "r1i": rec[0], "r2i": rec[1], "r3i": rec[2], "r4i": rec[3],
                                       "downsample_ratio": dr})
        frames.append(cv2.resize((pha[0, 0] * 255).astype(np.uint8), (960, 540), interpolation=cv2.INTER_AREA))
    np.save(os.path.join(out, f"matte_{a:g}_{b:g}.npy"), np.stack(frames))
    print(f"{rng}: {len(frames)} frames", flush=True)
