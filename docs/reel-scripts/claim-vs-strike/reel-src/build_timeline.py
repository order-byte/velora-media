"""Lays the voiceover lines on a timeline with dramatic pauses and word-level timings.

Reads lines.json and vo_<speaker>/line_XX.wav, aligns every scripted word to a time with
Whisper word timestamps (falling back to an even spread), and writes timing.json/timing.js
for reel.html plus voice.wav (48 kHz mono) for the mix.
Usage: python build_timeline.py <vo_dir>
"""
import difflib
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel

HERE = Path(__file__).resolve().parent
SR = 48000
FPS = 30
LEAD = 1.4                     # globe forms before the first word
PAUSE_AFTER = [0.7, 0.6, 0.3, 0.35, 0.6, 0.7, 0.5, 0.8, 0.4, 0.5, 0.8, 0.6]
TAIL = 3.6                     # end card after the last word


def decode(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         check=True, capture_output=True).stdout
    a = np.frombuffer(raw, np.float32).copy()
    idx = np.where(np.abs(a) > 0.012)[0]
    return a[max(0, idx[0] - 960): idx[-1] + 2400] if idx.size else a


def norm(w):
    return re.sub(r"[।,?!.'\"…\-\s]", "", w)


def align(script_words, heard, dur):
    """Greedy in-order match of scripted words to recognised words."""
    out, j = [], 0
    for k, w in enumerate(script_words):
        best, best_r = None, 0.0
        for jj in range(j, min(j + 4, len(heard))):
            r = difflib.SequenceMatcher(None, norm(w), norm(heard[jj][0])).ratio()
            if r > best_r:
                best, best_r = jj, r
        if best is not None and best_r >= 0.45:
            out.append((heard[best][1], heard[best][2])); j = best + 1
        else:
            out.append(None)
    # fill gaps by spreading between known neighbours
    n = len(out)
    for k in range(n):
        if out[k] is None:
            prev = next((out[i][1] for i in range(k - 1, -1, -1) if out[i]), 0.0)
            nxt_i = next((i for i in range(k + 1, n) if out[i]), None)
            nxt = out[nxt_i][0] if nxt_i is not None else dur
            span = (nxt_i if nxt_i is not None else n) - k + 1
            s = prev + (nxt - prev) / span
            out[k] = (s, s + (nxt - prev) / span * 0.9)
    return out


def main():
    vo_dir = Path(sys.argv[1])
    lines = json.loads((HERE / "lines.json").read_text())
    model = WhisperModel("large-v3", device="cpu", compute_type="int8", cpu_threads=4,
                         download_root=str(HERE.parent / "stt" / "models"))
    t = LEAD
    out_lines, clips = [], []
    for i, text in enumerate(lines):
        audio = decode(vo_dir / f"line_{i:02d}.wav")
        dur = len(audio) / SR
        a16 = audio[::3].astype(np.float32)
        segs, _ = model.transcribe(a16, language="hi", beam_size=5, word_timestamps=True, condition_on_previous_text=False)
        heard = [(w.word.strip(), w.start, w.end) for s in segs for w in (s.words or [])]
        words = text.split()
        times = align(words, heard, dur)
        out_lines.append({"start": round(t, 3), "end": round(t + dur, 3), "text": text,
                          "words": [{"w": norm(w), "s": round(t + s, 3), "e": round(t + e, 3)} for w, (s, e) in zip(words, times)]})
        clips.append((t, audio))
        print(f"line {i:2d} {t:6.2f}-{t + dur:6.2f}  heard: {' '.join(h[0] for h in heard)}", flush=True)
        t += dur + (PAUSE_AFTER[i] if i < len(PAUSE_AFTER) else 0)
    duration = round(out_lines[-1]["end"] + TAIL, 3)
    timing = {"fps": FPS, "duration": duration, "lines": out_lines}
    (HERE / "timing.json").write_text(json.dumps(timing, ensure_ascii=False, indent=1))
    (HERE / "timing.js").write_text("window.TIMING = " + json.dumps(timing, ensure_ascii=False) + ";\n")
    voice = np.zeros(int(np.ceil(duration * SR)), np.float32)
    for start, audio in clips:
        a = int(start * SR); voice[a:a + len(audio)] += audio
    voice *= 0.9 / (np.abs(voice).max() + 1e-9)
    sf.write(HERE / "voice.wav", voice, SR)
    print(f"duration {duration:.2f}s")


if __name__ == "__main__":
    main()
