# Noor Motion — showreel intro

A 25-second, 1920×1080, 60 fps showreel for the **noor_motion** Instagram page
(NOOR | SaaS Video & Motion Design).

- **Structure and timing** follow the reference edit (the ender.vfx showreel) beat for beat:
  3D title with a cursor selection → profile card → services → chat message → three
  2×2 grids of our work → end card. The cuts sit on the same frames as the reference,
  so its music lands exactly the same way.
- **Colours** come from the profile picture: black glass, molten orange, amber rim light.
- **Work shown**: Commas Affiliate Center, NanoSyllabus, FortKnox (OfflineIQ) and the
  NeuralHive presale ad (9:16, shown over a blurred fill so nothing is cropped). The grid
  categories are the services in the bio: Product videos · UI animation · Explainers.
- **Sound**: the reference track is the music bed; clicks, typing ticks, pops, whooshes
  and the end-card hit are cut from the Drive 1 video's SFX-only audio.

Output: `output/noor_motion_showreel.mp4`

## How it is built

| Step | Script | What it does |
| --- | --- | --- |
| 1 | `scripts/cut_sfx.py <drive1.mp4> assets/sfx` | cuts 29 individual sound effects from the Drive 1 audio |
| 2 | `scripts/prepare_clips.py <sources.json> build/clips` | exports the 12 portfolio segments shown in the grids as 30 fps JPEG frames |
| 3 | `node scripts/render.js --clips build/clips --out build/frames` | renders `scene/index.html` frame by frame in headless Chromium |
| 4 | `scripts/mix_audio.py <reference.mp4> assets/sfx build/soundtrack.wav` | music bed + SFX events, normalised to −14 LUFS |
| 5 | `scripts/encode.sh build/frames build/soundtrack.wav output/noor_motion_showreel.mp4` | H.264 + AAC, ready for Instagram |

`sources.json` maps the work ids (`commas`, `nano`, `fortknox`, `neural`) to the source video files.
The scene is a pure function of time (`window.__render(t)`), so any single frame can be
previewed by opening `scene/index.html?t=12.5&clips=<clips dir>` in Chromium.

Fonts: Unbounded and Sora (SIL Open Font License, see `assets/fonts/OFL-*.txt`).
