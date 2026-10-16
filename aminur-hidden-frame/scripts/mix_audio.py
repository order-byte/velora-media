"""Mix the voice, the sound-effect cue sheet and the music bed, then master for Instagram.

Usage: python mix_audio.py <voice.wav> <sfx_cues.json> <sfx_dir> <sfx_info.json> <duration_s> <out.wav> [music_dir]
- SFX are placed sample-accurately (align a cue's peak, onset or start to its `hit` time).
- If the cue sheet has a "music" section, the music bed is assembled from its segments
  (each: timeline `at`, source `src`, `dur`, fades, optional low-pass sweep and tape stop), then
  side-chain ducked under the voice.
- The mix is loudness-normalised to -14 LUFS with a -1 dBTP ceiling.
"""
import json, subprocess, sys
import numpy as np
from scipy.signal import butter, lfilter, lfilter_zi

voice, cues_path, sfx_dir, info_path, dur, out = sys.argv[1:7]
music_dir = sys.argv[7] if len(sys.argv) > 7 else None
dur = float(dur)
SR = 48000
N = int(round(dur * SR))


def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()


def fade(seg, fi, fo):
    n_in, n_out = min(len(seg), max(1, int(fi * SR))), min(len(seg), max(1, int(fo * SR)))
    seg[:n_in] *= np.linspace(0, 1, n_in)[:, None]
    seg[len(seg) - n_out:] *= np.linspace(1, 0, n_out)[:, None]
    return seg


def lowpass_sweep(seg, f_from, f_to, t0, t1, seg_start):
    """Block-wise 2nd-order low-pass whose cutoff glides (log scale) from f_from to f_to between t0 and t1."""
    outb = np.empty_like(seg)
    block = 256
    zi = None
    for i in range(0, len(seg), block):
        t = seg_start + i / SR
        k = min(1.0, max(0.0, (t - t0) / max(1e-6, t1 - t0)))
        fc = float(np.exp(np.log(f_from) + (np.log(f_to) - np.log(f_from)) * k))
        fc = min(fc, SR / 2 * 0.98)
        b, a = butter(2, fc / (SR / 2), btype="low")
        if zi is None:
            zi = np.stack([lfilter_zi(b, a) * seg[0, c] for c in range(2)])
        for c in range(2):
            outb[i:i + block, c], zi[c] = lfilter(b, a, seg[i:i + block, c], zi=zi[c])
    return outb


def tape_stop(seg, T):
    """Slow the last T seconds of seg to a halt, like a turntable losing power."""
    n, K = len(seg), min(len(seg), int(T * SR))
    if K < 2:
        return seg
    u = np.arange(K) / SR
    pos = (n - K) + (T / 2.5) * (1 - (1 - u / T) ** 2.5) * SR
    outb = seg.copy()
    for c in range(2):
        outb[n - K:, c] = np.interp(pos, np.arange(n), seg[:, c]) * np.linspace(1, 0.2, K)
    return outb


cues_doc = json.load(open(cues_path))
info = json.load(open(info_path))

# ---- SFX bus ----
bus = np.zeros((N + SR, 2), np.float32)
cache = {}
for c in cues_doc["cues"]:
    sid = str(c["id"])
    if sid not in cache:
        cache[sid] = load(f"{sfx_dir}/{sid}.wav")
    off = c.get("off", 0.0)
    seg = cache[sid][int(off * SR):]
    if c.get("dur"):
        seg = seg[: int(c["dur"] * SR)]
    seg = fade(seg.copy(), c.get("fadeIn", 0.004), c.get("fadeOut", 0.02))
    align = c.get("align", "peak")
    lead = {"peak": info[sid]["peakAt"], "onset": info[sid]["onset"], "start": 0.0}[align] - (off if align != "start" else 0.0)
    start = int(round((c["hit"] - max(0.0, lead)) * SR))
    if start < 0:
        seg, start = seg[-start:], 0
    end = min(len(bus), start + len(seg))
    bus[start:end] += seg[: end - start] * (10 ** (c["gain"] / 20))
bus = bus[:N]
bus.astype(np.float32).tofile(out + ".sfx.f32")

# ---- music bed ----
music = cues_doc.get("music")
mbus = np.zeros((N, 2), np.float32)
if music and music_dir:
    track = load(f"{music_dir}/{music['file']}")
    for sgm in music["segments"]:
        a = int(round(sgm["at"] * SR))
        src = int(round(sgm["src"] * SR))
        n = min(int(round(sgm["dur"] * SR)), len(track) - src, N - a)
        seg = track[src:src + n].copy()
        lp = sgm.get("lowpass")
        if lp:
            seg = lowpass_sweep(seg, lp["from"], lp["to"], lp["t0"], lp["t1"], sgm["at"])
        if sgm.get("tapeStop"):
            seg = tape_stop(seg, sgm["tapeStop"])
        seg = fade(seg, sgm.get("fadeIn", 0.005), sgm.get("fadeOut", 0.02)) * (10 ** (sgm.get("gain", 0.0) / 20))
        mbus[a:a + n] += seg
    mbus *= 10 ** (music.get("gain", -6.0) / 20)
mbus.astype(np.float32).tofile(out + ".music.f32")

duck = (music or {}).get("duck", {})
subprocess.run([
    "ffmpeg", "-v", "error", "-y",
    "-i", voice,
    "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", out + ".sfx.f32",
    "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", out + ".music.f32",
    "-filter_complex",
    f"[0:a]aresample={SR},apad=whole_dur={dur},asplit=3[v][k1][k2];"
    "[1:a]volume=-3dB,alimiter=limit=0.89:level=false[s];"
    "[s][k1]sidechaincompress=threshold=0.05:ratio=2.5:attack=8:release=180:makeup=1[sd];"
    f"[2:a][k2]sidechaincompress=threshold={duck.get('threshold', 0.03)}:ratio={duck.get('ratio', 4)}:"
    f"attack={duck.get('attack', 15)}:release={duck.get('release', 260)}:makeup=1[md];"
    "[v][sd][md]amix=inputs=3:normalize=0,alimiter=limit=0.95:level=false,"
    "loudnorm=I=-14:TP=-1.0:LRA=9:linear=true",
    "-ar", str(SR), "-c:a", "pcm_s16le", "-t", f"{dur}", out], check=True)
print("mixed", out)
