import json, wave, numpy as np, subprocess, sys
SPEED = 1.1; FPS = 30
W = wave.open('/home/user/work/raw/audio16k.wav'); SR = W.getframerate()
A = np.frombuffer(W.readframes(W.getnframes()), dtype=np.int16).astype(np.float32)/32768
hop = SR//100
db = 20*np.log10(np.sqrt(np.convolve(A**2, np.ones(hop*2)/(hop*2), 'same'))[::hop] + 1e-9)
KEEP_PAUSE = {"kicker", "fcfs", "hook_a"}  # pauses that carry the delivery
edl = json.load(open('/home/user/work/edit/edl.json'))
subs = []
for c in edl:
    i0, i1 = int(c['in']*100), int(c['out']*100)
    quiet = db[i0:i1] < -40
    cuts = []; k = 0
    while k < len(quiet):
        if quiet[k]:
            j = k
            while j < len(quiet) and quiet[j]: j += 1
            if (j-k) >= 30 and k > 5 and j < len(quiet)-5 and c['id'] not in KEEP_PAUSE:
                cuts.append(((i0+k)/100 + 0.06, (i0+j)/100 - 0.06))
            k = j
        else: k += 1
    s = c['in']
    for a, b in cuts:
        subs.append({"clip": c['id'], "in": round(s,3), "out": round(a,3)}); s = b
    subs.append({"clip": c['id'], "in": round(s,3), "out": c['out']})
t = 0
for k, sb in enumerate(subs):
    d = (sb['out']-sb['in'])/SPEED
    sb['oStart'] = round(t,4); sb['oEnd'] = round(t+d,4); t += d
total = t
def src2out(clip, ts):
    cand = [s for s in subs if s['clip'] == clip]
    for s in cand:
        if ts <= s['out']:
            return s['oStart'] + max(0, ts - s['in'])/SPEED
    return cand[-1]['oEnd']
timeline = {"fps": FPS, "duration": round(total,3), "subclips": subs, "clips": []}
for c in edl:
    words = [{"w": w['w'], "s": round(src2out(c['id'], c['in']+w['s']),3), "e": round(src2out(c['id'], c['in']+w['e']),3)} for w in c['words'] if w['w'] not in ('—',)]
    cs = [s for s in subs if s['clip']==c['id']]
    timeline["clips"].append({"id": c['id'], "text": c['text'], "oStart": cs[0]['oStart'], "oEnd": cs[-1]['oEnd'], "words": words})
json.dump(timeline, open('/home/user/work/edit/timeline.json','w'), indent=1, ensure_ascii=False)
print(f"{len(edl)} clips -> {len(subs)} subclips, output {total:.2f}s")
for c in timeline['clips']: print(f"  {c['id']:12s} {c['oStart']:6.2f}-{c['oEnd']:6.2f}  {c['text']}")
if '--dry' in sys.argv: sys.exit()
# per-subclip cuts (low memory), then one pass for speed/grade/voice
import os
os.makedirs('/home/user/work/edit/parts', exist_ok=True)
lst=open('/home/user/work/edit/parts/list.txt','w')
for k, sb in enumerate(subs):
    d = sb['out']-sb['in']; out=f'/home/user/work/edit/parts/p{k:02d}.mkv'
    subprocess.run(["ffmpeg","-v","error","-y","-ss",f"{sb['in']:.3f}","-i","/home/user/work/raw/raw.mp4","-t",f"{d:.3f}",
        "-af",f"afade=t=in:d=0.008,afade=t=out:st={max(0,d-0.012):.3f}:d=0.012","-c:v","libx264","-preset","veryfast","-crf","12",
        "-pix_fmt","yuv420p","-c:a","pcm_s16le","-ar","48000",out], check=True)
    lst.write(f"file '{out}'\n")
lst.close()
grade = ("eq=contrast=1.10:saturation=0.90:gamma=0.96:brightness=-0.015,"
         "colorbalance=rs=-0.02:gs=0.0:bs=0.03:rh=0.03:gh=0.01:bh=-0.03,"
         "curves=all='0/0.03 0.25/0.21 0.5/0.50 0.75/0.79 1/0.97',vignette=PI/5")
voice = (f"atempo={SPEED},highpass=f=85,lowpass=f=15000,afftdn=nf=-28,"
         "equalizer=f=220:t=q:w=1.2:g=-2,equalizer=f=3200:t=q:w=1.0:g=2.5,equalizer=f=9000:t=h:w=0.7:g=1.5,"
         "acompressor=threshold=-20dB:ratio=3.5:attack=4:release=90:makeup=3,loudnorm=I=-15:TP=-1.5:LRA=6,aresample=48000")
g = f"[0:v]setpts=PTS/{SPEED},fps={FPS},format=yuv420p,split[vr][vg0];[vg0]{grade}[vg];[0:a]{voice},asplit[ar][ag]"
cmd = ["ffmpeg","-v","error","-y","-f","concat","-safe","0","-i","/home/user/work/edit/parts/list.txt","-filter_complex",g,
       "-map","[vg]","-map","[ag]","-c:v","libx264","-preset","medium","-crf","16","-c:a","aac","-b:a","256k","/home/user/work/edit/base.mp4",
       "-map","[vr]","-map","[ar]","-c:v","libx264","-preset","medium","-crf","18","-c:a","aac","-b:a","192k","/home/user/work/edit/base_raw.mp4"]
subprocess.run(cmd, check=True)
print("done")
