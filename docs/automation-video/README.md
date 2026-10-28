# Agency explainer video

A 4-minute motion-graphics video explaining how the agency runs on Claude agents,
with a Bangla voiceover and Bangla subtitles. The on-screen text is in English.

- `Agency-Explainer-Bangla.mp4`: the final video (1920×1080, 30 fps)
- `captions_bn.srt`: Bangla subtitles, also burned into the video
- `script.json`: the voiceover script, one entry per spoken line, plus the voice settings

## Rebuilding

```bash
npm install
./get-fonts.sh
node make_icons.js
python3 build_audio.py      # needs: pip install edge-tts numpy; writes audio.wav and timing.js
node render.js frames 4     # needs Playwright with Chromium; writes frames/
ffmpeg -framerate 30 -i frames/f_%05d.jpg -i audio.wav -c:v libx264 -preset slow -crf 20 \
  -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart -shortest Agency-Explainer-Bangla.mp4
```

To change what's said, edit `script.json` and rebuild: the animation cues follow the
word timings the voice produces, so the visuals stay in sync. `node render.js stills 12,40,90`
renders single frames for a quick check.
