import cv2, numpy as np, sys, json
S=sys.argv[1]; REF=120
N=316
sift=cv2.SIFT_create(nfeatures=6000, contrastThreshold=0.02)
def load(i): return cv2.imread(f'{S}/orig/{i+1:04d}.png')
def mask_for(h,w):
    m=np.full((h,w),255,np.uint8)
    m[890:1065,:]=0   # caption (fixed to frame)
    return m
grays=[cv2.cvtColor(load(i),cv2.COLOR_BGR2GRAY) for i in range(N)]
feats=[]
for i in range(N):
    g=grays[i]
    kp,des=sift.detectAndCompute(g,mask_for(*g.shape))
    feats.append((kp,des))
bf=cv2.BFMatcher(cv2.NORM_L2)
def match(a,b):
    ka,da=feats[a]; kb,db=feats[b]
    if da is None or db is None or len(ka)<10 or len(kb)<10: return None,0
    ms=bf.knnMatch(da,db,k=2)
    good=[m for m,n in (x for x in ms if len(x)==2) if m.distance<0.75*n.distance]
    if len(good)<12: return None,len(good)
    pa=np.float32([ka[m.queryIdx].pt for m in good]); pb=np.float32([kb[m.trainIdx].pt for m in good])
    H,inl=cv2.findHomography(pa,pb,cv2.RANSAC,2.5,maxIters=5000,confidence=0.999)
    return H,int(inl.sum()) if inl is not None else 0
Hs=[None]*N; info=[None]*N
for i in range(N):
    if i==REF: Hs[i]=np.eye(3); info[i]=('ref',9999); continue
    H,n=match(REF,i)
    Hs[i]=H; info[i]=('direct',n)
# fallback chaining where weak
def weak(i): return Hs[i] is None or info[i][1]<60
for direction in (1,-1):
    rng=range(REF+1,N) if direction==1 else range(REF-1,-1,-1)
    for i in rng:
        if weak(i):
            p=i-direction
            Hp,n=match(p,i)
            if Hp is not None:
                Hs[i]=Hp@Hs[p]; info[i]=('chain',n)
for i in range(N):
    print(i, info[i][0], info[i][1])
np.save(f'{S}/H_raw.npy', np.array([h if h is not None else np.eye(3) for h in Hs]))
