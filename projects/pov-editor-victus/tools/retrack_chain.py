"""Re-track a frame range by chaining consecutive-frame homographies.

Repeating UI structure (timeline rows) can make anchor matching lock one row
off during fast, blurred moves; frame-to-frame matching does not have that
ambiguity. Starts from a trusted frame and walks backwards.
"""
import sys

import cv2
import numpy as np

src, h_path, start, stop = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
plane_top, plane_bottom = float(sys.argv[5]), float(sys.argv[6])

Hs = np.load(h_path)
cap = cv2.VideoCapture(src)
frames = []
while len(frames) <= start:
    ok, f = cap.read()
    frames.append(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY))
h, w = frames[0].shape
sift = cv2.SIFT_create(nfeatures=8000, contrastThreshold=0.015)
bf = cv2.BFMatcher(cv2.NORM_L2)


def plane_mask(H_frame_to_ref):
    # Ref-plane band [plane_top, plane_bottom] projected into the frame.
    quad = np.float32([[-600, plane_top], [1320, plane_top], [1320, plane_bottom], [-600, plane_bottom]])
    q = cv2.perspectiveTransform(quad.reshape(-1, 1, 2), np.linalg.inv(H_frame_to_ref)).reshape(-1, 2)
    m = np.zeros((h, w), np.uint8)
    cv2.fillConvexPoly(m, q.astype(np.int32), 255)
    m[:360] = 0
    return m


for i in range(start - 1, stop - 1, -1):
    a, b = frames[i], frames[i + 1]
    # guess the mask for frame i from frame i+1's pose
    ka, da = sift.detectAndCompute(a, plane_mask(Hs[i + 1]))
    kb, db = sift.detectAndCompute(b, plane_mask(Hs[i + 1]))
    knn = bf.knnMatch(da, db, k=2)
    good = [m for m, n2 in (p for p in knn if len(p) == 2) if m.distance < 0.7 * n2.distance]
    pa = np.float32([ka[m.queryIdx].pt for m in good])
    pb = np.float32([kb[m.trainIdx].pt for m in good])
    # consecutive frames: reject wild matches before RANSAC
    keep = np.linalg.norm(pa - pb, axis=1) < 120
    C, inl = cv2.findHomography(pa[keep], pb[keep], cv2.RANSAC, 1.5, maxIters=8000, confidence=0.9995)
    H = Hs[i + 1] @ C
    Hs[i] = H / H[2, 2]
    print(i, len(good), int(inl.sum()), flush=True)

np.save(h_path, Hs)
