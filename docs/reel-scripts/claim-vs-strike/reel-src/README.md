# Claim vs Strike reel: sources

48-second vertical reel (1080×1920, 30 fps). Hindi voiceover, English on-screen text.

- **Voice:** Veena by Maya Research (free, Apache-2.0), speaker `agastya`, generated on CPU by
  `veena_tts.py` from `lines.json`. `check_vo.py` transcribes each line back to catch errors.
- **Music:** "Aphelion" by Scott Buckley, CC BY 4.0 (from about 1:30 into the track). The post caption
  must credit it: `Music: "Aphelion" by Scott Buckley – released under CC-BY 4.0. www.scottbuckley.com.au`
- **Sound effects:** cut only from the reference clip the client supplied (`hpss.py` splits it into
  musical and percussive layers, `extract.py` cuts the individual hits), then pitched and reverbed in `mix.py`.
- **Visuals:** `reel.html` (three.js particles, bloom, film grain; GSAP for text), rendered frame by
  frame by `render.js` from a local web server (`python3 -m http.server 8765`).

Build order: `veena_tts.py` → `build_timeline.py <vo_dir>` → `node render.js frames 4` → `mix.py` →
ffmpeg (`-crf 21 -maxrate 10M`).
