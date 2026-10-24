# Aminur Rahaman (@aminur_rex) — X profile showreel

A 25-second, 1920×1080, 60 fps showreel for the X profile of **Aminur Rahaman**
("I help SaaS & tech startups explain their product with animated videos").
It is the second version of the Noor Motion edit (`../noor-motion-showreel`), built on
the same engine with these changes:

- **Profile picture in 3D, much bigger.** The person is cut out of the lime backdrop
  (`scripts/prepare_profile.py`, after a 4× Real-ESRGAN upscale of the screenshot crop) and
  sits on its own depth layer, breaking out of the round frame over the header image.
  The profile scene is an X profile card: header, avatar, name, bio, services, Kolkata,
  2,000+ videos delivered, DMs open, and a cursor that clicks **Follow**.
- **Transitions matched to the reference** after measuring it at 30 fps: zoom through the
  title into four black frames, card rising from below, whip pan into a rack-focus, hard cut
  to a tilted chat card, hard cut to a blurred grid close-up with a fast pull-back, cards
  dropping to black between grids with the label growing in, and a straight cut into grid 3.
- **Palette from the X profile**: black-and-white header, lime avatar backdrop.
- **Software** section shows the tools on the header: After Effects, Premiere Pro and the
  orange spark tile (labelled "AI tools").
- Grid labels follow the bio: Product animation · Explainers · Motion graphics.

Music is the reference track; sound effects are cut from the Drive 1 video (see
`scripts/cut_sfx.py`). Portfolio clips come from `scripts/prepare_clips.py`.

Output: `output/aminur_rex_showreel.mp4`

## Rebuild

```
python3 scripts/upscale.py RealESRGAN_x4plus.pth avatar_crop.png av_x4.png banner_crop.png banner_x4.png
python3 scripts/prepare_profile.py av_x4.png banner_x4.png assets
python3 scripts/prepare_clips.py sources.json build/clips
node scripts/render.js --clips build/clips --out build/frames
python3 scripts/mix_audio.py <reference.mp4> assets/sfx build/soundtrack.wav
scripts/encode.sh build/frames build/soundtrack.wav output/aminur_rex_showreel.mp4
```

Fonts: Unbounded and Sora (SIL Open Font License, see `assets/fonts/OFL-*.txt`).
