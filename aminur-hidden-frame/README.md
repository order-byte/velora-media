# I hid one frame in this video

Promo reel for Aminur (video editor), built to the "Creative Brief × Moodboard" Figma board.
9:16, 1080×1920, 30 fps, 38.9 s, H.264. Captions burned in, no music, sound design only.

**Final files:** [`exports/`](exports/)
- `aminur_hidden_frame.mp4`: the reel
- `aminur_hidden_frame_cover.jpg`: cover frame
- `aminur_hidden_frame.srt`: captions

## The hidden frame
Exactly one frame, **frame 392 of 1,168 (0:13.03)**, inside the 10:00 → 2:00 fast-forward.
It reads **YOU FOUND IT. / FRAME GAME / DM me these 2 words.** The DM keyword is `FRAME GAME`.
Change it with `SECRET` (and the frame with `HIDDEN_FRAME`) in `src/theme.ts`.
A frame counter runs top-left for the whole reel so viewers can say which frame they found.

## How it's made
| Step | File |
| --- | --- |
| Take selection (last clean take of each line) | `scripts/edl.json` |
| Cut, grade, voice clean-up | `scripts/build_selects.py` |
| Person matte (text behind the speaker, cut-out stickers) | `scripts/matte_rvm.py` |
| Beat-by-beat graphics and captions | `src/Reel.tsx`, `src/lib.tsx`, `src/data.ts` |
| Sound design cue sheet (101 cues) | `scripts/sfx_cues.json` |
| Mix + loudness (−14 LUFS, −1 dBTP) | `scripts/mix_audio.py` |
| Grain + final encode | `scripts/finish.sh` |
| SRT | `scripts/make_srt.py` |

Rebuild everything from the raw take:
```bash
npm install
pip install -r scripts/requirements.txt
scripts/build_all.sh raw/raw.mp4
```
Preview and tweak in Remotion Studio with `npm run studio` (needs `public/media/` from step 1–2 of the build).

## Edit decisions
- Script lines missing from the footage: "Ad lagte hi nahi" was never recorded, so the ads beat uses
  the ad-lib that was ("Woh ads hi nahi lagta hai. Kuch aur hi lagta hai."). "Shuruaat… isi video se"
  wasn't recorded either; it's the end-card line.
- Extra lines kept as asked: "I delivered over 2,000 videos and my team is currently handling 60+ clients"
  and "So if you need my service, then contact number in my bio."

See [CREDITS.md](CREDITS.md) for fonts, sound and tool licenses.
