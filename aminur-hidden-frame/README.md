# I hid one frame in this video

Promo reel for Aminur (video editor), built to the "Creative Brief × Moodboard" Figma board.
9:16, 1080×1920, 30 fps, 38.9 s, H.264. Captions burned in, premium filmic grade, dark-stage design system, beat-synced music bed + sound design.

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
| Cut, HDR→SDR + premium grade, voice clean-up | `scripts/build_selects.py` |
| Person matte (text behind the speaker, cut-out stickers) | `scripts/matte_rvm.py` |
| Beat-by-beat graphics and captions | `src/Reel.tsx`, `src/lib.tsx`, `src/data.ts` |
| Sound design cue sheet (107 cues) + music bed placement | `scripts/sfx_cues.json` |
| Music bar alignment (drop on the name reveal, re-entry after the freeze) | `scripts/music_align.py` |
| Mix: SFX + ducked music + voice, −14 LUFS / −1 dBTP | `scripts/mix_audio.py` |
| Grain + final encode | `scripts/finish.sh` |
| SRT | `scripts/make_srt.py` |

Rebuild everything from the raw take:
```bash
npm install
pip install -r scripts/requirements.txt
scripts/build_all.sh raw/raw.mp4
```
Preview and tweak in Remotion Studio with `npm run studio` (needs `public/media/` from step 1–2 of the build).

## Look and sound
- The raw is 10-bit HDR (HLG, BT.2020). It's tone-mapped to SDR with a filmic (Hable) curve that keeps
  the face's highlights instead of clipping them, then graded: true skin with real shape and detail,
  the blue F1-car mic kept saturated and sharp, the green wall light tamed to a deep teal,
  rich-but-not-crushed blacks, local-contrast sharpening (CAS) and a soft vignette.
  The black-and-white moments (hook, scanner, frame-by-frame) get extra contrast on top.
- Design: a dark "stage" with a soft key light behind every graphic beat, glass cards and pills,
  one accent colour (Atomic yellow), blur-and-rise and slot-mask type reveals, no cartoon outlines.
  Cut-outs of Aminur carry a real drop shadow and always sit on the bottom edge of the frame.
- Music: "Daylight Robbery" (Mixkit). Muffled under the mysterious hook, drops on the AMINUR reveal (2.9 s),
  tape-stops into the record-scratch freeze (14.98 s), slams back in at 15.38 s. Track lifts land on the
  10:00 fast-forward, "frame by frame" and EDITOR. The picture pulses on beats and bar downbeats.

## Edit decisions
- Script lines missing from the footage: "Ad lagte hi nahi" was never recorded, so the ads beat uses
  the ad-lib that was ("Woh ads hi nahi lagta hai. Kuch aur hi lagta hai."). "Shuruaat… isi video se"
  wasn't recorded either; it's the end-card line.
- Extra lines kept as asked: "I delivered over 2,000 videos and my team is currently handling 60+ clients"
  and "So if you need my service, then contact number in my bio."

See [CREDITS.md](CREDITS.md) for fonts, sound and tool licenses.
