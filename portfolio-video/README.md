# Aminur Rahaman showreel

A 30-second, 1920×1080 @ 60fps motion-graphics portfolio video for
[@aminur_rex](https://instagram.com/aminur_rex), styled after five reference reels
(glass/frost reveals, blur-in type, chat bubbles, prompt bars, card stacks, 2×2 grids,
pill marquees). Every frame is an HTML/CSS scene driven by a deterministic timeline,
rendered frame by frame with Playwright and encoded with ffmpeg. The soundtrack and
sound effects are synthesised from scratch, so they are free to use anywhere.

## Story (120 BPM, one bar = 2 s)

| Time | Scene | What happens |
|---|---|---|
| 0–4s | Glass hook | Violet fluted glass melts into a dusk sky; a liquid-glass pill with a lime neon orbit types "Need a video that stops the scroll?" and answers "Say less. Watch this." |
| 4–8s | Client chat | A founder messages Aminur; bubbles type in with emoji stickers. |
| 8–10s | Prompt | Dark prompt bar, "Make it smooth, bold & unforgettable", send. |
| 10–14s | Gradient title | Liquid wave, "Ready to launch?", aminur_rex reveal, "Promos for SaaS / Gaming / EdTech / AI tools / Tech brands". |
| 14–18s | Showcase | "Promos [card stack of real projects] that convert.", then a stream of project cards. |
| 18–22s | Grid | Eight projects, four at a time, in a 2×2 grid. |
| 22–24s | Services | Service-pill marquee and a "1,000+ videos delivered" counter. |
| 24–26s | Profile | Glass Instagram card; Follow gets tapped. |
| 26–30s | Sign-off | aminur_rex logo, tagline, "Book a call". |

## Layout

```
config.js            name, handle, stats, booking link, avatar path
index.html           the composition the renderer loads
preview.html         live preview player (published as a claude.ai artifact)
style.css            stage styles shared by both
js/engine.js         timeline engine: easing, keyframes, blur-in/typing helpers, __seek(t)
js/kit.js            shared parts: procedural sky, Clip (video in preview, exact frames in render)
js/s1-…s9-*.js       one file per scene
render.mjs           frame renderer -> out/video.mp4
tools/prepare_work.py   cuts project excerpts, upscales, converts to 1080p60 frames
tools/esrgan.py         Real-ESRGAN (realesr-general-x4v3) upscaler used for 736p sources
tools/make_audio.py     soundtrack + SFX -> out/audio/{mix,music,sfx}.wav
```

## Rebuild

```bash
# 1. project videos go in assets/work/raw/ (csgogem.mp4, nanosyllabus.mp4, fortknox.mp4,
#    quadrant.mp4, balcony_pin.mp4, habit_pin.mp4), then:
pip install numpy scipy soundfile pillow torch
ESRGAN_WEIGHTS=/path/to/realesr-general-x4v3.pth python3 tools/prepare_work.py
python3 tools/make_audio.py
node render.mjs                     # or: node render.mjs --from 14 --to 18 for a slice
ffmpeg -i out/video.mp4 -i out/audio/mix.wav -c:v copy -c:a aac -b:a 320k -shortest out/aminur_showreel.mp4
```

To use your own profile photo, save it as `assets/me/profile.jpg` (square crop works best).
