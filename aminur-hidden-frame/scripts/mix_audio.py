"""Mix the voice with the sound-effect cue sheet and master for Instagram.

Usage: python mix_audio.py <voice.wav> <sfx_cues.json> <sfx_dir> <sfx_info.json> <duration_s> <out.wav>
SFX are placed sample-accurately, the SFX bus is ducked under the voice, then the
mix is loudness-normalised to -14 LUFS with a -1 dBTP ceiling.
"""
import json, subprocess, sys
import numpy as np

voice, cues_path, sfx_dir, info_path, dur, out = sys.argv[1:7]
dur = float(dur)
SR = 48000

def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()

info = json.load(open(info_path))
bus = np.zeros((int(dur * SR) + SR, 2), np.float32)
cache = {}
for c in json.load(open(cues_path))["cues"]:
    sid = str(c["id"])
    if sid not in cache:
        cache[sid] = load(f"{sfx_dir}/{sid}.wav")
    a = cache[sid]
    off = c.get("off", 0.0)
    seg = a[int(off * SR):]
    if c.get("dur"):
        seg = seg[: int(c["dur"] * SR)]
    seg = seg.copy()
    fi, fo = c.get("fadeIn", 0.004), c.get("fadeOut", 0.02)
    n_in, n_out = max(1, int(fi * SR)), max(1, int(fo * SR))
    seg[:n_in] *= np.linspace(0, 1, min(n_in, len(seg)))[:, None][: len(seg[:n_in])]
    seg[-n_out:] *= np.linspace(1, 0, min(n_out, len(seg)))[:, None][-len(seg[-n_out:]):]
    align = c.get("align", "peak")
    lead = {"peak": info[sid]["peakAt"], "onset": info[sid]["onset"], "start": 0.0}[align] - (off if align != "start" else 0.0)
    start = int(round((c["hit"] - max(0.0, lead)) * SR))
    if start < 0:
        seg, start = seg[-start:], 0
    end = min(len(bus), start + len(seg))
    bus[start:end] += seg[: end - start] * (10 ** (c["gain"] / 20))
bus = bus[: int(dur * SR)]
bus.astype(np.float32).tofile(out + ".sfx.f32")
subprocess.run([
    "ffmpeg", "-v", "error", "-y",
    "-i", voice,
    "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", out + ".sfx.f32",
    "-filter_complex",
    f"[0:a]aresample={SR},apad=whole_dur={dur},asplit=2[v][key];"
    "[1:a]volume=-3dB,alimiter=limit=0.89:level=false[s];"
    "[s][key]sidechaincompress=threshold=0.05:ratio=2.5:attack=8:release=180:makeup=1[sd];"
    "[v][sd]amix=inputs=2:normalize=0,alimiter=limit=0.95:level=false,"
    "loudnorm=I=-14:TP=-1.0:LRA=9:linear=true",
    "-ar", str(SR), "-c:a", "pcm_s16le", "-t", f"{dur}", out], check=True)
print("mixed", out)
