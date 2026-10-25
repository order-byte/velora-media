import wave, numpy as np, json
from faster_whisper import WhisperModel
m = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8", cpu_threads=4)
w = wave.open("/home/user/work/final/cut16k.wav"); a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32)/32768
prompt = ("Sirf 20 creators, $200, aur poore mahine ki editing. Shoot karte ho 10 minute, edit karte ho poori raat chali jaati hai. "
 "Consistently post nahi kar paate ho, aur growth slow ho jaata hai, aur burnout full ho jaata hai. Isliye Aminur Rex Team laaya hai Monthly Editing Package. "
 "Tum sirf shoot karo, baaki sab humara kaam. Aur style? Jo abhi trend kar raha hai, sab. Talking head, Podcast clips, Documentary, Cinematic vlog, Motion graphics, Faceless story. "
 "Tumhara content, tumhara style, hum bas usse scroll stop bana dete hain. Har reel ke liye alag pay karne ka jhanjhat bhi khatam ho gaya. Poore mahine ki editing, sirf $200. "
 "Abhi 10 creators humare saath monthly package pe kaam kar rahe hain. Aur bas 20 slots bache hain, first come first serve. Comment karo EDIT, hum DM mein saari information bhej denge. "
 "Ya seedha bio mein check karo, wahan pe contact number hai. Aur haan, yeh video bhi humne hi edit kiya hai.")
segs, _ = m.transcribe(a, language="en", beam_size=5, word_timestamps=True, initial_prompt=prompt, vad_filter=True)
words = [{"w": x.word.strip(), "s": round(x.start, 3), "e": round(x.end, 3)} for s in segs for x in s.words]
json.dump(words, open("/home/user/work/final/words.json", "w"), indent=1)
print(" ".join(f"{x['w']}@{x['s']:.1f}" for x in words))
