import sys, wave, numpy as np, json
from faster_whisper import WhisperModel
m = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8", cpu_threads=4)
for c in json.load(open('/home/user/work/edit/edl.json')):
    w = wave.open(f"/home/user/work/edit/chk/{c['id']}.wav"); a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32)/32768
    a = np.concatenate([np.zeros(8000, np.float32), a, np.zeros(8000, np.float32)])
    segs, _ = m.transcribe(a, language="hi", beam_size=5, condition_on_previous_text=False)
    print(f"{c['id']:12s} | {''.join(s.text for s in segs).strip()}  ||  {c['text']}", flush=True)
