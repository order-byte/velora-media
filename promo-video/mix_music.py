"""Mix a music track under the voice + SFX, beat-aligned to the reference edit.
Usage: python mix_music.py <music.mp3> <music_beat_to_start_on_sec> <reference_mix.wav> <voice_aligned.wav> <sfx.wav> <silent.mp4> <out_prefix>
The music is shifted so its beats land where the reference music's beats were (129 BPM grid), ducked under the voice, and the mix is set to -14 LUFS."""
import sys, subprocess, re, numpy as np, librosa
mp3, mstart, refmix, vo, sfx, video, outp = sys.argv[1:8]
mstart = float(mstart)
def ff(*a): subprocess.run(['ffmpeg', '-v', 'error', '-y', *a], check=True)
def lufs(path, extra=''):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-i', path, '-af', (extra + ',' if extra else '') + 'ebur128=framelog=quiet', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return float(re.findall(r'I:\s+(-?[\d.]+) LUFS', r)[-1])
# beat phase of the reference edit's music
y, sr = librosa.load(refmix, sr=22050)
_, b = librosa.beat.beat_track(y=y, sr=sr, start_bpm=129)
bt = librosa.frames_to_time(b, sr=sr)
P = float(np.median(np.diff(bt)))
phase = float(np.median(bt % P))
# shift the music so its chosen beat lands on the reference beat grid
start = max(0.0, mstart - phase)
tmp = outp + '_music.wav'
ff('-ss', f'{start:.3f}', '-t', '22', '-i', mp3, '-ac', '2', '-ar', '48000',
   '-af', 'afade=t=in:d=0.12,afade=t=out:st=21.1:d=0.9', tmp)
gain = -25.0 - lufs(tmp)
mix = outp + '_mix.wav'
ff('-i', vo, '-i', sfx, '-i', tmp, '-filter_complex',
   '[0]highpass=f=70,acompressor=threshold=0.125:ratio=2.5:attack=8:release=120:makeup=1.6,aformat=channel_layouts=stereo,asplit=2[v][sc];'
   '[1]aformat=channel_layouts=stereo,volume=0.55[s];'
   f'[2]volume={gain:.2f}dB[m0];[m0][sc]sidechaincompress=threshold=0.04:ratio=3.5:attack=25:release=350:knee=4[m];'
   '[v][s][m]amix=inputs=3:normalize=0:duration=longest,loudnorm=I=-14:TP=-1:LRA=11',
   '-ar', '48000', '-c:a', 'pcm_s24le', mix)
ff('-i', video, '-i', mix, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-shortest', '-movflags', '+faststart', outp + '.mp4')
print(f'period {P:.3f}s phase {phase:.3f}s music_from {start:.2f}s gain {gain:.1f}dB -> {outp}.mp4')
