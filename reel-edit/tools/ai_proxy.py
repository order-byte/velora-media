# AI clips -> 30fps 1080x1920 proxies with the corner sparkle watermark inpainted.
import subprocess, sys, os, numpy as np, cv2
W, H = 1080, 1920
src, dst = sys.argv[1], sys.argv[2]
mask = np.zeros((H, W), np.uint8); cv2.circle(mask, (900, 1740), 52, 255, -1)
dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-vf", f"fps=30,scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", "30", "-i", "-",
                        "-c:v", "libx264", "-preset", "fast", "-crf", "16", "-pix_fmt", "yuv420p", dst], stdin=subprocess.PIPE)
n = 0
while True:
    b = dec.stdout.read(W * H * 3)
    if len(b) < W * H * 3: break
    f = np.frombuffer(b, np.uint8).reshape(H, W, 3)
    roi = f[1640:1840, 800:1000].copy()
    fixed = cv2.inpaint(roi, mask[1640:1840, 800:1000], 9, cv2.INPAINT_TELEA)
    f = f.copy(); f[1640:1840, 800:1000] = fixed
    enc.stdin.write(f.tobytes()); n += 1
enc.stdin.close(); enc.wait(); print(os.path.basename(dst), n, "frames")
