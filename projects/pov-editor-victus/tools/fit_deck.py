"""Fit focal length, screen tilt, lid angle and hinge height.

Uses the tracked screen homographies plus the keyboard-deck track of the
opening frames, so the deck of the new laptop can be projected for every
frame from the screen track alone.
"""
import itertools
import json
import sys

import numpy as np

S = sys.argv[1]
Hs = np.load(f"{S}/H_screen.npy")
Dk = np.load(f"{S}/H_deck.npy")
sc = np.load(f"{S}/H_deck_score.npy")
CX, CY = 360.0, 640.0
frames = [i for i in range(0, 25) if sc[i] >= 90 and not np.isnan(Dk[i]).any()]

gx, gy = np.meshgrid(np.linspace(60, 660, 9), np.linspace(960, 1240, 6))
pts0 = np.stack([gx.ravel(), gy.ravel(), np.ones(gx.size)])


def K(f):
    return np.array([[f, 0, CX], [0, f, CY], [0, 0, 1.0]])


def plane_to_ref(f, beta):
    e1 = np.array([1.0, 0, 0])
    e2 = np.array([0, np.cos(beta), -np.sin(beta)])
    c0 = np.array([0, 0, f])
    return K(f) @ np.column_stack([e1, e2, c0])


def pose(f, beta, i):
    M = np.linalg.inv(K(f)) @ np.linalg.inv(Hs[i]) @ plane_to_ref(f, beta)
    lam = 2.0 / (np.linalg.norm(M[:, 0]) + np.linalg.norm(M[:, 1]))
    M = M * lam
    if M[2, 2] < 0:
        M = -M
    r1, r2, t = M[:, 0], M[:, 1], M[:, 2]
    U, _, Vt = np.linalg.svd(np.column_stack([r1, r2, np.cross(r1, r2)]))
    R = U @ Vt
    return R, t


def deck_h(f, beta, theta, yh, i):
    R, t = pose(f, beta, i)
    a = np.pi - theta
    d = np.cos(a) * R[:, 1] - np.sin(a) * R[:, 2]
    return K(f) @ np.column_stack([R[:, 0], d, yh * R[:, 1] + t])


def err(params):
    f, beta, theta, yh = params
    G0inv = np.linalg.inv(deck_h(f, beta, theta, yh, 0))
    e = 0.0
    for i in frames:
        pred = deck_h(f, beta, theta, yh, i) @ G0inv @ pts0
        pred = pred[:2] / pred[2]
        obs = np.linalg.inv(Dk[i]) @ pts0
        obs = obs[:2] / obs[2]
        e += np.mean(np.sum((pred - obs) ** 2, axis=0))
    return np.sqrt(e / len(frames))


best = None
for f, beta, theta, yh in itertools.product(
    np.linspace(600, 3000, 25), np.radians(np.linspace(-15, 25, 9)),
    np.radians(np.linspace(95, 135, 9)), np.linspace(520, 680, 9)):
    e = err((f, beta, theta, yh))
    if best is None or e < best[0]:
        best = (e, (f, beta, theta, yh))
print("coarse", best[0], best[1][0], np.degrees(best[1][1]), np.degrees(best[1][2]), best[1][3])

# coordinate-descent refinement
p = np.array(best[1], float)
step = np.array([100, np.radians(2.5), np.radians(2.5), 10])
e0 = best[0]
for _ in range(60):
    improved = False
    for k in range(4):
        for s in (+1, -1):
            q = p.copy(); q[k] += s * step[k]
            e = err(q)
            if e < e0:
                p, e0, improved = q, e, True
    if not improved:
        step /= 2
f, beta, theta, yh = p
print("refined rms px", e0, "f", f, "beta", np.degrees(beta), "theta", np.degrees(theta), "yh", yh)
json.dump({"f": f, "beta": beta, "theta": theta, "yh": yh, "rms": e0}, open(f"{S}/camera_fit.json", "w"), indent=1)
