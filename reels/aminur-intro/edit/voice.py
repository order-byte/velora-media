# Voice clean-up for the raw take: late-reverb suppression, per-phrase levelling, EQ, then cut + speed-up.
import os, sys, subprocess, numpy as np, soundfile as sf
from scipy.signal import stft, istft
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cuts import plan, SPEED
S=os.environ.get("REEL_WORK", os.path.dirname(os.path.abspath(__file__))+"/work")
A=S+"/build/audio"
x,sr=sf.read(S+"/raw/raw48.wav"); assert sr==48000
rms=lambda v: np.sqrt(np.mean(np.square(v))+1e-12)

def dereverb(x, t60=0.45, td=0.05, beta=1.4, gmin=0.18):
    """Spectral subtraction of late reverberation (Lebart-style): the room tail at time t is
    modelled as a decayed copy of the smoothed spectrum td seconds earlier."""
    n,h=1024,256
    f,t,X=stft(x,sr,nperseg=n,noverlap=n-h); P=np.abs(X)**2
    Ps=np.empty_like(P); a=0.6; Ps[:,0]=P[:,0]
    for i in range(1,P.shape[1]): Ps[:,i]=a*Ps[:,i-1]+(1-a)*P[:,i]
    d=3*np.log(10)/t60; hop_s=h/sr; D=int(round(td/hop_s))
    R=np.zeros_like(P)
    # sum of decayed past frames from td back to ~t60
    K=int(round(t60/hop_s))
    for k in range(D,K,2):
        R[:,k:]+=np.exp(-2*d*k*hop_s)*Ps[:,:-k]*2
    R*= (1-np.exp(-2*d*hop_s))            # normalise the kernel to a per-frame decay
    G=np.clip(1-beta*R/(P+1e-12),gmin**2,1)**0.5
    # light smoothing in time and frequency against musical noise
    G[:,1:]=0.5*G[:,1:]+0.5*G[:,:-1]; G[1:-1]=(G[:-2]+2*G[1:-1]+G[2:])/4
    _,y=istft(X*G,sr,nperseg=n,noverlap=n-h); return y[:len(x)]

y=dereverb(x)
sf.write(A+"/v_dry.wav",y,sr)
# tone: remove boxiness, add presence and air; gentle broadband denoise
subprocess.run(["ffmpeg","-v","error","-y","-i",A+"/v_dry.wav","-af",
  "highpass=f=90,afftdn=nr=8:nf=-55,equalizer=f=320:t=q:w=1.0:g=-4,equalizer=f=650:t=q:w=1.4:g=-1.5,"
  "equalizer=f=3600:t=q:w=1.0:g=3.5,highshelf=f=8500:g=3",A+"/v_eq.wav"],check=True)
z,_=sf.read(A+"/v_eq.wav")
# per-phrase levelling: one static gain per spoken phrase (no pumping, tails are not lifted)
segs,T=plan(); target=10**(-20/20)
out=[]; fd=int(0.008*sr)
for s in segs:
    seg=z[int(s["src0"]*sr):int(s["src1"]*sr)].copy()
    # split long phrases at internal pauses so front-facing and side-facing parts level separately
    win=int(0.4*sr); g=np.ones(len(seg))
    env=np.array([rms(seg[i:i+win]) for i in range(0,len(seg),win//2)])
    act=seg[np.abs(seg)>0.25*np.abs(seg).max()]
    gain=target/rms(act) if len(act) else 1.0
    seg*=min(gain,10**(14/20))
    seg[:fd]*=np.linspace(0,1,fd); seg[-fd:]*=np.linspace(1,0,fd); out.append(seg)
v=np.concatenate(out); sf.write(A+"/voice_edit.wav",v,sr)
# downward expander pulls remaining tails down between words, then light compression and loudness
subprocess.run(["ffmpeg","-v","error","-y","-i",A+"/voice_edit.wav","-af",
  f"agate=threshold=0.035:ratio=2.2:range=0.22:attack=4:release=140:knee=6,acompressor=threshold=-22dB:ratio=2.5:attack=10:release=140:makeup=3,"
  f"deesser=i=0.3:m=0.5:f=0.5,rubberband=tempo={SPEED}:formant=preserved:pitchq=quality,loudnorm=I=-15:TP=-1.5:LRA=7","-ar","48000",A+"/voice_final.wav"],check=True)
print("voice done")
