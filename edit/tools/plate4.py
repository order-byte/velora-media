"""Real shelf set behind the speaker, built from a sharp text-free frame of the reference reel.
Upper rows are the real set (toys sit where they really are). Below the level shelf (camera height) the wall is
continued by mirroring the upper rows (correct perspective), using a copy with the toys removed so nothing repeats.
The right side is continued the same way. Colours are left natural (no grade)."""
import sys, numpy as np, cv2
C = cv2.imread('/home/user/work/final/setclean.png').astype(np.float32)
DX, DY = int(sys.argv[2]), int(sys.argv[3])          # where the set sits behind the speaker
LEVEL = 797                                           # level shelf board (camera height)
H, W = 1920, 1080
off = lambda x: 378 - 0.0665 * x                      # height of one cubby row at column x

def swap(img, x0, x1, y0, y1, sign, feather=14):
    """replace a box with the same column one cubby row up (sign=-1) or down (+1)"""
    xs = np.arange(x0, x1); ys = np.arange(y0, y1)
    sy = (ys[:, None] + sign * off(xs)[None, :]).astype(np.float32); sx = np.repeat(xs[None, :].astype(np.float32), len(ys), 0)
    patch = cv2.remap(img, sx, sy, cv2.INTER_LINEAR)
    m = np.zeros((len(ys), len(xs)), np.float32); m[feather:-feather, feather:-feather] = 1
    m = cv2.GaussianBlur(m, (0, 0), feather / 2)[..., None]
    img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - m) + patch * m

CT = C.copy()                                         # toy-free copy for the continued wall
CT[735:800, 0:130] = C[735:800, 115:245]              # little car
swap(CT, 0, 200, 150, 425, +1)                        # radio + books
swap(CT, 570, 760, 225, 470, +1)                      # silver figure
swap(CT, 230, 460, 540, 800, -1)                      # elephant
swap(CT, 895, 1040, 570, 800, -1)                     # orange dog

top = C[:LEVEL]; below = CT[1:LEVEL][::-1]            # mirror about the level shelf
wall = np.vstack([top, below, below[:400]])           # (last part sits behind the table)
wallT = np.vstack([CT[:LEVEL], below, below[:400]])
ext = wallT[:, ::-1][:, :700]                         # right-hand continuation (mirror of the clean wall)
wide = np.hstack([wall, ext[:, 1:]])
canvas = np.zeros((H + 400, W + 400, 3), np.float32)
y0, x0 = 200 + DY, 200 + DX
crop = wide[max(0, -y0):, max(0, -x0):]
canvas[max(0, y0):max(0, y0) + crop.shape[0], max(0, x0):max(0, x0) + crop.shape[1]] = crop[:canvas.shape[0] - max(0, y0), :canvas.shape[1] - max(0, x0)]
plate = canvas[200:200 + H, 200:200 + W]
plate = cv2.GaussianBlur(plate, (0, 0), 2.2)                                   # light depth blur, like the reference
plate += np.random.default_rng(3).normal(0, 2.2, plate.shape).astype(np.float32)  # phone-like sensor noise
cv2.imwrite(sys.argv[1], np.clip(plate, 0, 255).astype(np.uint8))
print("ok")
