import sys, wave, json, numpy as np
from faster_whisper import WhisperModel
w = wave.open(sys.argv[1]); a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32)/32768.0
m = WhisperModel(sys.argv[3] if len(sys.argv) > 3 else "small", device="cpu", compute_type="int8")
segs, info = m.transcribe(a, beam_size=5, word_timestamps=True, vad_filter=False)
out = {"lang": info.language, "segments": []}
for s in segs:
    out["segments"].append({"start": s.start, "end": s.end, "text": s.text, "words": [[x.start, x.end, x.word] for x in (s.words or [])]})
    print(f"[{s.start:6.2f} - {s.end:6.2f}] {s.text}", flush=True)
json.dump(out, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
print("LANG", info.language)
