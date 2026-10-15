# Credits and licenses

## Footage and script
Aminur (talent, script, raw footage). Raw take is not stored in this repo.

## Creative direction
"Creative Brief × Moodboard" Figma board (Dolz Agency Scale & Exit): palette, type rules, safe zones,
pacing rules and the five visual directions. Reference reels V1–V9 linked on the board were studied for
pacing and type treatment only; no material from them is used in the edit.

## Fonts (stand-ins, SIL Open Font License 1.1, from Google Fonts)
- **Inter Tight** ExtraBold/Black, standing in for **Europa Grotesk SH Bold** (big words and numbers).
- **Hanken Grotesk**, standing in for **HK Nova** (captions and UI). The board itself names Hanken Grotesk as the HK Nova stand-in.

HK Nova and Europa Grotesk SH are commercial typefaces. To use the licensed files, put them in
`public/fonts/` and point `DISPLAY_FONT_FILES` / `TEXT_FONT_FILES` in `src/theme.ts` at them, then re-render.

## Sound effects
All sound effects are from [Mixkit](https://mixkit.co/free-sound-effects/) under the Mixkit Sound Effects
Free License (commercial use, no attribution required). The files are not redistributed here;
`scripts/fetch_sfx.sh` downloads them by id. No music is used.

## Tools
- [Remotion](https://www.remotion.dev/) for the animated picture. Free for individuals and companies of
  up to 3 people; larger teams need a Remotion company license.
- [Robust Video Matting](https://github.com/PeterL1n/RobustVideoMatting) (MobileNetV3 ONNX) for the person matte.
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (large-v3) for transcription and caption timing.
- FFmpeg for cutting, grading, mixing and the final encode.
