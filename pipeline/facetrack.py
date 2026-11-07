"""Sample the raw clip and record the speaker's face box over time.

Usage: python3 facetrack.py <raw.mp4> <cascade.xml> <out.json> [step_seconds]
Output: {"w":1920,"h":1080,"samples":[[t,cx,cy,fw], ...]} in source pixels.
"""
import json, subprocess, sys
import numpy as np, cv2

src, cascade_path, out = sys.argv[1:4]
step = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
W, H, SW, SH = 1920, 1080, 640, 360
proc = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-vf", f"fps=1/{step},scale={SW}:{SH}",
                         "-f", "rawvideo", "-pix_fmt", "gray", "-"], stdout=subprocess.PIPE)
cas = cv2.CascadeClassifier(cascade_path)
samples, i = [], 0
while True:
    buf = proc.stdout.read(SW * SH)
    if len(buf) < SW * SH:
        break
    g = np.frombuffer(buf, np.uint8).reshape(SH, SW)
    faces = cas.detectMultiScale(g, scaleFactor=1.1, minNeighbors=6, minSize=(40, 40))
    if len(faces):
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        k = W / SW
        samples.append([round(i * step, 2), round((x + w / 2) * k, 1), round((y + h / 2) * k, 1), round(w * k, 1)])
    i += 1
json.dump({"w": W, "h": H, "step": step, "samples": samples}, open(out, "w"))
a = np.array(samples)
print(f"{len(samples)}/{i} frames with a face; cx {a[:,1].min():.0f}-{a[:,1].max():.0f} (med {np.median(a[:,1]):.0f}), "
      f"cy {a[:,2].min():.0f}-{a[:,2].max():.0f} (med {np.median(a[:,2]):.0f}), fw med {np.median(a[:,3]):.0f}")
