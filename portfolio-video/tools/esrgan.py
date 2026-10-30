"""Real-ESRGAN (realesr-general-x4v3, SRVGGNetCompact) upscaler for a folder of PNG frames.
usage: python3 esrgan.py weights.pth in_dir out_dir [out_w out_h]"""
import sys, os, glob, torch, torch.nn as nn, torch.nn.functional as F, numpy as np
from PIL import Image

class SRVGGNetCompact(nn.Module):
    def __init__(self, num_in_ch=3, num_out_ch=3, num_feat=64, num_conv=32, upscale=4):
        super().__init__()
        self.upscale = upscale
        self.body = nn.ModuleList([nn.Conv2d(num_in_ch, num_feat, 3, 1, 1), nn.PReLU(num_parameters=num_feat)])
        for _ in range(num_conv):
            self.body.append(nn.Conv2d(num_feat, num_feat, 3, 1, 1))
            self.body.append(nn.PReLU(num_parameters=num_feat))
        self.body.append(nn.Conv2d(num_feat, num_out_ch * upscale * upscale, 3, 1, 1))
        self.upsampler = nn.PixelShuffle(upscale)

    def forward(self, x):
        out = x
        for layer in self.body:
            out = layer(out)
        out = self.upsampler(out)
        return out + F.interpolate(x, scale_factor=self.upscale, mode='nearest')

weights, src, dst = sys.argv[1:4]
size = (int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else None
os.makedirs(dst, exist_ok=True)
torch.set_num_threads(os.cpu_count())
net = SRVGGNetCompact()
sd = torch.load(weights, map_location='cpu')
net.load_state_dict(sd.get('params', sd.get('params_ema', sd)))
net.eval()
files = sorted(glob.glob(os.path.join(src, '*.png')))
import time
t0 = time.time()
with torch.inference_mode():
    for i, f in enumerate(files):
        out_path = os.path.join(dst, os.path.basename(f))
        if os.path.exists(out_path):
            continue
        img = np.asarray(Image.open(f).convert('RGB'), dtype=np.float32) / 255.0
        x = torch.from_numpy(img).permute(2, 0, 1)[None]
        y = net(x).clamp(0, 1)[0].permute(1, 2, 0).numpy()
        im = Image.fromarray((y * 255.0 + 0.5).astype(np.uint8))
        if size:
            im = im.resize(size, Image.LANCZOS)
        im.save(out_path)
        if i % 10 == 0:
            print(f'{i+1}/{len(files)}  {(time.time()-t0)/(i+1):.2f}s/frame', flush=True)
