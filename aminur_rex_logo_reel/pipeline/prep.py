import cv2, numpy as np, sys, json
S = sys.argv[1]
N = 316
Hs = np.load(f'{S}/H_raw.npy')
Hq = np.load(f'{S}/Hq.npy')
S2 = np.array([[0.5, 0, 0], [0, 0.5, 0], [0, 0, 1]])
M = np.array([Hs[i] @ Hq @ S2 for i in range(N)])
np.save(f'{S}/M.npy', M)
W2, H2 = 1440, 1140

def load(i):
    return cv2.imread(f'{S}/orig/{i+1:04d}.png')

def pink(im):
    b, g, r = [im[..., k].astype(np.int32) for k in range(3)]
    return (r > 110) & (b > 90) & (r - g > 50)

capmask = np.zeros((1280, 720), np.uint8); capmask[890:1065, :] = 255

# --- union of where the original logo (and its glow) ever appears, in 2x screen space
uni = np.zeros((H2, W2), np.float32)
for i in range(12, 300):
    im = load(i)
    p = (pink(im) & (capmask == 0)).astype(np.uint8) * 255
    w = cv2.warpPerspective(p, M[i], (W2, H2), flags=cv2.INTER_NEAREST | cv2.WARP_INVERSE_MAP)
    uni += (w > 0)
ys, xs = np.where(uni > 3)
print('pink extent 2x screen: x', xs.min(), xs.max(), 'y', ys.min(), ys.max())
cv2.imwrite(f'{S}/pink_union.png', np.clip(uni * 4, 0, 255).astype(np.uint8))

# --- clean plate from logo-free frames
pv = []
for i in range(N):
    im = load(i)
    p = pink(im); p[890:1065] = False
    pv.append(int(p.sum()))
clean_ids = [i for i in range(N) if pv[i] < 700 and 10 < i < 296]
print('clean frames', clean_ids)
stack = []; vals = []
for i in clean_ids:
    im = load(i).astype(np.float32)
    w = cv2.warpPerspective(im, M[i], (W2, H2), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_CONSTANT, borderValue=(-1, -1, -1))
    v = cv2.warpPerspective(255 - capmask, M[i], (W2, H2), flags=cv2.INTER_NEAREST | cv2.WARP_INVERSE_MAP)
    w[v == 0] = np.nan
    w[(w < 0).any(2)] = np.nan
    stack.append(w)
stack = np.array(stack)
plate = np.nanmedian(stack, axis=0)
cnt = np.isfinite(stack[..., 0]).sum(0)
print('plate coverage min in patch region', cnt[300:850, 60:1300].min())
plate = np.nan_to_num(plate, nan=0)
np.save(f'{S}/plate.npy', plate.astype(np.float32))
cv2.imwrite(f'{S}/plate.png', np.clip(plate, 0, 255).astype(np.uint8))
json.dump({'pv': pv}, open(f'{S}/pv.json', 'w'))

# --- old caption mask (static white text + emoji)
fr = np.array([cv2.cvtColor(load(i), cv2.COLOR_BGR2GRAY) for i in range(0, N, 3)]).astype(np.float32)
std = fr.std(0); mean = fr.mean(0)
m = np.zeros((1280, 720), np.uint8)
reg = np.zeros_like(m, bool); reg[895:1060, 40:690] = True
m[reg & (std < 10) & (mean > 140)] = 255
m[985:1050, 585:670][(std[985:1050, 585:670] < 14)] = 255
m = cv2.dilate(m, np.ones((7, 7), np.uint8))
cv2.imwrite(f'{S}/oldcap_mask.png', m)
print('oldcap mask px', (m > 0).sum())
