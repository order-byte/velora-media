import cv2, numpy as np, sys, json, os
S = sys.argv[1]
OUT = sys.argv[2]
only = [int(x) for x in sys.argv[3].split(',')] if len(sys.argv) > 3 and sys.argv[3] else None
os.makedirs(OUT, exist_ok=True)
N = 316
M = np.load(f'{S}/M.npy')
plate = np.load(f'{S}/plate.npy')
fmap = json.load(open(f'{S}/framemap.json'))
W2, H2 = 1440, 1140
FW, FH = 720, 1280

# light temporal smoothing of the homographies (corner-based) to kill tracking jitter
pts = np.float32([[0, 0], [W2, 0], [W2, H2], [0, H2]]).reshape(-1, 1, 2)
corners = np.array([cv2.perspectiveTransform(pts, M[i]).reshape(4, 2) for i in range(N)])
k = np.array([0.25, 0.5, 0.25])
sm = corners.copy()
for i in range(1, N - 1):
    sm[i] = k[0] * corners[i - 1] + k[1] * corners[i] + k[2] * corners[i + 1]
Ms = np.array([cv2.getPerspectiveTransform(pts.reshape(4, 2), sm[i].astype(np.float32)) for i in range(N)])

# patch mask (2x screen): where original logo lived, feathered
patch = np.zeros((H2, W2), np.float32)
patch[270:890, 95:1275] = 1
patch = cv2.GaussianBlur(patch, (0, 0), 22)
# viewer clip (2x screen) for the new logo light/solid so glows stay inside the comp viewer
viewer = np.zeros((H2, W2), np.float32)
viewer[14:1128, :] = 1
viewer = cv2.GaussianBlur(viewer, (0, 0), 2)
# region used to measure exposure gain: viewer area outside the logo zone
ring = np.zeros((H2, W2), np.uint8)
ring[60:1100, 0:W2] = 1
ring[230:930, 60:1320] = 0

cap = cv2.imread(f'{S}/cap/caption.png', cv2.IMREAD_UNCHANGED).astype(np.float32)
cap_a = cap[..., 3:4] / 255.0
cap_rgb = cap[..., :3]
oldcap = cv2.imread(f'{S}/oldcap_mask.png', 0)
inpaint_mask = ((oldcap > 0) & (cap_a[..., 0] < 0.98)).astype(np.uint8) * 255

def load(i):
    return cv2.imread(f'{S}/orig/{i+1:04d}.png')

# --- exposure gain per frame (frame / plate) in the ring region
gains = []
for i in range(N):
    f = load(i).astype(np.float32)
    pw = cv2.warpPerspective(plate, Ms[i], (FW, FH), flags=cv2.INTER_LINEAR)
    rw = cv2.warpPerspective(ring, Ms[i], (FW, FH), flags=cv2.INTER_NEAREST)
    rw[880:1070] = 0
    sel = rw > 0
    if sel.sum() < 2000:
        gains.append(None); continue
    g = np.array([np.median(f[..., c][sel]) / max(np.median(pw[..., c][sel]), 1) for c in range(3)])
    gains.append(g)
gl = np.array([g if g is not None else [np.nan] * 3 for g in gains])
for c in range(3):
    col = gl[:, c]; idx = np.arange(N); ok = np.isfinite(col)
    gl[:, c] = np.interp(idx, idx[ok], col[ok])
gs = gl.copy()
for i in range(N):
    a, b = max(0, i - 4), min(N, i + 5)
    gs[i] = gl[a:b].mean(0)
gs = np.clip(gs, 0.6, 1.6)

# logo-centre velocity for motion blur
cen = np.array([cv2.perspectiveTransform(np.float32([[[672, 560]]]), Ms[i])[0, 0] for i in range(N)])

