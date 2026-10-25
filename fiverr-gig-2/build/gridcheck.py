import sys, json, numpy as np
from scipy.io import wavfile
from scipy import signal
SR=48000; BEAT=14/30
for p in sys.argv[1:]:
    sr, x = wavfile.read(p); m = x.mean(1)
    sos = signal.butter(2, 150/(SR/2), 'lowpass', output='sos'); lo = signal.sosfilt(sos, m)
    hop=240; env = np.sqrt(np.convolve(lo**2, np.ones(hop)/hop, 'same')[::hop]); fl = np.maximum(0, np.diff(env, prepend=0))
    fps = SR/hop
    res=[]
    for seg,(a,b) in {"intro":(0,4),"dropA":(4,12),"break":(12,16),"dropB":(16,24),"outro":(24,28)}.items():
        t0=a*4*BEAT; t1=b*4*BEAT
        offs=np.arange(-0.06,0.0601,0.002); sc=[]
        for o in offs:
            beats=np.arange(t0,t1,BEAT)+o
            idx=np.round(beats*fps).astype(int); idx=idx[(idx>=0)&(idx<len(fl))]
            sc.append(fl[idx].sum())
        sc=np.array(sc); best=offs[np.argmax(sc)]; strength=sc.max()/(np.median(sc)+1e-9)
        res.append(f"{seg}:{best*1000:+4.0f}ms(x{strength:.1f})")
    print(p.split('/')[-1], ' '.join(res))
