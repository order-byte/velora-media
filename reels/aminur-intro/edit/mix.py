import soundfile as sf, numpy as np, subprocess
import os
S=os.environ.get("REEL_WORK", os.path.dirname(os.path.abspath(__file__))+"/work")  # holds ref/, build/ (raw frames, audio)
fx,sr=sf.read(S+"/ref/audio/sep/htdemucs/ref44/no_vocals.wav")
voice,vsr=sf.read(S+"/build/audio/voice_final.wav")
assert vsr==48000
# resample fx to 48k
from scipy.signal import resample_poly
fx=resample_poly(fx,160,147,axis=0); sr=48000
TOTAL=34.65
out=np.zeros((int(TOTAL*sr),2),dtype=np.float64)
# (ref_start, ref_end, my_time, gain_db)
EV=[
 (0.38,0.98, 0.40, 0),     # name pop
 (1.10,1.62, 1.50, 4),     # pixel transition to campus
 (2.92,3.85, 3.02, 0),     # cut to desk
 (5.45,6.45, 6.36, 0),     # cut to editor
 (7.15,7.98, 8.82, 0),     # zoom out + number
 (8.35,8.95, 10.27, 3),    # cards scene
 (10.15,10.95, 11.76, 0),  # second card
 (11.20,11.75, 13.05, 3),  # dark scene
 (12.55,13.65, 14.57, 0),  # profile card in
 (13.95,15.10, 15.30, 0),  # words / cursor
 (15.15,16.05, 16.42, 0),  # click + swap
 (16.35,16.92, 18.45, 2),  # cut to dark goal
 (16.95,17.75, 19.80, 0),  # KEEP GETTING BETTER slam
 (17.95,18.62, 20.85, 0),  # curve icons
 (19.15,19.47, 21.79, 0),  # pill in
 (19.45,19.98, 22.27, 0),  # press
 (20.45,21.25, 23.08, 0),  # enjoy what i do
 (21.50,22.05, 24.85, 2),  # dark
 (23.15,24.20, 27.41, 0),  # work grid
 (27.00,27.60, 31.38, 4),  # final scene
 (28.15,28.95, 33.25, 4),  # DM me
]
for a,b,t,g in EV:
    x=fx[int(a*sr):int(b*sr)].copy()
    fi=int(0.012*sr); fo=int(0.08*sr)
    x[:fi]*=np.linspace(0,1,fi)[:,None]; x[-fo:]*=np.linspace(1,0,fo)[:,None]
    x*=10**((g-2.5)/20)
    i=int(t*sr); n=min(len(x),len(out)-i); out[i:i+n]+=x[:n]
v=np.zeros(len(out)); n=min(len(voice),len(out)); v[:n]=voice[:n] if voice.ndim==1 else voice[:n].mean(1)
mix=out+v[:,None]
sf.write(S+"/build/audio/sfx_only.wav",out,sr)
sf.write(S+"/build/audio/mix_raw.wav",mix,sr)
subprocess.run(["ffmpeg","-v","error","-y","-i",S+"/build/audio/mix_raw.wav","-af","alimiter=limit=0.94:attack=3:release=60,loudnorm=I=-14:TP=-1.2:LRA=9","-ar","48000",S+"/build/audio/mix_final.wav"],check=True)
print("mixed", len(mix)/sr)
