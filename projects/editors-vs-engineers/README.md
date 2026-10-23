# Editors vs Engineers reel

Our version of the "Editors are making more than engineers" reel: the script and
edit follow reel 1 (after_zain, words from @theeditingskool), the room and the
colour follow reel 2 (timelinecutsco).

## What is where

| Path | What |
|---|---|
| `edit/takes.json` | Which pieces of the raw shoot are used, in play order, with hand fixes where words run together |
| `edit/plan.py` | Reel 1's cut list re-timed to our speaker's words, plus every caption card |
| `background/reel2_room/plate_mirrored_soft.png` | Reel 2's room with the speaker and on-screen graphics removed, mirrored so its lamp matches our key light, lightly blurred |
| `background/background_*.png` | An earlier, fully procedural room (not used in the final cut) |
| `grade/*.cube` | The warm lamp-room look as a 3D LUT, for use in any editor |
| `fonts/` | Playfair Display (captions) and Luckiest Guy (bar chart), both open-licensed |
| `tools/` | The pipeline, below |

## Pipeline

1. `align_takes.py` forced-aligns the spoken words of each chosen take (wav2vec2).
2. `build_voice.py` cuts the takes on word edges, squeezes long pauses, plays at 1.1x, writes `voice.wav` + `edl.json`.
3. `matte.py` cuts the speaker out (Robust Video Matting, ONNX) of the selects clip.
4. `clean_plate.py` rebuilds reel 2's empty room; `track_reel1.py` tracks reel 1's speaker and editor monitor.
5. `render_reel.py` renders every frame from `edit/plan.py`: talking head in the room (`composite.py`),
   bar chart (`barchart.py`), torn-paper and editor-monitor swaps, reel-1 B-roll, captions (`captions.py`).
6. `mix_audio.py` lays our voice over reel 1's music and effects bed (demucs-separated), re-cut to the new timing.

Raw footage, the two reference reels and intermediate renders are not kept in the repo.
