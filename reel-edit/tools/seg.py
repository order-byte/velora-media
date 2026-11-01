# Person matte with the MediaPipe selfie multiclass model, run through LiteRT (no GPU/EGL needed).
import numpy as np, cv2
from ai_edge_litert.interpreter import Interpreter
class Segmenter:
    def __init__(self, path, threads=4):
        self.it = Interpreter(model_path=path, num_threads=threads)
        self.it.allocate_tensors()
        self.inp = self.it.get_input_details()[0]
        self.out = self.it.get_output_details()[0]
        self.size = tuple(self.inp["shape"][1:3])  # (h, w)
    def person(self, rgb):
        h, w = rgb.shape[:2]
        x = cv2.resize(rgb, (self.size[1], self.size[0]), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
        self.it.set_tensor(self.inp["index"], x[None])
        self.it.invoke()
        y = self.it.get_tensor(self.out["index"])[0]
        if y.shape[-1] > 1:
            e = np.exp(y - y.max(-1, keepdims=True)); p = e / e.sum(-1, keepdims=True)
            m = 1.0 - p[..., 0]
        else:
            m = y[..., 0]
        m = cv2.resize(m.astype(np.float32), (w, h), interpolation=cv2.INTER_LINEAR)
        return np.clip(m, 0, 1)
