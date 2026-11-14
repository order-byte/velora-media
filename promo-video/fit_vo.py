"""Place an ElevenLabs voiceover onto the promo timeline and mix it with the SFX track.

Usage: python fit_vo.py <voice.mp3|wav> <sfx_track.wav> <silent_video.mp4> <out_dir>

The voice file is the whole SCRIPT.md read in one go. Whisper finds each word. For every one of the
8 lines the tool:
  1. cuts the line out of the read,
  2. shortens pauses inside the line that are longer than the line's pause limit,
  3. speeds the line up (pitch kept, Rubber Band) only as much as needed to fit its slot, up to MAX_SPEED,
  4. places it at the slot start, or right after the previous line if that one ran long.
Writes vo_aligned.wav, mix.wav and the final video with sound.
Needs: faster-whisper, librosa, soundfile, numpy, and ffmpeg with the rubberband filter.
"""
import json, os, re, subprocess, sys
import numpy as np
import soundfile as sf

SR = 48000
# (first word of the line, slot start, slot end, longest pause kept inside the line)
LINES = [
    ("want",    0.05,  1.70, 0.16),
    ("say",     1.72,  3.60, 0.16),
    ("the",     3.62,  5.94, 0.16),
    ("explore", 5.96, 12.70, 0.18),
    ("punchy", 12.72, 14.40, 0.12),
    ("with",   14.42, 16.36, 0.12),
    ("drag",   16.38, 17.60, 0.14),
    ("you",    17.64, 21.40, 0.16),
]
MAX_SPEED = 1.25
GAP = 0.04          # smallest gap between two lines when one runs long
TOTAL = 22.0


def ff(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def load(path):
    tmp = path + ".48k.wav"
    ff("-i", path, "-ac", "1", "-ar", str(SR), "-c:a", "pcm_f32le", tmp)
    y, _ = sf.read(tmp, dtype="float32")
    os.remove(tmp)
    return y


def words_of(y):
    from faster_whisper import WhisperModel
    import librosa
    y16 = librosa.resample(y, orig_sr=SR, target_sr=16000)
    m = WhisperModel("medium.en", device="cpu", compute_type="int8")
    segs, _ = m.transcribe(y16, word_timestamps=True, beam_size=5)
    return [(re.sub(r"[^a-z]", "", w.word.lower()), w.start, w.end) for s in segs for w in s.words]


def xfade_join(parts, n=int(0.010 * SR)):
    out = parts[0]
    for p in parts[1:]:
        if len(out) > n and len(p) > n:
            ramp = np.linspace(0, 1, n, dtype=np.float32)
            mid = out[-n:] * (1 - ramp) + p[:n] * ramp
            out = np.concatenate([out[:-n], mid, p[n:]])
        else:
            out = np.concatenate([out, p])
    return out


def squeeze_pauses(y, t0, t1, wl, cap):
    """Cut [t0,t1] out of y, shortening silences between words to `cap` seconds."""
    keep, cur = [], t0
    for (_, _, e), (_, s, _) in zip(wl, wl[1:]):
        if s - e > cap:
            a = e + cap * 0.6          # keep a little tail after the word
            b = s - cap * 0.4          # and a little lead-in before the next one
            keep.append((cur, a)); cur = b
    keep.append((cur, t1))
    return xfade_join([y[int(a * SR):int(b * SR)] for a, b in keep])


def stretch(clip, speed, out_dir):
    if abs(speed - 1) < 0.005:
        return clip
    a, b = os.path.join(out_dir, "_c.wav"), os.path.join(out_dir, "_s.wav")
    sf.write(a, clip, SR)
    ff("-i", a, "-af", f"rubberband=tempo={speed:.4f}:formant=preserved:pitchq=quality", "-ar", str(SR), b)
    out, _ = sf.read(b, dtype="float32")
    os.remove(a); os.remove(b)
    return out


def main():
    vo_in, sfx_path, video, out_dir = sys.argv[1:5]
    os.makedirs(out_dir, exist_ok=True)
    y = load(vo_in)
    words = words_of(y)
    print("heard:", " ".join(w for w, _, _ in words))

    starts, wi = [], 0
    for key, *_ in LINES:
        while wi < len(words) and not words[wi][0].startswith(key):
            wi += 1
        if wi == len(words):
            sys.exit(f"could not find the line starting with '{key}' — check the voice file matches SCRIPT.md")
        starts.append(wi); wi += 1
    ends = [s - 1 for s in starts[1:]] + [len(words) - 1]

    vo = np.zeros(int(TOTAL * SR), dtype=np.float32)
    prev_end, report = 0.0, []
    for i, (key, a, b, cap) in enumerate(LINES):
        wl = words[starts[i]:ends[i] + 1]
        t0 = max(0.0, wl[0][1] - 0.06)
        t1 = wl[-1][2] + 0.14
        if i + 1 < len(LINES):
            t1 = min(t1, words[starts[i + 1]][1] - 0.03)
        clip = squeeze_pauses(y, t0, t1, wl, cap)
        raw = (t1 - t0)
        place = max(a, prev_end + GAP)
        room = b - place
        speed = min(MAX_SPEED, max(1.0, (len(clip) / SR) / room))
        clip = stretch(clip, speed, out_dir)
        n = min(len(clip) // 2, int(0.006 * SR))
        clip[:n] *= np.linspace(0, 1, n); clip[-n:] *= np.linspace(1, 0, n)
        s = int(place * SR); e = min(len(vo), s + len(clip))
        vo[s:e] += clip[:e - s]
        prev_end = place + len(clip) / SR
        report.append({"line": i + 1, "slot": f"{a:.2f}-{b:.2f}", "placed": f"{place:.2f}-{prev_end:.2f}",
                       "read_len": round(raw, 2), "speed": round(speed, 3), "late_by": round(max(0, prev_end - b), 2)})
    for r in report:
        print(r)

    vo_out = os.path.join(out_dir, "vo_aligned.wav")
    sf.write(vo_out, vo, SR, subtype="PCM_24")
    mix = os.path.join(out_dir, "mix.wav")
    # light clean-up on the voice, SFX a little under it, -14 LUFS for Instagram
    ff("-i", vo_out, "-i", sfx_path, "-filter_complex",
       "[0]highpass=f=70,acompressor=threshold=0.125:ratio=2.5:attack=8:release=120:makeup=1.6,aformat=channel_layouts=stereo[v];"
       "[1]aformat=channel_layouts=stereo,volume=0.55[s];"
       "[v][s]amix=inputs=2:normalize=0:duration=longest,loudnorm=I=-14:TP=-1:LRA=11",
       "-ar", str(SR), "-c:a", "pcm_s24le", mix)
    final = os.path.join(out_dir, "aminur_rex_promo_with_voice.mp4")
    ff("-i", video, "-i", mix, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k",
       "-shortest", "-movflags", "+faststart", final)
    print("wrote", final)


if __name__ == "__main__":
    main()
