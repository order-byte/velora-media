import wave, numpy as np, json, re
from faster_whisper import WhisperModel
m = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8", cpu_threads=4)
edl = json.load(open('/home/user/work/edit/edl.json'))
for c in edl:
    w = wave.open(f"/home/user/work/edit/chk/{c['id']}.wav"); a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32)/32768
    pad = 0.5; a = np.concatenate([np.zeros(int(16000*pad), np.float32), a])
    segs, _ = m.transcribe(a, language="en", beam_size=5, word_timestamps=True, initial_prompt=c['text'], condition_on_previous_text=False)
    ww = [(x.word.strip(), max(0, x.start-pad), max(0, x.end-pad)) for s in segs for x in s.words]
    exp = c['text'].split()
    if len(ww) == len(exp):
        words = [{"w": e, "s": round(s,3), "e": round(t,3)} for e,(_,s,t) in zip(exp, ww)]
        mode = "match"
    else:
        s0 = ww[0][1] if ww else 0.05; s1 = ww[-1][2] if ww else (c['out']-c['in'])
        L = [len(re.sub(r'\W','',e)) + 1 for e in exp]; tot = sum(L); t = s0; words = []
        for e, l in zip(exp, L):
            d = (s1 - s0) * l / tot; words.append({"w": e, "s": round(t,3), "e": round(t+d,3)}); t += d
        mode = f"prop ({len(ww)} vs {len(exp)})"
    c['words'] = words
    print(f"{c['id']:12s} {mode:14s} " + ' '.join(f"{x['w']}@{x['s']:.2f}" for x in words), flush=True)
json.dump(edl, open('/home/user/work/edit/edl.json','w'), indent=1, ensure_ascii=False)
