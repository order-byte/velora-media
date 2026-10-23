"""Person matte for a talking-head clip with Robust Video Matting (ONNX, CPU).

Writes a lossless grayscale alpha video (FFV1 .mkv) frame-aligned with the input.

Usage: python3 matte.py MODEL.onnx IN.mp4 OUT_alpha.mkv [--downsample 0.25] [--threads 4]
"""
import argparse
import json
import subprocess
import time

import numpy as np
import onnxruntime as ort


def probe(path):
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate", "-of", "json", path])
    s = json.loads(out)["streams"][0]
    return s["width"], s["height"], s["r_frame_rate"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--downsample", type=float, default=0.25)
    ap.add_argument("--threads", type=int, default=4)
    args = ap.parse_args()

    w, h, fps = probe(args.src)
    opts = ort.SessionOptions()
    opts.intra_op_num_threads = args.threads
    sess = ort.InferenceSession(args.model, opts, providers=["CPUExecutionProvider"])

    reader = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-i", args.src, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        stdout=subprocess.PIPE)
    writer = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{w}x{h}",
         "-r", fps, "-i", "-", "-c:v", "ffv1", args.out],
        stdin=subprocess.PIPE)

    rec = [np.zeros((1, 1, 1, 1), np.float32)] * 4
    ds = np.array([args.downsample], np.float32)
    n, t0 = 0, time.time()
    frame_bytes = w * h * 3
    while True:
        buf = reader.stdout.read(frame_bytes)
        if len(buf) < frame_bytes:
            break
        src = np.frombuffer(buf, np.uint8).reshape(h, w, 3).transpose(2, 0, 1)[None].astype(np.float32) / 255
        fgr, pha, *rec = sess.run(None, {"src": src, "r1i": rec[0], "r2i": rec[1], "r3i": rec[2],
                                         "r4i": rec[3], "downsample_ratio": ds})
        writer.stdin.write((np.clip(pha[0, 0], 0, 1) * 255 + 0.5).astype(np.uint8).tobytes())
        n += 1
        if n % 100 == 0:
            print(f"{n} frames, {n / (time.time() - t0):.1f} fps", flush=True)
    writer.stdin.close()
    writer.wait()
    reader.wait()
    print(f"done: {n} frames in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
