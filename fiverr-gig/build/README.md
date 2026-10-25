# Build scripts

These scripts made the gig video, music and images. Paths at the top of each file point to the
session's working folders, so change `ROOT` before running them somewhere else.

| Script | Does |
|---|---|
| `music.py OUT.wav` | First synthesized track (replaced by the Mixkit track) |
| `analyze_tracks.py DIR OUT.json` | Measures tempo, beat strength, drops and brightness of candidate tracks |
| `edit_music.py TRACK.mp3 OUT.wav REPORT.json` | Stretches a track to 128.57 BPM with rubberband and cuts it on bar lines to the reel's 28-bar structure |
| `gridcheck.py EDIT.wav ...` | Checks that kicks land on the video's beat grid per section |
| `make_option.sh ID` | Loudness-matches an edit, adds the v1 SFX, masters to -14 LUFS and muxes a 720p preview |
| `render.py OUT.mp4 CUES.json` | Cuts the six client videos into the reel and writes the SFX cue sheet. `--frames 0,230,...` renders stills only |
| `mix.py V1.wav MUSIC.wav CUES.json OUT.wav` | Lays v1's real sound effects on the music at the cue frames |
| `images.py OUT_DIR` | Builds the three 1280×769 gallery images |
| `cutout.py PHOTO OUT.png PREVIEW.jpg` | Keys the lime background out of the profile photo |

Final steps used for the gig video:

```sh
python3 render.py reel_video.mp4 cues.json
python3 edit_music.py 471.mp3 music.wav music.json      # Rising Forest
# normalize music.wav to -12 LUFS, then
SFX_GAIN=1.1 python3 mix.py v1.wav music.wav cues.json mix.wav
# two-pass loudnorm to -14 LUFS / -2 dBTP, 30 ms fade-in -> mix_master.wav, then:
ffmpeg -i reel_video.mp4 -i mix_master.wav -map 0:v -map 1:a -c:v libx264 -preset slow -crf 16 \
  -maxrate 10000k -bufsize 20000k -pix_fmt yuv420p -c:a aac -b:a 256k -movflags +faststart \
  -shortest aminur-showreel-gig-video.mp4
```
