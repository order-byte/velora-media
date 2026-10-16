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
# Premium natural grade. The raw is 10-bit HDR HLG (BT.2020): light denoise on the 10-bit source,
# hable tone-map to SDR BT.709 (keeps contrast and holds the highlights on the face), the neon-green
# wall light pulled down to a deep emerald, skin calmed from orange, the lilac shirt calmed so the
# blue F1-car mic and the face lead, a gentle S-curve, warm highlights / cool shadows, a soft
# vignette for depth, then local contrast (large-radius unsharp) + CAS for crisp detail.
GRADE = ("hqdn3d=1.2:1.6:3:4,"
         "zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,"
         "tonemap=tonemap=hable:desat=0:peak=4.9,zscale=t=bt709:m=bt709:r=tv,format=gbrp,"
         "huesaturation=saturation=-0.45:hue=6:colors=g+c:strength=15,"
         "huesaturation=saturation=-0.2:hue=-3:colors=r+y:strength=10,"
         "huesaturation=saturation=-0.32:colors=m:strength=12,"
         "curves=all='0/0 0.1/0.09 0.5/0.56 0.85/0.9 1/0.97',"
         "colorbalance=rs=-0.015:bs=0.02:rh=0.025:gh=0.008:bh=-0.02,eq=saturation=1.03:brightness=0.035,"
         "vignette=angle=0.2:eval=init,"
         "format=yuv420p,unsharp=13:13:0.45:5:5:0,cas=strength=0.45:planes=1")
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
                    "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
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
