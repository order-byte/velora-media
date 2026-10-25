"""Crop/trim/grade stock clips into vertical 1080x1920 B-roll with one consistent low-key look."""
import subprocess, json, sys
OUT = "/home/user/work/reel/public/broll4"
# name: (source, in_sec, dur, crop_x 0..1, look)
CLIPS = {
 "tripod":     ("/home/user/work/broll2/tripod_place.mp4", 3.4, 2.6, 0.55, "bw"),
 "editclose":  ("/home/user/work/broll2/edit_closeup.mp4", 2.0, 2.0, 0.40, "bwlift"),
 "clock":      ("/home/user/work/broll2/clock_dark.mp4", 0.5, 2.2, 0.50, "bw"),
 "analytics":  ("/home/user/work/broll2/yt_analytics.mp4", 0.0, 2.6, 0.22, "bw"),
 "rubface":    ("/home/user/work/broll2/night_office.mp4", 5.4, 2.6, 0.62, "bw"),
 "yttripod":   ("/home/user/work/broll2/yt_tripod.mp4", 2.0, 2.0, 0.50, "lowkey"),
 "editoroff":  ("/home/user/work/broll/editor_office.mp4", 3.0, 1.6, 0.50, "lowkey"),
 "lumetri":    ("/home/user/work/broll2/lumetri.mp4", 3.0, 1.4, 0.40, "lowkey"),
 "scroll":     ("/home/user/work/broll/phone_scroll.mp4", 1.0, 2.0, 0.50, "lowkey"),
 "pay":        ("/home/user/work/broll2/online_pay.mp4", 0.8, 2.6, 0.45, "lowkey"),
 "cash":       ("/home/user/work/broll2/cash_falling.mp4", 7.4, 3.4, 0.50, "lowkey"),
 "ytstudio":   ("/home/user/work/broll2/yt_studio.mp4", 1.0, 1.6, 0.42, "lowkey"),
 "camgirl":    ("/home/user/work/broll2/influencer_cam.mp4", 1.0, 1.6, 0.50, "lowkey"),
 "vlogout":    ("/home/user/work/broll2/vlog_outdoor.mp4", 6.0, 1.6, 0.45, "lowkey"),
 "hourglass":  ("/home/user/work/broll2/hourglass_dark.mp4", 2.4, 3.2, 0.45, "lowkey"),
 "cashtop":    ("/home/user/work/broll2/cash_falling.mp4", 8.0, 1.0, 0.50, "lowkey"),
}
LOOK = {
 "bw": "hue=s=0,eq=contrast=1.22:brightness=-0.05:gamma=0.92,curves=all='0/0 0.25/0.16 0.6/0.6 1/0.96'",
 "bwlift": "hue=s=0,eq=contrast=1.15:brightness=0.06:gamma=1.15,curves=all='0/0 0.25/0.22 0.6/0.66 1/0.97'",
 "lowkey": "eq=contrast=1.12:brightness=-0.05:saturation=0.78:gamma=0.94,colorbalance=rs=-0.05:bs=0.06:gs=0.01:rh=0.05:bh=-0.04,curves=all='0/0 0.25/0.18 0.6/0.6 1/0.96'",
}
ONLY = sys.argv[1:]
for name, (src, t0, dur, cx, look) in CLIPS.items():
    if ONLY and name not in ONLY: continue
    w, h = map(int, subprocess.run(["ffprobe","-v","error","-select_streams","v","-show_entries","stream=width,height","-of","csv=p=0",src],capture_output=True,text=True).stdout.strip().split(","))
    if w / h > 9 / 16:
        cw = int(h * 9 / 16) // 2 * 2; x = int((w - cw) * cx)
        crop = f"crop={cw}:{h}:{x}:0,"
    else: crop = ""
    vf = f"{crop}scale=1080:1920:flags=lanczos,{LOOK[look]},unsharp=5:5:0.6:5:5:0.0,vignette=PI/4.2,fps=30,format=yuv420p"
    subprocess.run(["ffmpeg","-v","error","-y","-ss",str(t0),"-i",src,"-t",str(dur),"-vf",vf,"-an","-c:v","libx264","-preset","medium","-crf","17",f"{OUT}/{name}.mp4"], check=True)
    print("ok", name, flush=True)
