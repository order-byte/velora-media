import json, sys
from faster_whisper import WhisperModel
import wave, numpy as np
model_name, audio, out = sys.argv[1], sys.argv[2], sys.argv[3]
m = WhisperModel(model_name, device="cpu", compute_type="int8", cpu_threads=4)
_w=wave.open(audio); audio=np.frombuffer(_w.readframes(_w.getnframes()),dtype=np.int16).astype(np.float32)/32768.0
segs, info = m.transcribe(audio, word_timestamps=True, vad_filter=False, beam_size=5,
    initial_prompt="Creators, yeh app abhi delete karo. Aminur Rex Team, Monthly Editing Package, Talking head, Podcast clips, Documentary, Cinematic vlog, Motion graphics, Faceless story, $200, 10 creators, 20 slots, comment karo EDIT, bio mein contact link.")
res = {"language": info.language, "segments": []}
for s in segs:
    res["segments"].append({"start": s.start, "end": s.end, "text": s.text,
        "words": [{"w": w.word, "s": w.start, "e": w.end, "p": w.probability} for w in (s.words or [])]})
    print(f"[{s.start:7.2f}-{s.end:7.2f}] {s.text}", flush=True)
json.dump(res, open(out, "w"), ensure_ascii=False, indent=1)