def motion_kernel(v, shutter=0.55):
    L = np.linalg.norm(v) * shutter
    if L < 1.2:
        return None
    n = int(np.ceil(L)) | 1
    n = max(n, 3)
    ker = np.zeros((n, n), np.float32)
    c = n // 2
    d = v / np.linalg.norm(v)
    for t in np.linspace(-L / 2, L / 2, int(L * 3) + 2):
        x, y = c + d[0] * t, c + d[1] * t
        xi, yi = int(round(x)), int(round(y))
        if 0 <= xi < n and 0 <= yi < n:
            ker[yi, xi] += 1
    return ker / ker.sum()

rng = np.random.default_rng(3)
layer_cache = {}
def get_layers(name):
    if name not in layer_cache:
        so = cv2.imread(f'{S}/layers/solid_{name}.png', cv2.IMREAD_UNCHANGED).astype(np.float32) / 255
        li = cv2.imread(f'{S}/layers/light_{name}.png').astype(np.float32) / 255
        a = so[..., 3:4] * viewer[..., None]
        prem = so[..., :3] * a
        li = li * viewer[..., None]
        sig = 0.8
        prem = cv2.GaussianBlur(prem, (0, 0), sig); a = cv2.GaussianBlur(a, (0, 0), sig)[..., None]; li = cv2.GaussianBlur(li, (0, 0), sig)
        layer_cache[name] = (prem, a, li)
    return layer_cache[name]

frames = only if only is not None else range(N)
for i in frames:
    f = load(i).astype(np.float32)
    H = Ms[i]
    g = gs[i]
    # 1) replace original logo region with clean plate (exposure matched)
    pw = cv2.warpPerspective(plate, H, (FW, FH), flags=cv2.INTER_LINEAR) * g[None, None, :]
    A = cv2.warpPerspective(patch, H, (FW, FH), flags=cv2.INTER_LINEAR)[..., None]
    noise = rng.normal(0, 2.2, (FH, FW, 1)).astype(np.float32)
    noise = cv2.GaussianBlur(noise, (0, 0), 0.6)[..., None] * 1.6
    base = f * (1 - A) + (pw + noise) * A
    # 2) new logo layers
    prem, a, li = get_layers(fmap[str(i)])
    wp = cv2.warpPerspective(prem, H, (FW, FH), flags=cv2.INTER_LINEAR)
    wa = cv2.warpPerspective(a, H, (FW, FH), flags=cv2.INTER_LINEAR)
    wl = cv2.warpPerspective(li, H, (FW, FH), flags=cv2.INTER_LINEAR)
    v = (cen[min(i + 1, N - 1)] - cen[max(i - 1, 0)]) / 2
    ker = motion_kernel(v)
    if ker is not None:
        wp = cv2.filter2D(wp, -1, ker); wa = cv2.filter2D(wa, -1, ker); wl = cv2.filter2D(wl, -1, ker)
    cam = 0.55
    wp = cv2.GaussianBlur(wp, (0, 0), cam); wa = cv2.GaussianBlur(wa, (0, 0), cam); wl = cv2.GaussianBlur(wl, (0, 0), cam)
    if wa.ndim == 2: wa = wa[..., None]
    gl_ = (g / g.mean()) * min(g.mean(), 1.15)
    out = base * (1 - wa) + wp * 255 * 0.96 * gl_[None, None, :]
    out = out + wl * 255 * 0.95 * gl_[None, None, :]
    # soft highlight roll-off like a phone camera
    out = np.where(out > 220, 220 + (out - 220) * 0.55, out)
    out = np.clip(out, 0, 255).astype(np.uint8)
    # 3) caption: inpaint old text edges, then draw the new Instagram-style caption
    out = cv2.inpaint(out, inpaint_mask, 5, cv2.INPAINT_TELEA)
    o = out.astype(np.float32) * (1 - cap_a) + cap_rgb * cap_a
    cv2.imwrite(f'{OUT}/{i+1:04d}.png', np.clip(o, 0, 255).astype(np.uint8))
print('done', len(list(frames)))
