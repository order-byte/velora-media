"""Word-level transcription of the raw clip with faster-whisper.

Usage: python3 transcribe.py <audio.wav> <out.json> [model]
"""
import json, sys, wave
import numpy as np
from faster_whisper import WhisperModel

audio, out = sys.argv[1], sys.argv[2]
model_name = sys.argv[3] if len(sys.argv) > 3 else "small"
model = WhisperModel(model_name, device="cpu", compute_type="int8", cpu_threads=4)
with wave.open(audio) as wf:  # 16 kHz mono s16 wav (PyAV-free path)
    pcm = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
segments, info = model.transcribe(pcm, word_timestamps=True, vad_filter=True, beam_size=5)
res = {"language": info.language, "duration": info.duration, "segments": []}
for s in segments:
    res["segments"].append({
        "start": s.start, "end": s.end, "text": s.text.strip(),
        "words": [{"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3), "p": round(w.probability, 3)} for w in s.words],
    })
    print(f"[{s.start:7.2f} -> {s.end:7.2f}] {s.text.strip()}", flush=True)
json.dump(res, open(out, "w"), indent=1)
