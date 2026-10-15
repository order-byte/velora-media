"""Person matte for the selects clip with Robust Video Matting (ONNX, CPU).

Usage: python matte_rvm.py <selects.mp4> <rvm_mobilenetv3_fp32.onnx> <matte_out.mp4>
Writes a grayscale matte video (white = person) at the source size and frame rate.
"""
import subprocess, sys
import numpy as np
import onnxruntime as ort

src, model, out = sys.argv[1:4]
W, H, FPS = 1080, 1920, 30
sess = ort.InferenceSession(model, providers=["CPUExecutionProvider"])
dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                       stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{W}x{H}",
                        "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "10",
                        "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
rec = [np.zeros([1, 1, 1, 1], dtype=np.float32)] * 4
ratio = np.array([0.25], dtype=np.float32)
n = 0
while True:
    buf = dec.stdout.read(W * H * 3)
    if len(buf) < W * H * 3:
        break
    img = np.frombuffer(buf, np.uint8).reshape(H, W, 3).astype(np.float32) / 255.0
    x = img.transpose(2, 0, 1)[None]
    fgr, pha, *rec = sess.run(None, {"src": x, "r1i": rec[0], "r2i": rec[1], "r3i": rec[2], "r4i": rec[3],
                                     "downsample_ratio": ratio})
    enc.stdin.write((np.clip(pha[0, 0], 0, 1) * 255).astype(np.uint8).tobytes())
    n += 1
    if n % 100 == 0:
        print("frames", n, flush=True)
enc.stdin.close(); enc.wait(); dec.wait()
print("done", n)
