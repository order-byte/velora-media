import sys, json, subprocess, numpy as np, cv2, re
import onnxruntime as ort
_so = ort.SessionOptions(); _so.intra_op_num_threads = 4
MOD = ort.InferenceSession('/home/user/work/models/modnet.onnx', _so)
def talking_head(fr):
    """proxy: a large, centred person in frame = talking-head shot"""
    x = cv2.resize(fr, (288, 512))[:, :, ::-1].astype(np.float32) / 255.0
    m = MOD.run(None, {"input": ((x - 0.5) / 0.5).transpose(2, 0, 1)[None]})[0][0, 0]
    area = (m > 0.5).mean(); cx = (m[:, 96:192] > 0.5).mean()
    return area > 0.16 and cx > 0.25
def scene_cuts(f):
    r = subprocess.run(["ffmpeg","-v","info","-i",f,"-vf","select='gt(scene,0.28)',showinfo","-an","-f","null","-"],capture_output=True,text=True).stderr
    return [float(x) for x in re.findall(r"pts_time:([\d.]+)", r)]
def audio_stats(f):
    r = subprocess.run(["ffmpeg","-v","info","-i",f,"-af","ebur128=framelog=quiet","-f","null","-"],capture_output=True,text=True).stderr
    m = re.search(r"I:\s+(-?[\d.]+) LUFS", r); lufs = float(m.group(1)) if m else None
    raw = subprocess.run(["ffmpeg","-v","error","-i",f,"-ac","1","-ar","22050","-f","s16le","-"],capture_output=True).stdout
    a = np.frombuffer(raw,np.int16).astype(np.float32)/32768
    if len(a) < 22050: return lufs, 0, 0
    hop=512; n=len(a)//hop; fr=a[:n*hop].reshape(n,hop)*np.hanning(hop); S=np.abs(np.fft.rfft(fr,axis=1))
    flux=np.maximum(0,np.diff(np.log1p(S),axis=0)).sum(1); hi=S[:,int(4000/22050*hop):].sum(1)/(S.sum(1)+1e-9)
    thr=flux.mean()+1.6*flux.std(); t=np.arange(len(flux))*hop/22050
    pk=[i for i in range(1,len(flux)-1) if flux[i]>thr and flux[i]>=flux[i-1] and flux[i]>=flux[i+1]]
    on=[]; 
    for i in pk:
        if not on or t[i]-on[-1][0]>0.12: on.append((t[i],hi[i+1]))
    dur=len(a)/22050
    return lufs, len(on)/dur, sum(1 for _,h in on if h>0.25)/dur
def visual(f):
    cap=cv2.VideoCapture(f); fps=cap.get(5) or 30; n=int(cap.get(7)); step=max(1,int(fps/2))
    sats=[];lum=[];con=[];blk=[];faces=0;tot=0;sh=[];hl=[]
    for i in range(0,n,step):
        cap.set(1,i); ok,fr=cap.read()
        if not ok: break
        fr=cv2.resize(fr,(270,480)); hsv=cv2.cvtColor(fr,cv2.COLOR_BGR2HSV); y=cv2.cvtColor(fr,cv2.COLOR_BGR2GRAY).astype(np.float32)/255
        sats.append(hsv[:,:,1].mean()/255); lum.append(y.mean()); con.append(y.std()); blk.append((y<0.07).mean())
        b,g,r=[fr[:,:,c].astype(np.float32) for c in range(3)]
        m1=y<0.25; m2=y>0.7
        if m1.sum()>50: sh.append(((r[m1]-b[m1]).mean(), (g[m1]-(r[m1]+b[m1])/2).mean()))
        if m2.sum()>50: hl.append(((r[m2]-b[m2]).mean(), (g[m2]-(r[m2]+b[m2])/2).mean()))
        faces+= 1 if talking_head(fr) else 0; tot+=1
    shm=np.mean(sh,0) if sh else (0,0); hlm=np.mean(hl,0) if hl else (0,0)
    return dict(sat=float(np.mean(sats)),luma=float(np.mean(lum)),contrast=float(np.mean(con)),black=float(np.mean(blk)),face=faces/max(1,tot),
                shadow_rb=float(shm[0]),shadow_g=float(shm[1]),hi_rb=float(hlm[0]),hi_g=float(hlm[1]))
out=[]
for f in sys.argv[1:]:
    d=float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f],capture_output=True,text=True).stdout or 0)
    cuts=scene_cuts(f); lufs,ons,hions=audio_stats(f); v=visual(f)
    row=dict(file=f.split('/')[-1],dur=round(d,1),cuts=len(cuts),shot=round(d/max(1,len(cuts)+1),2),lufs=lufs,onsets_s=round(ons,2),bright_onsets_s=round(hions,2),**{k:round(x,3) for k,x in v.items()})
    out.append(row); print(json.dumps(row),flush=True)
json.dump(out,open('/home/user/work/research/metrics.json','w'),indent=1)
