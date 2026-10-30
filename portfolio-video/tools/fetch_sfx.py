"""Download the recorded sound effects used by tools/make_audio.py from Mixkit's free
sound-effects library (Mixkit Sound Effects Free License: free for commercial use, no
attribution; the raw files are not redistributed in this repo), convert them to 48 kHz
WAV and slice single keystrokes out of the typing recording.

usage: python3 tools/fetch_sfx.py
"""
import os, subprocess
import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
DST = os.path.join(os.path.dirname(HERE), 'assets', 'sfx')
IDS = {'whoosh_fast': 1490, 'whoosh_cine': 1492, 'whoosh_air': 1489, 'sweep_small': 166, 'swoosh_fast': 3115, 'sweep_short': 175, 'sweep_fast': 174, 'sweep_air': 168, 'swoosh_accent': 1464, 'swoosh_speed': 1484, 'swoosh_wind_short': 1461, 'swoosh_windy': 1474, 'sparkle_whoosh': 2350, 'fairy_whoosh': 869, 'sweep_magic': 2638, 'pop_bubble': 2357, 'pop_message': 2354, 'pop_hard': 2364, 'pop_dry': 2356, 'pop_long': 2358, 'pop_explainer': 3005, 'click_select': 1109, 'click_modern': 3124, 'click_tone': 2568, 'click_mouse': 1113, 'click_classic': 1117, 'click_check': 1120, 'click_device': 2577, 'click_bubble': 1124, 'click_double': 275, 'type_laptop': 2531, 'type_single': 2533, 'type_press': 2541, 'type_hard': 2542, 'type_phone': 2535, 'type_fast': 1387, 'impact_deep': 1143, 'impact_logo': 2900, 'impact_zoom': 772, 'impact_big': 788, 'impact_intro': 2902, 'impact_reverse': 784, 'vacuum_zoom': 2608, 'beep_positive': 221, 'notify_positive': 265, 'alert_tech': 3218, 'shutter': 1133, 'intro_transition': 1146, 'tech_slide': 3120}


def main():
    os.makedirs(DST, exist_ok=True)
    for name, i in IDS.items():
        wav = os.path.join(DST, f'{name}.wav')
        if os.path.exists(wav):
            continue
        mp3 = wav[:-4] + '.mp3'
        subprocess.run(['curl', '-sS', '-m', '60', '-o', mp3, f'https://assets.mixkit.co/active_storage/sfx/{i}/{i}-preview.mp3'], check=True)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', mp3, '-ac', '2', '-ar', '48000', wav], check=True)
        os.remove(mp3)
    # single keystrokes from the laptop typing take
    x, sr = sf.read(os.path.join(DST, 'type_laptop.wav')); m = x.mean(1)
    env = np.sqrt(np.convolve(m ** 2, np.ones(96) / 96, 'same')); d = np.diff(env, prepend=0)
    thr, keys, i = env.max() * 0.25, [], 0
    while i < len(env) and len(keys) < 40:
        if env[i] > thr and d[i] > 0:
            a = max(0, i - int(0.004 * sr)); seg = x[a:a + int(0.085 * sr)].copy()
            fade = np.linspace(1, 0, int(0.02 * sr)); seg[-len(fade):] *= fade[:, None]
            keys.append(seg / (np.abs(seg).max() + 1e-9)); i += int(0.09 * sr)
        else:
            i += 1
    np.save(os.path.join(DST, 'keys.npy'), np.array(keys))
    print(len(IDS), 'effects,', len(keys), 'keystrokes in', DST)


if __name__ == '__main__':
    main()
