# Aminur Rex SFX Pack — promo video

A 22-second, 1920×1080, 30 fps motion-graphics promo. It follows the reference ad beat for beat, with Aminur Rex brand elements in place of the reference's.

## Files

| File | What it is |
|---|---|
| `out/aminur_rex_promo_with_voice.mp4` | **Final:** the video with the ElevenLabs voice and the sound effects. No music yet. |
| `out/aminur_rex_promo_sfx.mp4` | The video with the sound effects only. |
| `out/aminur_rex_promo_silent.mp4` | The same video with no audio. |
| `audio/sfx_track.wav` | The sound effects alone, 22 s, 48 kHz, 24-bit. Drop it on the timeline at 0:00. |
| `audio/voice_aligned.wav` | The voice alone, already placed in time. Drop it on the timeline at 0:00. |
| `audio/final_mix_voice_sfx.wav` | Voice + SFX mixed at -14 LUFS, the audio of the final video. |
| `SCRIPT.md` | The voiceover script, the ElevenLabs voice and settings, and each line's time slot. |
| `logo.png` | The profile-photo logo, square. The video crops it to a circle. |
| `index.html` | The animation. Open `index.html#play` in a browser for a live preview. |
| `render.js`, `accumulate.py`, `build.sh` | The renderer. It draws several sub-frames per frame and averages them for real motion blur. |
| `fit_vo.py` | Cuts the ElevenLabs voiceover into its 8 lines, places each in its slot, and mixes it with the SFX. |

## Scenes

| Time | Scene |
|---|---|
| 0.0–1.6 | "Want your edits to hit harder?": kinetic words on black, camera pulls back |
| 1.6–2.5 | Headphone emoji rolls in, "Say hello to...", the frame flies off as a card |
| 2.4–3.8 | Logo reveal: photo logo + AMINUR REX / SFX PACK, whip exit |
| 3.8–5.7 | Vinyl and CD spin in, the search bar types "Best SFX pack for video editors", camera follows |
| 5.6–8.6 | The store page builds from its nav bar, then a 3D zoom and pan across the hero |
| 8.6–12.8 | 15 sound-folder tiles pop in, 3D camera moves, the cursor clicks PLAY |
| 12.8–15.0 | "Punchy sounds that hit just right." |
| 15.0–16.5 | Phone list of sounds scrolls |
| 16.5–19.9 | "Drag. Drop. Done." → "You can't say [logo] without saying..." → line wipe |
| 19.9–22.0 | End card: logo + @aminurrex |

## Changing things

- Handle, logo file and crop: `CONFIG` at the top of the script in `index.html`.
- Text: the word lists in `init()` (scenes A and F), `'Say hello to'`, the search text, `GRID_ITEMS`, `LIST_ITEMS`, and `'Drag. Drop. Done.'`.

## Rebuilding

Needs Node with Playwright and Chromium, Python 3 with numpy and Pillow, and ffmpeg.

```bash
./build.sh /tmp/work out/aminur_rex_promo_silent.mp4
```

Then add the sound effects:

```bash
ffmpeg -i out/aminur_rex_promo_silent.mp4 -i audio/sfx_track.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -shortest out/aminur_rex_promo_sfx.mp4
```

Once the voiceover exists (needs `faster-whisper`):

```bash
python fit_vo.py voice.mp3 audio/sfx_track.wav out/aminur_rex_promo_silent.mp4 out/
```
