"""Render the whole edit in parallel 30 s chunks.

Each chunk writes a 1080p video-only master piece and a 720p preview part with audio.
Usage: python3 render_chunks.py <edl> <raw> <broll_dir> <out_dir> [workers] [only_chunks e.g. 0,1,5]
"""
import json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

edl, raw, broll, out = sys.argv[1:5]
workers = int(sys.argv[5]) if len(sys.argv) > 5 else 3
dur = json.load(open(edl))["meta"]["duration"]
PART = 30.0
n = int(-(-dur // PART))
only = [int(x) for x in sys.argv[6].split(",")] if len(sys.argv) > 6 else list(range(n))
os.makedirs(os.path.join(out, "master"), exist_ok=True)
os.makedirs(os.path.join(out, "preview"), exist_ok=True)
here = os.path.dirname(os.path.abspath(__file__))


def job(i):
    a, b = i * PART, min(dur, (i + 1) * PART)
    m = os.path.join(out, "master", f"m{i:02d}.mp4")
    p = os.path.join(out, "preview", f"part{i:02d}.mp4")
    log = open(os.path.join(out, f"chunk{i:02d}.log"), "w")
    r = subprocess.run([sys.executable, "-I", os.path.join(here, "render.py"), "--edl", edl, "--raw", raw, "--broll", broll,
                        "--start", str(a), "--end", str(b), "--master", m + ".tmp.mp4", "--preview", p + ".tmp.mp4"],
                       stdout=log, stderr=subprocess.STDOUT)
    if r.returncode == 0:
        os.replace(m + ".tmp.mp4", m); os.replace(p + ".tmp.mp4", p)
        print(f"chunk {i:02d} ready", flush=True)
    else:
        print(f"chunk {i:02d} FAILED rc={r.returncode}", flush=True)
    return r.returncode


with ThreadPoolExecutor(workers) as ex:
    codes = list(ex.map(job, only))
print("all done" if not any(codes) else f"failures: {codes}", flush=True)
