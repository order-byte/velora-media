"""Builds the Bangla voiceover, a soft music bed and the timing file the animation reads.

Outputs (next to this file):
  tts_cache/       one mp3 + word timings per voiceover line
  timing.json      scene / line / caption timings
  timing.js        same data as window.TIMING for video.html
  captions_bn.srt  Bangla subtitles
  audio.wav        final mixed, loudness-normalised soundtrack
"""
import asyncio
import hashlib
import json
import os
import ssl
import subprocess
from pathlib import Path

import numpy as np
import edge_tts
import edge_tts.communicate as communicate

# Behind a TLS-intercepting proxy, trust its CA instead of certifi's.
PROXY_CA = os.environ.get("TTS_CA_BUNDLE", "/root/.ccr/ca-bundle.crt")
if os.path.exists(PROXY_CA):
    communicate._SSL_CTX = ssl.create_default_context(cafile=PROXY_CA)

HERE = Path(__file__).resolve().parent
CACHE = HERE / "tts_cache"
SR = 48000
FPS = 30

LEAD_FIRST = 1.4   # silence before the very first line
LEAD = 0.9         # scene starts, visuals settle, then the voice comes in
GAP = 0.45         # pause between lines inside a scene
TAIL = 0.9         # hold after the last line of a scene
TAIL_LAST = 4.0    # end card


async def synth(text, voice, rate, mp3_path, words_path):
    com = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary",
                               proxy=os.environ.get("HTTPS_PROXY"))
    words = []
    with open(mp3_path, "wb") as f:
        async for chunk in com.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                s = chunk["offset"] / 1e7
                words.append({"w": chunk["text"], "s": s, "e": s + chunk["duration"] / 1e7})
    words_path.write_text(json.dumps(words, ensure_ascii=False))


