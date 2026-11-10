import os, soundfile as sf, numpy as np, subprocess
from scipy.signal import resample_poly
S=os.environ.get("REEL_WORK", os.path.dirname(os.path.abspath(__file__))+"/work")  # holds ref/, music/, build/audio
MUSIC_START=float(os.environ.get("MUSIC_START","0"))   # second of the music track where the reel starts
MUSIC_DB=float(os.environ.get("MUSIC_DB","-12"))       # music level relative to the voice
SR=48000; TOTAL=34.65
fx,sr=sf.read(S+"/ref/audio/sep/htdemucs/ref44/no_vocals.wav"); fx=resample_poly(fx,160,147,axis=0)
voice,_=sf.read(S+"/build/audio/voice_final.wav")
mus,_=sf.read(S+"/music/m.wav")
rms=lambda x: np.sqrt(np.mean(np.square(x))+1e-12)
# sound-effect library: every sound is a slice of the reference reel's effects stem (voice removed)
LIB=dict(
 shimmer=(0.47,1.03), whooshA=(3.03,3.90), whooshB=(5.80,6.42), zoom=(7.37,7.94), slide=(10.30,10.88),
 card=(13.04,13.60), click=(14.85,16.15), impact=(16.95,17.95), pop=(18.27,18.66), press=(19.42,20.17),
 swell=(20.56,21.44), whooshC=(23.57,24.18),
 tick1=(1.27,1.38), tick2=(1.91,2.02), tick3=(14.03,14.16), tick4=(14.34,14.71), tick5=(18.05,18.23), tick6=(20.26,20.39), tick7=(21.68,21.83))
# (sound, time on the new timeline, gain dB)
EV=[
 ("tick1",0.26,2),("shimmer",0.39,-1),
 ("whooshB",1.38,-6),("pop",2.05,-5),("tick3",2.00,2),("tick5",2.34,0),
 ("whooshA",3.02,-1),("tick6",4.55,2),("tick2",4.95,2),("zoom",5.32,-4),
 ("whooshB",6.38,-1),("card",7.44,-4),("zoom",8.86,-1),
 ("whooshC",10.27,-2),("tick4",11.04,3),("slide",11.75,-1),
 ("tick7",12.96,2),("impact",13.36,-2),
 ("card",14.62,-1),("tick3",15.16,2),("tick6",15.70,2),("click",15.95,-1),("tick1",17.30,1),("tick2",17.98,1),
 ("whooshB",18.45,-3),("pop",18.55,-3),("impact",19.52,-1),("slide",20.02,-6),("pop",20.84,-1),("tick5",20.96,1),
 ("tick4",21.83,3),("press",22.08,-1),("swell",23.00,-2),
 ("whooshB",24.84,-3),("tick7",25.84,2),("tick1",26.38,2),("zoom",26.72,-6),
 ("whooshC",27.43,-1),("tick3",27.50,0),("tick6",27.61,0),("tick5",27.72,0),("tick3",27.83,0),("tick6",27.94,0),("tick5",28.05,0),("card",28.50,-4),
 ("shimmer",30.95,-6),
 ("whooshA",31.37,-3),("tick2",32.18,1),("tick1",32.54,1),("slide",33.08,-4),("zoom",33.30,-2),("pop",33.72,-2),("shimmer",33.92,-4),
]
N=int(TOTAL*SR); sfx=np.zeros((N,2))
for name,t,g in EV:
    a,b=LIB[name]; x=fx[int(a*SR):int(b*SR)].copy()
    fi=int(0.010*SR); fo=int(min(0.09,(b-a)/3)*SR)
    x[:fi]*=np.linspace(0,1,fi)[:,None]; x[-fo:]*=np.linspace(1,0,fo)[:,None]
    x*=10**((g-3.0)/20); i=int(t*SR); n=min(len(x),N-i)
    if n>0: sfx[i:i+n]+=x[:n]
v=np.zeros(N); n=min(len(voice),N); v[:n]=voice[:n] if voice.ndim==1 else voice[:n].mean(1)
# music bed: fixed level under the voice, dips a little further while speech is present
m=mus[int(MUSIC_START*SR):int(MUSIC_START*SR)+N].copy()
if len(m)<N: m=np.vstack([m,np.zeros((N-len(m),2))])
m*=rms(v[np.abs(v)>0.02])/rms(m)*10**(MUSIC_DB/20)
env=np.sqrt(np.convolve(v*v,np.ones(int(0.25*SR))/int(0.25*SR),mode="same")); duck=1-0.30*np.clip(env/0.08,0,1)
m*=duck[:,None]
fi=int(0.6*SR); fo=int(1.8*SR); m[:fi]*=np.linspace(0,1,fi)[:,None]**2; m[-fo:]*=np.linspace(1,0,fo)[:,None]**2
mix=sfx+m+v[:,None]
sf.write(S+"/build/audio/mix_raw.wav",mix,SR); sf.write(S+"/build/audio/sfx_only.wav",sfx,SR)
subprocess.run(["ffmpeg","-v","error","-y","-i",S+"/build/audio/mix_raw.wav","-af","alimiter=limit=0.94:attack=3:release=60,loudnorm=I=-14:TP=-1.2:LRA=9","-ar","48000",S+"/build/audio/mix_final.wav"],check=True)
db=lambda x:round(float(20*np.log10(rms(x))),1)
print("voice",db(v[np.abs(v)>0.02]),"music",db(m),"sfx peak",round(float(20*np.log10(np.abs(sfx).max())),1),"events",len(EV))
