"""Transcribes generated voiceover lines back to text, to catch garbled or cut-off lines."""
import glob, json, os, subprocess, sys
import numpy as np
from faster_whisper import WhisperModel
d = sys.argv[1]
lines = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lines.json")))
m = WhisperModel("large-v3", device="cpu", compute_type="int8", cpu_threads=4,
                 download_root="/tmp/claude-0/-home-user-velora-media/66ff1a82-31ea-5c05-a6ba-b6463a076dc9/scratchpad/stt/models")
for f in sorted(glob.glob(os.path.join(d, "line_*.wav"))):
    i = int(f[-6:-4])
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"], capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.float32)
    segs, _ = m.transcribe(a, language="hi", beam_size=5, condition_on_previous_text=False)
    heard = " ".join(s.text.strip() for s in segs)
    peak = float(np.abs(a).max())
    print(f"[{i:02d}] {len(a)/16000:4.1f}s peak {peak:.2f}\n  want: {lines[i]}\n  got : {heard}", flush=True)
