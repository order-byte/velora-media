"""Forced-align the known words of every take (wav2vec2 CTC), so cuts land exactly.

Usage: python3 align_takes.py TAKES.json RAW.wav OUT_words.json
Writes {piece_id: [{"w", "s", "e"}, ...]} with times in the raw file.
"""
import json
import sys
import wave

import numpy as np
import torch
import torchaudio
import torchaudio.functional as F
from torchaudio.pipelines import WAV2VEC2_ASR_BASE_960H as BUNDLE


def load(path):
    w = wave.open(path)
    sr, ch = w.getframerate(), w.getnchannels()
    a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    return a.reshape(-1, ch).mean(1), sr


def main():
    takes, raw, out = sys.argv[1:4]
    pieces = json.load(open(takes))["pieces"]
    a, sr = load(raw)
    model = BUNDLE.get_model().eval()
    labels = BUNDLE.get_labels()
    idx = {c: i for i, c in enumerate(labels)}
    res = {}
    for p in pieces:
        s, e = p["win"]
        clip = torch.from_numpy(a[int(s * sr):int(e * sr)].copy())[None]
        clip = torchaudio.functional.resample(clip, sr, BUNDLE.sample_rate)
        with torch.inference_mode():
            em, _ = model(clip)
        em = torch.log_softmax(em, -1)
        words = p["say"].upper().replace("'", "'").split()
        tokens = [idx[c] for wd in words for c in wd if c in idx]
        ali, scores = F.forced_align(em, torch.tensor([tokens], dtype=torch.int32), blank=0)
        ali, scores = ali[0], scores[0].exp()
        spans = F.merge_tokens(ali, scores)
        ratio = clip.shape[1] / BUNDLE.sample_rate / em.shape[1]
        out_words, k = [], 0
        for wd in words:
            n = len([c for c in wd if c in idx])
            ws = spans[k:k + n]
            k += n
            out_words.append(dict(w=wd.lower(), s=round(s + ws[0].start * ratio, 3), e=round(s + ws[-1].end * ratio, 3),
                                  conf=round(float(np.mean([x.score for x in ws])), 2)))
        res[p["id"]] = out_words
        print(p["id"], " ".join(f"{x['w']}[{x['s']:.2f}-{x['e']:.2f}|{x['conf']}]" for x in out_words), flush=True)
    json.dump(res, open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
