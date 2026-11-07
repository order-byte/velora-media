# Offscript VSL edit pipeline

Code-driven edit of the client's raw talking-head VSL, matching the reference style
(constant push-ins / punch-ins, kinetic serif text, full-screen graphics, B-roll after the hook).

| Step | Script | Output |
|---|---|---|
| 1. Transcribe | `transcribe.py <audio16k.wav> transcript.json` | word-level timings (faster-whisper) |
| 2. Face track | `facetrack.py <raw.mp4> haarcascade.xml face.json` | speaker position over time |
| 3. Timeline | `build_edl.py transcript.json face.json ../preview/data/edl.json` | shots (zoom), texts, graphics, B-roll |
| 4. Render | `render_chunks.py edl.json raw.mp4 broll/ out/ 3` | 1080p master pieces + 720p preview parts |
| Mattes | `matte.py <raw.mp4> rvm_mobilenetv3_fp32.onnx mattes/ 24:36 268:273` | speaker alpha for graphics behind him |
| B-roll search | `mixkit_search.py "term" ...` | Mixkit free-license stock clip ids |

`motions.py` holds one template per reference motion (r1m1 … r5m6, see `preview/data/analysis.json`);
`gfx.py` is the shared drawing kit. Run the chunk renderer with `MATTES=mattes/` for the behind-the-speaker motions.

`render.py` can also write stills for review: `--stills 8.4,27.2 --stills-dir stills/`.

Requirements: ffmpeg, Python with `numpy opencv-python-headless<5 skia-python faster-whisper onnxruntime`
(Skia needs `libegl1`). Fonts (OFL) live in `assets/fonts/`.

Large media (raw footage, B-roll, renders) is not committed.

## Timeline rules (step 1, motion)
- 0:00–0:41 is the hook + intro: no B-roll, only zoom motion and kinetic text.
- Every shot drifts (slow push-in or pull-out); cuts between wide / medium / close framings make the punch-ins.
- When text sits on one side, the camera shifts the speaker to the other side.
- Hero words get a small scale pulse.
- No sound effects or music yet (steps 2 and 3).

## v1.1 (reference match)
All 30 motions found in the five client references are rebuilt and placed on the matching lines;
each edit-log label carries its reference tag, e.g. `[R2·1] $60,000,000 counter behind the speaker`.
