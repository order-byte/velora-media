# Sprout promo ad

A 55-second, 1920×1080 / 60 fps promo for **Sprout — Baby Tracker & Care**
(<https://sprout.velorynlabs.co.uk/>).

- **Visual style** follows the NanoSyllabus reference ad: soft lavender/lime gradient
  background, per-letter blur-in kinetic typography with blue accent words, a colour-block
  montage, letterboxed "What if…" section, floating UI cards, dark tile wall, connected
  nodes and a logo end card.
- **Sound** is built only from sound effects cut out of the Commas Affiliate reference ad
  (whoosh swells, falling zips, sub-boom impact, UI pings, mouse clicks, glitch hits,
  rhythmic pulses, chime and outro swell), re-timed to this ad's beats. Like that
  reference, there is no music bed.

Final file: `output/sprout-promo.mp4`

## Story

| Time | Scene |
| --- | --- |
| 0–2 s | App tiles orbit a glowing sprout orb |
| 2–4.4 s | "For too long, baby tracking has worked the same way." |
| 4.4–6.5 s | Montage: Scribble it down · Time it on your phone · Which side was it? · Count the nappies |
| 6.5–11.3 s | "But looking after them shouldn't be about remembering everything." → "It should be about **understanding** them." |
| 11.3–16.6 s | "What if every feed and nap was logged in one tap, easy to understand, even predictable, one day at a time?" with Quick log / Sleep week / Nap window cards |
| 16.6–18.7 s | Sprout logo reveal |
| 18.7–23.4 s | "We turn sleepless guesswork into calm, clear answers." (3D phone, icon cards) |
| 23.4–28.6 s | Dark: Track everything — Sleep. Feeds. Nappies. All in one tap. |
| 28.6–34.4 s | Reports — Spot the patterns. See the trends. Export in one tap. |
| 34.4–39.4 s | Premium — turn a week of logs into a tailored daily routine |
| 39.4–42.7 s | Predictions. Routines. All connected. (nap predictions · schedule creator · Ask Sprout AI) |
| 42.7–46.7 s | Dark wall — From the first feed to the first steps. One day at a time. |
| 46.7–50 s | Making early parenthood easier to track / understand / enjoy |
| 50–55.5 s | Sprout · Watch them sprout. · sprout.velorynlabs.co.uk · Download free |

## Layout

- `src/index.html`, `src/styles.css`, `src/main.js` — the animation. One paused GSAP timeline;
  `window.PROMO.seek(t)` renders any frame and `PROMO.cues` lists the sound-effect placements.
- `src/icons.js` — Lucide icons bundled by `scripts/build_icons.js`.
- `sfx/` — the effects cut from the reference ad, plus `sfx_index.json` (source times).
- `scripts/extract_sfx.py` — re-cuts `sfx/` from the reference video.
- `scripts/render.js` — Playwright frame renderer (stills, cue export, full video).
- `scripts/build_audio.py` — mixes the cue list into the soundtrack.

## Rebuild

```sh
npm install
pip install -r scripts/requirements.txt          # numpy, soundfile
# Playwright must be importable (it is pre-installed globally in the dev container)

npm run icons                                    # only after changing the icon list
node scripts/render.js --stills 3.6,15.6         # quick look at single frames -> output/stills/
node scripts/render.js                           # silent video -> output/video.mp4
node scripts/render.js --cues                    # SFX cue list -> output/cues.json
python scripts/build_audio.py output/cues.json sfx output/sfx_track.wav
ffmpeg -i output/video.mp4 -i output/sfx_track.wav -c:v copy -c:a aac -b:a 256k -shortest output/sprout-promo.mp4
```

Open `src/index.html?play` in a browser for a real-time (silent) preview, or
`src/index.html?t=12.5` to inspect a single moment.
