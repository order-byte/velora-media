"""Track the laptop screen plane through the reference reel.

Writes a (N, 3, 3) array of homographies that map each reference-reel frame
onto the chosen anchor frame's screen plane, so the new render can reuse the
original handheld camera move exactly.
"""
import sys

import cv2
import numpy as np

src, out_path = sys.argv[1], sys.argv[2]
anchor = int(sys.argv[3]) if len(sys.argv) > 3 else 90
roi = sys.argv[4] if len(sys.argv) > 4 else "screen"
last = int(sys.argv[5]) if len(sys.argv) > 5 else None

cap = cv2.VideoCapture(src)
frames = []
while True:
    ok, f = cap.read()
    if not ok:
        break
    frames.append(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY))
    if last is not None and len(frames) > last:
        break
n = len(frames)
h, w = frames[0].shape

sift = cv2.SIFT_create(nfeatures=6000, contrastThreshold=0.02)
matcher = cv2.BFMatcher(cv2.NORM_L2)


def region_mask(img):
    m = np.zeros_like(img)
    if roi == "screen":
        # Everything below the caption band; the dark room has no features anyway.
        m[360:, :] = 255
    else:
        # Keyboard deck: in anchor-frame coordinates the screen plane always
        # lands behind the hinge line, so a fixed cut-off isolates the deck.
        m[930:, :] = 255
    return m


ref = frames[anchor]
kr, dr = sift.detectAndCompute(ref, region_mask(ref))


def estimate(img, H_guess):
    warped = cv2.warpPerspective(img, H_guess, (w, h))
    valid = cv2.warpPerspective(np.full_like(img, 255), H_guess, (w, h))
    mask = cv2.bitwise_and(region_mask(warped), cv2.erode(valid, np.ones((9, 9), np.uint8)))
    kw, dw = sift.detectAndCompute(warped, mask)
    if dw is None or len(kw) < 20:
        return None, 0
    knn = matcher.knnMatch(dw, dr, k=2)
    good = [m for m, n2 in (p for p in knn if len(p) == 2) if m.distance < 0.75 * n2.distance]
    if len(good) < 10:
        return None, len(good)
    p_w = np.float32([kw[m.queryIdx].pt for m in good])
    p_r = np.float32([kr[m.trainIdx].pt for m in good])
    C, inl = cv2.findHomography(p_w, p_r, cv2.RANSAC, 2.0, maxIters=5000, confidence=0.999)
    if C is None:
        return None, 0
    return C @ H_guess, int(inl.sum())


Hs = [None] * n
score = np.zeros(n, int)
Hs[anchor] = np.eye(3)
score[anchor] = 9999
for rng in (range(anchor + 1, n), range(anchor - 1, -1, -1)):
    prev = np.eye(3)
    for i in rng:
        H, s = estimate(frames[i], prev)
        if H is not None and s >= (25 if roi == "screen" else 12):
            # second pass from the refined guess tightens large-motion frames
            H2, s2 = estimate(frames[i], H)
            if H2 is not None and s2 >= s:
                H, s = H2, s2
            Hs[i], score[i] = H / H[2, 2], s
            prev = Hs[i]
        else:
            score[i] = s
        print(i, s, flush=True)

np.save(out_path, np.array([H if H is not None else np.full((3, 3), np.nan) for H in Hs]))
np.save(out_path.replace(".npy", "_score.npy"), score)
