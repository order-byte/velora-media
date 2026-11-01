# "How to get clients as a video editor" reel edit

Scripted 9:16 edit of the reel, built from the footage in the shared Google Drive folder.
Live preview page: https://claude.ai/artifact/LSAV3yDW7Ei9vYin9fjoiq

## Pipeline

All paths assume a scratch directory `$S` with `tools/`, `drive/`, `work/` inside it.

1. `tools/dl.py drive-listing.json $S/drive/footage` downloads the Drive files (needs `pip install gdown`).
2. `tools/proxy.sh` converts the iPhone HLG HDR clips to 1080x1920 SDR H.264 proxies in `work/proxy/`.
3. `tools/voice_build.py voice48.wav voice_raw.wav voice_marks.json` cuts the best takes from the voice memo;
   then the ffmpeg chain in the session (highpass, afftdn, EQ, de-esser, compressor, `atempo=1.15`, loudnorm -14 LUFS)
   produces `work/voice_final.wav`.
4. `tools/render.py OUT.mp4` renders the picture (EDL, grading, kinetic text, graphics, transitions).
   `--from/--to/--stills DIR` renders still frames for checking.
5. `tools/audio.py events.json voice_final.wav proxy/IMG_4985.mp4 mix.wav 67.9` mixes voice, closing selfie audio and synthesised SFX.
6. Mux: `ffmpeg -i video.mp4 -i mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k out.mp4`.

Fonts (Anton, Montserrat, Inter from Fontsource) go in `work/fonts/` as TTF; the person matte uses the MediaPipe
`selfie_multiclass_256x256.tflite` model through `ai-edge-litert`.

## AI clips

Scenes 6, 13, 15, 16, 18 and 19 use placeholder shots until the AI clips arrive. Drop them in `work/ai/`
(`AI_06a.mp4`, `AI_13.mp4`, `AI_15a.mp4`, `AI_15b.mp4`, `AI_16.mp4`, `AI_18.mp4`, `AI_19.mp4`, `AI_niche_1..4.png`)
and point the matching EDL rows in `render.py` at them. Prompts are on the live preview page.

Music (Drake – "Shabang") is added inside Instagram at upload time, not baked into the file.

## Version 3 (current): matches the reference reel

- Format: landscape 1440x1014, the same shape as the reference file (1020x718).
- `tools/retime.py` fits each voice phrase into the reference phrase timing (pauses squeezed, rubberband stretch only when needed).
- The reference audio is split with Demucs (`htdemucs --two-stems=vocals`); the `no_vocals` stem is the music + SFX bed.
- `tools/audio3.py bed48.wav voice2_final.wav IMG_4985.mp4 mix.wav 63.15 57.42` mixes bed, voice and the closing selfie audio.
- `tools/proxy14.sh` makes 1440x2560 SDR proxies from the 4K HLG clips; `tools/ai_proxy.py` makes 30 fps AI clip proxies with the corner watermark inpainted.
- `tools/render3.py OUT.mp4` renders the picture: 35 shots timed to the reference cuts, text placed from measurements of the reference frames (`tools/refgrid.py`).
