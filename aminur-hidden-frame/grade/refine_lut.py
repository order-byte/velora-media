"""Judge refinement for LOOK 3 (moody low-key).

Composes a small post-grade tweak onto the LOOK 3 65^3 cube, node by node, so the
ffmpeg chain keeps exactly one lut3d (same speed, no extra interpolation stage).

LUT output domain (from LOOK 3 generator): BT.709 RGB, BT.1886 display encoding,
D = V^2.4.  Tweaks are done in OKLab on D.

usage: python -I refine.py <in.cube> <out.cube> <params.json>
"""
import sys, json
import numpy as np

M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929],
               [0.2119034982, 0.6806995451, 0.1073969566],
               [0.0883024619, 0.2817188376, 0.6299787005]])
M2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468],
               [1.9779984951, -2.4285922050, 0.4505937099],
               [0.0259040371, 0.7827717662, -0.8086757660]])
M1i = np.linalg.inv(M1)
M2i = np.linalg.inv(M2)


def lin_to_oklab(x):
    return np.cbrt(np.maximum(x, 0) @ M1.T) @ M2.T


def oklab_to_lin(lab):
    return (lab @ M2i.T) ** 3 @ M1i.T


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def hue_w(h, c, s):
    d = (h - c + 180) % 360 - 180
    return np.exp(-0.5 * (d / s) ** 2)


def pchip(x, xp, yp):
    xp = np.asarray(xp, float); yp = np.asarray(yp, float)
    h = np.diff(xp); d = np.diff(yp) / h
    m = np.zeros_like(yp)
    for i in range(1, len(xp) - 1):
        if d[i - 1] * d[i] > 0:
            w1 = 2 * h[i] + h[i - 1]; w2 = h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
    m[0] = d[0]; m[-1] = d[-1]
    x = np.clip(x, xp[0], xp[-1])
    k = np.clip(np.searchsorted(xp, x) - 1, 0, len(h) - 1)
    t = (x - xp[k]) / h[k]
    h00 = 2 * t**3 - 3 * t**2 + 1; h10 = t**3 - 2 * t**2 + t
    h01 = -2 * t**3 + 3 * t**2; h11 = t**3 - t**2
    return h00 * yp[k] + h10 * h[k] * m[k] + h01 * yp[k + 1] + h11 * h[k] * m[k + 1]


def gamut_compress(rgb, L):
    g = (np.clip(L, 0, 1) ** 3)[..., None] * np.ones(3)
    d = rgb - g
    with np.errstate(divide='ignore', invalid='ignore'):
        lo = np.where(rgb < 0, g / np.maximum(g - rgb, 1e-9), 1.0)
        hi = np.where(rgb > 1, (1 - g) / np.maximum(rgb - g, 1e-9), 1.0)
    t = np.clip(np.minimum(lo.min(-1), hi.min(-1)), 0, 1)[..., None]
    return g + d * t


def tweak(V, p):
    D = np.clip(V, 0, 1) ** 2.4
    lab = lin_to_oklab(D)
    L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
    C = np.hypot(a, b)
    h = np.degrees(np.arctan2(b, a)) % 360

    # 1) exposure: gentle monotone lift of low-mids/mids on OKLab L, black and white anchored
    L2 = pchip(L, p['tone_x'], p['tone_y'])
    # keep chroma proportional-ish so lifted areas don't go pastel
    ratio = np.where(L > 1e-4, L2 / np.maximum(L, 1e-4), 1.0)
    C2 = C * np.clip(ratio, 0.8, 1.25) ** p['chroma_follow']

    # 2) skin evening: lift low-chroma skin (ashen shadow side of the face) toward a target chroma
    w = hue_w(h, p['skin_h'], p['skin_sigma']) * smoothstep(0.012, 0.03, C)
    w *= smoothstep(p['skin_Llo'][0], p['skin_Llo'][1], L2) * (1 - smoothstep(p['skin_Lhi'][0], p['skin_Lhi'][1], L2))
    C2 = C2 + p['skin_even'] * w * np.maximum(p['skin_target_C'] - C2, 0)
    C2 = C2 * (1 + w * (p.get('skin_sat', 1.0) - 1))
    # small hue pull of those skin pixels toward skin_hue_target (removes the beige/olive cast on the shadow side)
    dh = ((p.get('skin_hue_target', p['skin_h']) - h + 180) % 360) - 180
    h2 = h + p['skin_hue_pull'] * w * dh

    hr = np.radians(h2)
    out = oklab_to_lin(np.stack([L2, C2 * np.cos(hr), C2 * np.sin(hr)], -1))
    out = gamut_compress(out, L2)
    return np.clip(out, 0, 1) ** (1 / 2.4)


def main(inp, outp, params):
    p = json.load(open(params))
    hdr, rows = [], []
    with open(inp) as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            if s[0].isalpha() or s[0] == '#':
                hdr.append(s)
            else:
                rows.append(s)
    V = np.array([list(map(float, r.split())) for r in rows])
    n = [int(h.split()[1]) for h in hdr if h.startswith('LUT_3D_SIZE')][0]
    assert V.shape == (n ** 3, 3), V.shape
    out = tweak(V, p)
    with open(outp, 'w') as f:
        f.write('TITLE "LOOK3 moody low-key + judge refine (input: ffmpeg hable HLG->709, peak 4.9)"\n')
        f.write(f'LUT_3D_SIZE {n}\nDOMAIN_MIN 0 0 0\nDOMAIN_MAX 1 1 1\n')
        np.savetxt(f, out, fmt='%.6f')
    d = np.abs(out - V)
    print(f'nodes {len(V)}  mean|d| {d.mean():.4f}  max|d| {d.max():.4f}')
    # monotonicity sanity on the neutral axis
    g = np.linspace(0, 1, n)
    idx = [int(round(i * (n - 1))) * (1 + n + n * n) for i in g]
    neu = out[idx].mean(1)
    print('neutral axis monotone:', bool(np.all(np.diff(neu) >= -1e-6)), ' black', out[0], ' white', out[-1])


if __name__ == '__main__':
    main(*sys.argv[1:4])