def decode(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "1",
                          "-ar", str(SR), "-"], check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def chunk_captions(text, words, line_start, line_end):
    """Splits a line into evenly sized caption chunks at word gaps, preferring punctuation."""
    spans, pos = [], 0
    for w in words:
        i = text.find(w["w"], pos)
        if i < 0:
            i = pos
        spans.append((i, i + len(w["w"])))
        pos = i + len(w["w"])
    n = len(words)
    starts = [0] + [spans[k][0] for k in range(1, n)]
    seg = lambda a, b: text[starts[a]:(starts[b] if b < n else len(text))].strip()
    pieces = max(1, -(-len(text) // 50))
    nobreak = {("স্ট্রাইক", "ডেস্ক"), ("লিড", "কার্ড"), ("কোয়ালিটি", "চেক"), ("সোশ্যাল", "মিডিয়া"), ("সাহেব", "ভাই"),
               ("ইউটিউব", "স্টুডিওর"), ("কাউন্টার", "নোটিফিকেশনের"), ("রেভিনিউ", "প্রুফ"), ("এক", "লাখ"), ("কনটেন্ট", "লাইন")}
    target = len(text) / pieces
    # dp[k][j]: best cost for words[:j] split into k chunks
    INF = float("inf")
    dp = [[INF] * (n + 1) for _ in range(pieces + 1)]
    back = [[0] * (n + 1) for _ in range(pieces + 1)]
    dp[0][0] = 0
    for k in range(1, pieces + 1):
        for j in range(1, n + 1):
            for i in range(k - 1, j):
                if dp[k - 1][i] == INF:
                    continue
                t = seg(i, j)
                cost = (len(t) - target) ** 2 + (0 if t[-1] in "।,?!" or j == n else 400)
                if j < n and (words[j - 1]["w"], words[j]["w"]) in nobreak:
                    cost += 3000
                if len(t) > 60:
                    cost += 5000
                if dp[k - 1][i] + cost < dp[k][j]:
                    dp[k][j], back[k][j] = dp[k - 1][i] + cost, i
    cuts, j = [], n
    for k in range(pieces, 0, -1):
        i = back[k][j]
        cuts.append((i, j))
        j = i
    chunks = [{"text": seg(i, j), "s": line_start + words[i]["s"]} for i, j in reversed(cuts)]
    for i, ch in enumerate(chunks):
        ch["e"] = chunks[i + 1]["s"] if i + 1 < len(chunks) else line_end + 0.25
    return chunks


def music_bed(n, scene_starts, voice_mask):
    t = np.arange(n) / SR
    out = np.zeros((n, 2), dtype=np.float64)
    midi = lambda m: 440.0 * 2 ** ((m - 69) / 12)
    # Fmaj7 - Am7 - Cadd9 - G6, eight seconds each, looped
    chords = [([53, 57, 60, 64], 41), ([57, 60, 64, 67], 45), ([55, 60, 62, 64], 48), ([55, 59, 62, 64], 43)]
    length, attack, release = 8.0, 2.5, 3.0
    k = 0
    while k * length < n / SR:
        notes, bass = chords[k % len(chords)]
        t0 = k * length
        a, b = int(t0 * SR), min(n, int((t0 + length + release) * SR))
        tt = t[a:b] - t0
        env = np.clip(tt / attack, 0, 1) * np.clip((length + release - tt) / release, 0, 1)
        env = env ** 1.5
        for j, m in enumerate(notes + [bass]):
            f = midi(m)
            amp = 0.07 if m != bass else 0.09
            for ch, det in ((0, 0.998), (1, 1.002)):
                ph = 2 * np.pi * f * det * tt + j
                tone = np.sin(ph) + 0.28 * np.sin(2 * ph) + 0.1 * np.sin(3 * ph)
                out[a:b, ch] += amp * env * tone
        k += 1
    # soft bell notes on chord tones, two octaves up
    rng = np.random.default_rng(7)
    step = 2.0
    for i in range(int(n / SR / step)):
        if rng.random() < 0.35:
            continue
        t0 = i * step + rng.choice([0, 0.5, 1.0])
        notes, _ = chords[int(t0 // length) % len(chords)]
        f = midi(rng.choice(notes) + 24)
        a, b = int(t0 * SR), min(n, int((t0 + 2.5) * SR))
        tt = t[a:b] - t0
        bell = 0.035 * np.exp(-tt * 2.2) * np.sin(2 * np.pi * f * tt) * np.clip(tt / 0.01, 0, 1)
        pan = rng.uniform(0.3, 0.7)
        out[a:b, 0] += bell * (1 - pan)
        out[a:b, 1] += bell * pan
    out /= np.abs(out).max() + 1e-9
    out *= 0.16
    # duck under the voice
    win = int(0.35 * SR)
    m = np.convolve(voice_mask, np.ones(win) / win, mode="same")
    out *= (1 - 0.5 * np.clip(m, 0, 1))[:, None]
    # whooshes on scene changes
    noise = np.random.default_rng(3).standard_normal(int(0.9 * SR))
    spec = np.fft.rfft(noise)
    freqs = np.fft.rfftfreq(noise.size, 1 / SR)
    spec *= np.exp(-((np.log(freqs + 1) - np.log(1800)) ** 2) / 0.9)
    whoosh = np.fft.irfft(spec, noise.size)
    tw = np.arange(whoosh.size) / SR
    whoosh *= np.where(tw < 0.4, (tw / 0.4) ** 2, np.exp(-(tw - 0.4) * 6))
    whoosh /= np.abs(whoosh).max()
    whoosh *= 0.09
    for s in scene_starts[1:]:
        a = int(max(0, s - 0.35) * SR)
        b = min(n, a + whoosh.size)
        out[a:b, 0] += whoosh[: b - a] * 0.9
        out[a:b, 1] += whoosh[: b - a]
    # fade in / out
    fi, fo = int(2.0 * SR), int(5.0 * SR)
    out[:fi] *= np.linspace(0, 1, fi)[:, None]
    out[-fo:] *= np.linspace(1, 0, fo)[:, None]
    return out


def srt_time(x):
    ms = int(round(x * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def main():
    script = json.loads((HERE / "script.json").read_text())
    voice, rate = script["voice"], script["rate"]
    CACHE.mkdir(exist_ok=True)

    clips = []
    for si, scene in enumerate(script["scenes"]):
        for li, text in enumerate(scene["lines"]):
            key = hashlib.sha1(f"{voice}|{rate}|{text}".encode()).hexdigest()[:12]
            mp3, wj = CACHE / f"{key}.mp3", CACHE / f"{key}.json"
            if not (mp3.exists() and wj.exists() and mp3.stat().st_size > 0):
                print("tts", scene["id"], li)
                asyncio.run(synth(text, voice, rate, mp3, wj))
            clips.append((si, li, text, decode(mp3), json.loads(wj.read_text())))

    scenes, t, ci = [], 0.0, 0
    for si, scene in enumerate(script["scenes"]):
        sc = {"id": scene["id"], "chapter": scene["chapter"], "start": round(t, 3), "lines": []}
        lt = t + (LEAD_FIRST if si == 0 else LEAD)
        for li in range(len(scene["lines"])):
            _, _, text, audio, words = clips[ci]
            ci += 1
            dur = audio.size / SR
            line = {"id": f"{scene['id']}.{li}", "start": round(lt, 3), "end": round(lt + dur, 3), "text": text,
                    "words": [{"w": w["w"], "s": round(lt + w["s"], 3), "e": round(lt + w["e"], 3)} for w in words]}
            line["captions"] = chunk_captions(text, words, lt, lt + dur)
            for c in line["captions"]:
                c["s"], c["e"] = round(c["s"], 3), round(c["e"], 3)
            sc["lines"].append(line)
            lt += dur + GAP
        last_end = sc["lines"][-1]["end"]
        t = last_end + (TAIL_LAST if si == len(script["scenes"]) - 1 else TAIL)
        sc["end"] = round(t, 3)
        scenes.append(sc)

    duration = round(t, 3)
    timing = {"fps": FPS, "duration": duration, "scenes": scenes}
    (HERE / "timing.json").write_text(json.dumps(timing, ensure_ascii=False, indent=1))
    (HERE / "timing.js").write_text("window.TIMING = " + json.dumps(timing, ensure_ascii=False) + ";\n")

    n = int(np.ceil(duration * SR))
    voice_track = np.zeros(n)
    mask = np.zeros(n)
    ci = 0
    for sc in scenes:
        for line in sc["lines"]:
            audio = clips[ci][3]
            ci += 1
            a = int(line["start"] * SR)
            b = min(n, a + audio.size)
            voice_track[a:b] += audio[: b - a]
            mask[a:b] = 1
    voice_track *= 0.89 / (np.abs(voice_track).max() + 1e-9)
    mix = music_bed(n, [s["start"] for s in scenes], mask) + voice_track[:, None]
    mix = np.clip(mix, -1, 1).astype(np.float32)
    raw = HERE / "mix_raw.f32"
    raw.write_bytes(mix.tobytes())
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", str(raw),
                    "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", str(SR), str(HERE / "audio.wav")], check=True)
    raw.unlink()

    srt, k = [], 1
    for sc in scenes:
        for line in sc["lines"]:
            for c in line["captions"]:
                srt.append(f"{k}\n{srt_time(c['s'])} --> {srt_time(c['e'])}\n{c['text']}\n")
                k += 1
    (HERE / "captions_bn.srt").write_text("\n".join(srt))
    print(f"duration {duration:.1f}s, {sum(len(s['lines']) for s in scenes)} lines")


if __name__ == "__main__":
    main()
