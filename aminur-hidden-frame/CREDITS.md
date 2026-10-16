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

## Music
"Daylight Robbery" by Michael Ramir C., from [Mixkit](https://mixkit.co/free-stock-music/hip-hop/) (id 1136),
under the Mixkit Stock Music Free License (social media, YouTube and online use, commercial or not;
no attribution required; not for broadcast or physical media). Not redistributed here:
`scripts/fetch_music.sh` downloads it.

## Sound effects
All sound effects are from [Mixkit](https://mixkit.co/free-sound-effects/) under the Mixkit Sound Effects
Free License (commercial use, no attribution required). The files are not redistributed here;
`scripts/fetch_sfx.sh` downloads them by id.

## Tools
- [Remotion](https://www.remotion.dev/) for the animated picture. Free for individuals and companies of
  up to 3 people; larger teams need a Remotion company license.
- [Robust Video Matting](https://github.com/PeterL1n/RobustVideoMatting) (MobileNetV3 ONNX) for the person matte.
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (large-v3) for transcription and caption timing.
- FFmpeg (zscale, tonemap, lut3d) for cutting, HDR-to-SDR conversion, grading, mixing and the final encode.
- librosa (beat tracking), Demucs (vocal check) and pyloudnorm for the music analysis and mix balance.

## Grade
"Soft cream" aesthetic look, built with FFmpeg filters in `scripts/build_selects.py` (HLG tone-map, hue-selective
saturation, curves, colour balance, gentle glow, CAS sharpening).
