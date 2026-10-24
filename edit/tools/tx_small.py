import sys, wave, numpy as np
from faster_whisper import WhisperModel
m = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8", cpu_threads=4)
for f in sys.argv[1:]:
    w=wave.open(f); a=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)/32768
    segs,_=m.transcribe(a, word_timestamps=True, language="hi", beam_size=5)
    off=float(f.split('_')[-1][:-4])
    print("==", f)
    for s in segs:
        print("  ", " ".join(f"{x.word.strip()}[{x.start+off:.2f}-{x.end+off:.2f}]" for x in s.words))
