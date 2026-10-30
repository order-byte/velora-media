"""Hindi voiceover for the 'Copyright Claim vs Strike' reel.

Each line is synthesised separately and joined with short pauses (longer between
sections), then loudness-normalised and written as MP3.
Usage: python make_vo.py <voice> <rate> <out.mp3>
"""
import asyncio
import os
import ssl
import subprocess
import sys
from pathlib import Path

import numpy as np
import edge_tts
import edge_tts.communicate as communicate

CA = "/root/.ccr/ca-bundle.crt"
if os.path.exists(CA):
    communicate._SSL_CTX = ssl.create_default_context(cafile=CA)

SR = 48000
LINE_GAP, SECTION_GAP = 0.25, 0.45

SECTIONS = [
    ["एक गलती, और आपका चैनल जा सकता है।"],
    ["वो गलती है, कॉपीराइट क्लेम और स्ट्राइक को एक समझना।"],
    ["क्लेम मतलब, आपके वीडियो में किसी और का गाना या क्लिप है। चैनल सेफ है। बस उस वीडियो की कमाई ओनर को जा सकती है, या वीडियो ब्लॉक हो सकता है।"],
    ["स्ट्राइक मतलब, ओनर ने यूट्यूब से वीडियो हटवा दिया, और चैनल पे स्ट्राइक लग गया।",
     "क्रिकेट जैसा समझो। क्लेम में रन कटे, स्ट्राइक में विकेट गिरा। नब्बे दिन में तीन विकेट, तो चैनल बंद हो सकता है।"],
    ["अब दो गलतियाँ मत करना। वीडियो डिलीट करने से स्ट्राइक नहीं हटता। और बिना राइट्स के डिस्प्यूट किया, तो क्लेम स्ट्राइक बन सकता है।"],
    ["समझ नहीं आ रहा क्या करें? 'कॉपीराइट' लिख के डीएम करो। हम सच-सच बताएंगे।"],
]


async def synth(text, voice, rate, path):
    com = edge_tts.Communicate(text, voice, rate=rate, proxy=os.environ.get("HTTPS_PROXY"))
    await com.save(str(path))


def decode(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         check=True, capture_output=True).stdout
    a = np.frombuffer(raw, dtype=np.float32)
    # trim the synthesiser's leading/trailing silence so our own pauses set the rhythm
    idx = np.where(np.abs(a) > 0.01)[0]
    return a[max(0, idx[0] - 480): idx[-1] + 2400] if idx.size else a


def main():
    voice, rate, out = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    work = Path(__file__).resolve().parent / f"clips60_{voice}_{rate}"
    work.mkdir(exist_ok=True)
    parts = [np.zeros(int(0.25 * SR), dtype=np.float32)]
    for si, sec in enumerate(SECTIONS):
        for li, text in enumerate(sec):
            mp3 = work / f"{si}_{li}.mp3"
            if not mp3.exists() or mp3.stat().st_size == 0:
                asyncio.run(synth(text, voice, rate, mp3))
            parts.append(decode(mp3))
            last = li == len(sec) - 1
            parts.append(np.zeros(int((SECTION_GAP if last else LINE_GAP) * SR), dtype=np.float32))
    mix = np.concatenate(parts)
    raw = work / "mix.f32"
    raw.write_bytes(mix.tobytes())
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", str(raw),
                    "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "44100", "-ac", "2",
                    "-c:a", "libmp3lame", "-b:a", "192k", str(out)], check=True)
    raw.unlink()
    print(f"{out} {len(mix) / SR:.1f}s")


if __name__ == "__main__":
    main()
