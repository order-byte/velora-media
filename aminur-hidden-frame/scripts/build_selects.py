"""Cut the raw take into one continuous selects clip (graded video + cleaned voice).

Usage: python build_selects.py <raw.mp4> <edl.json> <out_dir>
Writes selects.mp4 (H.264, 1080x1920, 30 fps), voice.wav and timeline.json
(each clip's start/end on the edit timeline, used by the Remotion composition).
"""
import json, os, subprocess, sys

raw, edl_path, out = sys.argv[1], sys.argv[2], sys.argv[3]
edl = json.load(open(edl_path))
fps = edl["fps"]
tmp = os.path.join(out, "clips")
os.makedirs(tmp, exist_ok=True)
GRADE = ("eq=contrast=1.07:saturation=0.78:gamma=0.98,"
         "colorbalance=rs=0.04:gs=0.0:bs=-0.05:rm=0.03:bm=-0.03:rh=0.02:bh=-0.02,"
         "curves=all='0/0.035 0.5/0.5 1/0.97'")
t, timeline, listing = 0.0, [], []
for i, c in enumerate(edl["clips"]):
    # snap to whole frames so video and audio cut on the same boundary
    a = round(c["in"] * fps) / fps
    b = round(c["out"] * fps) / fps
    freeze = c.get("freeze", 0.0)
    dur = b - a
    vf = GRADE + (f",tpad=stop_mode=clone:stop_duration={freeze}" if freeze else "") + ",format=yuv420p"
    af = f"afade=t=in:d=0.012,afade=t=out:st={dur - 0.02:.3f}:d=0.02" + (f",apad=pad_dur={freeze}" if freeze else "")
    clip = os.path.join(tmp, f"{i:02d}_{c['id']}.mov")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.4f}", "-t", f"{dur:.4f}", "-i", raw,
                    "-vf", vf, "-af", af, "-r", str(fps), "-c:v", "libx264", "-preset", "medium", "-crf", "14",
                    "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2", clip], check=True)
    listing.append(f"file '{clip}'")
    total = dur + freeze
    timeline.append({"id": c["id"], "text": c["text"], "start": round(t, 4), "end": round(t + total, 4),
                     "srcIn": a, "srcOut": b, "freeze": freeze})
    t += total
open(os.path.join(tmp, "list.txt"), "w").write("\n".join(listing) + "\n")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", os.path.join(tmp, "list.txt"),
                "-map", "0:v", "-c:v", "copy", "-an", "-movflags", "+faststart", f"{out}/selects.mp4"], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", os.path.join(tmp, "list.txt"),
                "-map", "0:a", "-af",
                "highpass=f=85,afftdn=nr=10:nf=-45,acompressor=threshold=-20dB:ratio=3:attack=5:release=80:makeup=2,"
                "loudnorm=I=-15:TP=-1.5:LRA=7,aresample=48000",
                "-c:a", "pcm_s16le", f"{out}/voice.wav"], check=True)
json.dump({"fps": fps, "duration": round(t, 4), "clips": timeline}, open(f"{out}/timeline.json", "w"), indent=1)
print(f"selects: {len(timeline)} clips, {t:.2f}s")
