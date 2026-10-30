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
LINE_GAP, SECTION_GAP = 0.28, 0.55

SECTIONS = [
    ["वीडियो पे 'कॉपीराइट' आया, और दिल बैठ गया?",
     "रुको। पहले ये देखो, क्लेम है या स्ट्राइक? क्योंकि दोनों में बहुत बड़ा फ़र्क है।"],
    ["ज़्यादातर क्रिएटर्स दोनों को एक ही समझते हैं, और घबरा के गलत स्टेप ले लेते हैं।"],
    ["पहले क्लेम। मतलब, आपके वीडियो में किसी और का गाना या क्लिप मिला, और उसका ओनर कह रहा है, 'ये हिस्सा मेरा है।'",
     "आपका चैनल सेफ है। असर सिर्फ़ उस वीडियो पे पड़ता है। अक्सर उसकी कमाई ओनर को जाने लगती है, या वीडियो ब्लॉक हो सकता है।"],
    ["अब स्ट्राइक। ये तब लगता है, जब ओनर सीधा यूट्यूब से कहता है, 'ये वीडियो हटाओ।' वीडियो हट जाता है, और चैनल पे स्ट्राइक लग जाता है।",
     "क्रिकेट की तरह समझो। क्लेम में सिर्फ़ रन कटे, आप अभी भी क्रीज़ पे हो। स्ट्राइक मतलब, विकेट गिरा।",
     "और नब्बे दिन में तीन विकेट, तो चैनल बंद हो सकता है।",
     "एक स्ट्राइक नब्बे दिन में खत्म होता है, लेकिन तभी, जब आप यूट्यूब का 'कॉपीराइट स्कूल' पूरा करो।"],
    ["अब दो बड़ी गलतियाँ।",
     "पहली, स्ट्राइक आते ही वीडियो डिलीट करना। इससे स्ट्राइक नहीं हटता।",
     "हाँ, कभी-कभी यूट्यूब ईमेल में सात दिन देता है, वीडियो खुद हटाने के लिए। तो ईमेल ध्यान से पढ़ो।",
     "दूसरी, हर क्लेम पे डिस्प्यूट डालना। अगर गाना या क्लिप सच में आपका नहीं है, तो ओनर वीडियो हटवा सकता है, और क्लेम सीधा स्ट्राइक बन जाता है।"],
    ["तो अगली बार घबराओ मत। पहले चेक करो, क्लेम है या स्ट्राइक।",
     "और अगर समझ नहीं आ रहा कि आगे क्या करें, तो हमें 'कॉपीराइट' लिख के डीएम करो। हम पहले आपकी सिचुएशन समझेंगे, फिर सच बताएंगे कि क्या हो सकता है।"],
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
    work = Path(__file__).resolve().parent / f"clips_{voice}_{rate}"
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
