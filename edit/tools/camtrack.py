"""Smooth the per-frame face positions into a CapCut-style tracking path (split at the jump cuts so the camera never slides across a cut)."""
import json, sys, numpy as np

def median_filter(x, size, mode=None):
    k = size[0] // 2; p = np.pad(x, ((k, k), (0, 0)), mode='edge')
    return np.stack([np.median(p[i:i + 2 * k + 1], axis=0) for i in range(len(x))])
def gaussian_filter1d(x, sigma, axis=0, mode=None):
    k = int(3 * sigma); w = np.exp(-0.5 * (np.arange(-k, k + 1) / sigma) ** 2); w /= w.sum()
    p = np.pad(x, ((k, k), (0, 0)), mode='edge')
    return np.stack([np.convolve(p[:, j], w, 'valid') for j in range(x.shape[1])], 1)
tr = np.array(json.load(open(sys.argv[1])), np.float32)          # [cx, cy] per frame (30 fps)
cuts = [0] + [int(round(float(c) * 30)) for c in sys.argv[3].split(',')] + [len(tr)]
out = np.zeros((len(tr), 4), np.float32)
for a, b in zip(cuts[:-1], cuts[1:]):
    seg = tr[a:b].copy()
    seg = median_filter(seg, size=(9, 1), mode='nearest')
    seg = gaussian_filter1d(seg, 5, axis=0, mode='nearest')
    out[a:b, :2] = seg; out[a:b, 2:] = np.median(seg, axis=0)
json.dump(np.round(out, 1).tolist(), open(sys.argv[2], 'w'))
d = out[:, :2] - out[:, 2:]
print("face offset range x", d[:, 0].min().round(1), d[:, 0].max().round(1), " y", d[:, 1].min().round(1), d[:, 1].max().round(1))
