"""Place an ElevenLabs voiceover onto the promo timeline and mix it with the SFX track.

Usage: python fit_vo.py <voice.mp3|wav> <sfx_track.wav> <silent_video.mp4> <out_dir>

The voice file is the whole SCRIPT.md read in one go. Whisper finds where each of the 8 lines
starts; each line is cut out, sped up slightly if it is longer than its slot, and placed at the
slot start. Writes vo_aligned.wav, mix.wav and the final video with sound.
Needs: faster-whisper, soundfile, numpy, ffmpeg.
"""
import json, os, re, subprocess, sys
import numpy as np
import soundfile as sf

SR = 48000
# first word of each line, and its slot (start, end) in seconds on the video timeline
LINES = [
    ("want", 0.05, 1.70),
    ("say", 1.72, 3.60),
    ("the", 3.62, 5.94),
    ("explore", 5.96, 12.74),
    ("punchy", 12.78, 14.42),
    ("with", 14.44, 16.30),
    ("drag", 16.34, 17.56),
    ("you", 17.64, 20.30),
]
MAX_SPEEDUP = 1.22


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
    out = []
    for s in segs:
        for w in s.words:
            out.append((re.sub(r"[^a-z]", "", w.word.lower()), w.start, w.end))
    return out


def main():
    vo_path, sfx_path, video, out_dir = sys.argv[1:5]
    os.makedirs(out_dir, exist_ok=True)
    y = load(vo_path)
    words = words_of(y)
    print("heard:", " ".join(w for w, _, _ in words))

    # find each line's first word, in order
    starts, wi = [], 0
    for key, _, _ in LINES:
        while wi < len(words) and not words[wi][0].startswith(key):
            wi += 1
        if wi == len(words):
            sys.exit(f"could not find the line starting with '{key}' — check the voice file matches SCRIPT.md")
        starts.append(wi)
        wi += 1
    ends = [starts[i + 1] - 1 for i in range(len(starts) - 1)] + [len(words) - 1]

    total = int(22.0 * SR)
    vo = np.zeros(total, dtype=np.float32)
    report = []
    for i, (key, a, b) in enumerate(LINES):
        t0 = max(0.0, words[starts[i]][1] - 0.06)
        t1 = words[ends[i]][2] + 0.12
        if i + 1 < len(LINES):
            t1 = min(t1, words[starts[i + 1]][1] - 0.02)
        clip = y[int(t0 * SR):int(t1 * SR)]
        dur, slot = len(clip) / SR, b - a
        speed = 1.0
        if dur > slot:
            speed = min(MAX_SPEEDUP, dur / slot)
            tmp_in, tmp_out = os.path.join(out_dir, "_c.wav"), os.path.join(out_dir, "_s.wav")
            sf.write(tmp_in, clip, SR)
            ff("-i", tmp_in, "-filter:a", f"atempo={speed:.4f}", "-ar", str(SR), tmp_out)
            clip, _ = sf.read(tmp_out, dtype="float32")
            os.remove(tmp_in); os.remove(tmp_out)
        # 8 ms fades so cuts never click
        n = min(len(clip) // 2, int(0.008 * SR))
        if n > 0:
            clip[:n] *= np.linspace(0, 1, n); clip[-n:] *= np.linspace(1, 0, n)
        s = int(a * SR)
        e = min(total, s + len(clip))
        vo[s:e] += clip[:e - s]
        report.append({"line": i + 1, "slot": [a, b], "voice_len": round(dur, 2), "speed": round(speed, 3)})
    print(json.dumps(report, indent=1))

    vo_path_out = os.path.join(out_dir, "vo_aligned.wav")
    sf.write(vo_path_out, vo, SR, subtype="PCM_24")
    mix = os.path.join(out_dir, "mix.wav")
    # SFX sit a little under the voice; final loudness -14 LUFS for Instagram
    ff("-i", vo_path_out, "-i", sfx_path, "-filter_complex",
       "[0]aformat=channel_layouts=stereo,volume=1.0[v];[1]aformat=channel_layouts=stereo,volume=0.6[s];"
       "[v][s]amix=inputs=2:normalize=0:duration=longest,loudnorm=I=-14:TP=-1:LRA=11",
       "-ar", str(SR), "-c:a", "pcm_s24le", mix)
    final = os.path.join(out_dir, "aminur_rex_promo_with_voice.mp4")
    ff("-i", video, "-i", mix, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k",
       "-shortest", "-movflags", "+faststart", final)
    print("wrote", final)


if __name__ == "__main__":
    main()
