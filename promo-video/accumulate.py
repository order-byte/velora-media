"""Average the sub-frames written by render.js into final frames and pipe them to ffmpeg.
Usage: python3 accumulate.py <subDir> <frameCount> <out.mp4> [fps]"""
import sys, os, glob, subprocess, time
import numpy as np
from PIL import Image
sub, count, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
fps = sys.argv[4] if len(sys.argv) > 4 else '30'
ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1920x1080', '-r', fps, '-i', '-',
                       '-c:v', 'libx264', '-preset', 'slow', '-crf', '14', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out],
                      stdin=subprocess.PIPE)
for f in range(count):
    done = os.path.join(sub, f'done_{f:05d}')
    while not os.path.exists(done):
        time.sleep(0.2)
    files = sorted(glob.glob(os.path.join(sub, f'f{f:05d}_*')))
    acc = None
    for p in files:
        a = np.asarray(Image.open(p).convert('RGB'), dtype=np.float32)
        acc = a if acc is None else acc + a
    frame = np.clip(acc / len(files) + 0.5, 0, 255).astype(np.uint8)
    ff.stdin.write(frame.tobytes())
    for p in files:
        os.remove(p)
ff.stdin.close(); ff.wait()
print('wrote', out)
