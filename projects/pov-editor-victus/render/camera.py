"""Camera path recovered from the reference reel.

`H_screen.npy` holds, per reference frame, the homography taking that frame
onto the anchor frame's screen plane. `camera_fit.json` holds the focal
length, the residual tilt of the anchor view, the lid opening angle and the
hinge height fitted by tools/fit_deck.py.
"""
import json
import os

import numpy as np

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
CX, CY = 360.0, 640.0  # reference reel is 720x1280
REF_FPS = 29.917
STEADY_FROM = 190  # after this the original shot is a still, handheld hold


class CameraPath:
    def __init__(self):
        self.Hs = np.load(os.path.join(DATA, "H_screen.npy"))
        fit = json.load(open(os.path.join(DATA, "camera_fit.json")))
        self.f, self.beta, self.theta, self.yh = fit["f"], fit["beta"], fit["theta"], fit["yh"]
        self.K = np.array([[self.f, 0, CX], [0, self.f, CY], [0, 0, 1.0]])
        e1 = np.array([1.0, 0, 0])
        e2 = np.array([0, np.cos(self.beta), -np.sin(self.beta)])
        self.plane_to_ref = self.K @ np.column_stack([e1, e2, [0, 0, self.f]])
        self.n = len(self.Hs)

    def ref_index(self, t):
        """Reference-frame index (fractional) for output time t in seconds.

        The reference shot is shorter than the McLaren edit, so once it ends
        the steady handheld hold is played forwards and backwards; reversing
        handheld drift reads as more handheld drift, never as a jump.
        """
        m = t * REF_FPS
        last = self.n - 1
        if m <= last:
            return m
        span = last - STEADY_FROM
        d = (m - last) % (2 * span)
        return last - d if d <= span else STEADY_FROM + (d - span)

    def frame_to_ref(self, m):
        i = int(np.floor(m))
        a = m - i
        i = min(max(i, 0), self.n - 1)
        j = min(i + 1, self.n - 1)
        A = self.Hs[i] / self.Hs[i][2, 2]
        B = self.Hs[j] / self.Hs[j][2, 2]
        return (1 - a) * A + a * B

    def screen_plane_to_image(self, m):
        """Screen-plane coords -> reference-reel image pixels (rigid pose)."""
        R, t = self.pose(m)
        return self.K @ np.column_stack([R[:, 0], R[:, 1], t])

    def pose(self, m):
        M = np.linalg.inv(self.K) @ np.linalg.inv(self.frame_to_ref(m)) @ self.plane_to_ref
        M = M * (2.0 / (np.linalg.norm(M[:, 0]) + np.linalg.norm(M[:, 1])))
        if M[2, 2] < 0:
            M = -M
        U, _, Vt = np.linalg.svd(np.column_stack([M[:, 0], M[:, 1], np.cross(M[:, 0], M[:, 1])]))
        return U @ Vt, M[:, 2]

    def deck_plane_to_image(self, m):
        """Deck coords (u across, v forward from the hinge) -> image pixels."""
        R, t = self.pose(m)
        a = np.pi - self.theta
        d = np.cos(a) * R[:, 1] - np.sin(a) * R[:, 2]
        return self.K @ np.column_stack([R[:, 0], d, self.yh * R[:, 1] + t])
