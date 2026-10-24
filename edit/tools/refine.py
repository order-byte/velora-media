import wave, numpy as np, json
w = wave.open('/home/user/work/raw/audio16k.wav'); sr = w.getframerate()
a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
hop = int(sr * 0.01)
rms = np.sqrt(np.convolve(a**2, np.ones(hop*2)/(hop*2), mode='same'))[::hop]
db = 20*np.log10(rms + 1e-9)
TH = -38
def fr(t): return int(round(t*100))
def tt(f): return f/100
def start_at(t, mode):
    if mode == 'min':  # local minimum near t
        lo, hi = fr(t-0.15), fr(t+0.15); f = lo + int(np.argmin(db[lo:hi])); return tt(f)
    lo = fr(t-0.35); hi = fr(t+0.35)
    seg = db[lo:hi]; idx = np.where(seg > TH)[0]
    return tt(lo + idx[0]) - 0.05 if len(idx) else t
def end_at(t, mode):
    if mode == 'min':
        lo, hi = fr(t-0.15), fr(t+0.15); f = lo + int(np.argmin(db[lo:hi])); return tt(f)
    lo = fr(t-0.35); hi = fr(t+0.35)
    seg = db[lo:hi]; idx = np.where(seg > TH)[0]
    return tt(lo + idx[-1]) + 0.08 if len(idx) else t
# id, approx_in, in_mode, approx_out, out_mode, text
clips = [
 ("hook_a", 4.16,'th', 6.78,'th', "Sirf 20 creators, $200,"),
 ("hook_b", 7.80,'th', 9.32,'th', "aur poore mahine ki editing."),
 ("pain_1", 12.14,'th', 13.97,'th', "Shoot karte ho 10 minute,"),
 ("pain_2", 14.40,'th', 16.66,'th', "edit karte ho, poori raat chali jaati hai."),
 ("pain_3", 16.94,'th', 19.10,'th', "Consistently post nahi kar paate ho,"),
 ("pain_4", 20.86,'th', 23.79,'th', "aur growth slow ho jaata hai, aur burnout full ho jaata hai."),
 ("offer_1", 35.50,'min', 39.44,'th', "Isliye Aminur Rex Team laaya hai Monthly Editing Package."),
 ("offer_2", 42.33,'th', 43.83,'th', "Tum sirf shoot karo,"),
 ("offer_3", 48.61,'th', 50.50,'th', "baaki sab humara kaam."),
 ("style_q", 54.16,'th', 55.20,'th', "Aur style?"),
 ("style_trend", 62.18,'th', 63.97,'th', "Jo abhi trend kar raha hai,"),
 ("style_sab", 66.27,'th', 66.75,'th', "sab —"),
 ("st_talking", 67.38,'th', 68.36,'th', "Talking head,"),
 ("st_podcast", 69.90,'th', 71.36,'th', "Podcast clips,"),
 ("st_doc", 72.42,'th', 73.89,'th', "Documentary style,"),
 ("st_cine", 76.06,'th', 77.35,'th', "Cinematic vlog,"),
 ("st_motion", 77.82,'th', 79.25,'th', "Motion graphics,"),
 ("st_faceless", 81.57,'th', 83.12,'th', "Faceless story."),
 ("content", 85.08,'th', 87.05,'min', "Tumhara content, tumhara style —"),
 ("scroll", 101.06,'th', 104.08,'th', "hum bas usse scroll-stopping bana dete hain."),
 ("reel", 123.19,'th', 126.72,'th', "Har reel ke liye alag pay karne ka jhanjhat bhi khatam ho gaya."),
 ("price", 134.12,'th', 136.83,'th', "Poore mahine ki editing… sirf $200."),
 ("proof_a", 142.00,'th', 142.99,'th', "Abhi"),
 ("proof_b", 143.34,'th', 147.48,'th', "10 creators humare saath monthly package pe kaam kar rahe hain."),
 ("slots", 150.91,'th', 154.05,'th', "Aur bas 20 slots bache hain —"),
 ("fcfs", 158.00,'th', 160.11,'th', "first come, first serve."),
 ("cta_1", 162.80,'th', 164.06,'min', "Comment karo 'EDIT' —"),
 ("cta_2", 169.88,'min', 172.00,'th', "hum DM mein saari information bhej denge."),
 ("cta_3", 173.87,'th', 177.01,'th', "Ya seedha bio mein check karo, wahan pe contact hai."),
 ("kicker", 184.26,'th', 187.28,'th', "Aur haan… yeh video bhi humne hi edit kiya hai."),
]
out = []; total = 0
for cid, i, im, o, om, txt in clips:
    s = round(start_at(i, im), 2); e = round(end_at(o, om), 2)
    total += e - s
    out.append({"id": cid, "in": s, "out": e, "text": txt})
    print(f"{cid:12s} {s:7.2f} -> {e:7.2f}  ({e-s:4.2f}s)  {txt}")
print("total", round(total, 2))
json.dump(out, open('/home/user/work/edit/edl.json', 'w'), indent=1, ensure_ascii=False)
