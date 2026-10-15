"""Measure each sound effect (duration, onset, transient peak) so cues can land on the beat.

Usage: python sfx_info.py <sfx_dir> <out.json>
"""
import subprocess, sys, json, glob, os
import numpy as np
res = {}
for f in sorted(glob.glob(os.path.join(sys.argv[1], '*.wav'))):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', f, '-ac', '1', '-ar', '48000', '-f', 'f32le', '-'], capture_output=True).stdout
    a = np.frombuffer(raw, np.float32)
    if not len(a): continue
    env = np.sqrt(np.convolve(a**2, np.ones(480)/480, 'same'))
    pk = int(np.argmax(env)); peak_db = 20*np.log10(env[pk] + 1e-9)
    on = int(np.argmax(env > env[pk] * 0.1))
    res[os.path.basename(f)[:-4]] = {'dur': round(len(a)/48000, 3), 'onset': round(on/48000, 3), 'peakAt': round(pk/48000, 3), 'peakDb': round(float(peak_db), 1)}
json.dump(res, open(sys.argv[2], 'w'), indent=0)
for k, v in res.items(): print(k, v)
