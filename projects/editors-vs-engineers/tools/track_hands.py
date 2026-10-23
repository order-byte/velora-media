"""Hand landmarks for every frame of the selects clip (MediaPipe Hand Landmarker).

The shoot's purple fill light makes the shaded side of the hands the same colour
as the shirt, so the hands are found by shape instead and get the skin grade.

Usage: python3 track_hands.py hand_landmarker.task SELECTS.mp4 OUT.json
Writes {"frames": [[hand, ...], ...]} with each hand a list of 21 [x, y] in 0..1.
"""
import json
import subprocess
import sys

import mediapipe as mp
import numpy as np

W, H = 1080, 1920
SW, SH = 540, 960


def main():
    model, src, out = sys.argv[1:4]
    opts = mp.tasks.vision.HandLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=model),
        running_mode=mp.tasks.vision.RunningMode.VIDEO, num_hands=2,
        min_hand_detection_confidence=0.35, min_hand_presence_confidence=0.35, min_tracking_confidence=0.35)
    det = mp.tasks.vision.HandLandmarker.create_from_options(opts)
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-vf", f"scale={SW}:{SH}", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    frames, i = [], 0
    while True:
        b = p.stdout.read(SW * SH * 3)
        if len(b) < SW * SH * 3:
            break
        img = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.frombuffer(b, np.uint8).reshape(SH, SW, 3).copy())
        res = det.detect_for_video(img, int(i * 1001 / 24))
        frames.append([[[round(l.x, 4), round(l.y, 4)] for l in hand] for hand in res.hand_landmarks])
        i += 1
    json.dump(dict(frames=frames), open(out, "w"))
    print(f"{i} frames, hands found in {sum(1 for f in frames if f)}")


if __name__ == "__main__":
    main()
