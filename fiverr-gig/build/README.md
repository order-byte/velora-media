# Build scripts

These scripts made the gig video, music and images. Paths at the top of each file point to the
session's working folders, so change `ROOT` before running them somewhere else.

| Script | Does |
|---|---|
| `music.py OUT.wav` | Synthesizes the original 128.6 BPM track (28 bars + tail, 53.5 s) |
| `render.py OUT.mp4 CUES.json` | Cuts the six client videos into the reel and writes the SFX cue sheet. `--frames 0,230,...` renders stills only |
| `mix.py V1.wav MUSIC.wav CUES.json OUT.wav` | Lays v1's real sound effects on the music at the cue frames |
| `images.py OUT_DIR` | Builds the three 1280×769 gallery images |
| `cutout.py PHOTO OUT.png PREVIEW.jpg` | Keys the lime background out of the profile photo |

Final steps used for the gig video:

```sh
python3 music.py music.wav
python3 render.py reel_video.mp4 cues.json
python3 mix.py v1.wav music.wav cues.json mix.wav
# two-pass loudnorm to -14 LUFS / -1 dBTP -> mix_master.wav, then:
ffmpeg -i reel_video.mp4 -i mix_master.wav -map 0:v -map 1:a -c:v libx264 -preset slow -crf 16 \
  -maxrate 10000k -bufsize 20000k -pix_fmt yuv420p -c:a aac -b:a 256k -movflags +faststart \
  -shortest aminur-showreel-gig-video.mp4
```
