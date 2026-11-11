# JARVIS HUD · build 0.3 (interface test)

Single-page test of the JARVIS interface. No live data yet: panels show demo values.

## What's in this build

- **Cinematic boot.** Panels fly off screen, the reactor core powers up ring by ring,
  then each panel flies back in and latches into place. Every move has a synthesized
  robotic sound (whoosh, servo, latch click, data chatter); no audio files.
- **JARVIS voice (ElevenLabs).** 59 lines recorded with the ElevenLabs voice
  "Spuds Oxley - Grandpa" (voice id `NOpBlnGInO9m6vDvFkFC`, model `eleven_v4`), stored in
  `voice/`. The morning briefing is stitched from them: greeting, time (nearest half hour),
  sleep vs target, advice, sign-off. The core reacts to the real voice level.
- **Basic commands.** Type in the command box or press the mic button. Recognised:
  greetings, time, date, sleep, tasks, messages, money, payments (always refused), health,
  routine, jokes, status, mute, fullscreen, reboot, settings, stop.
- **Browser voice** is still available in Test controls for reading any text.

## Run it locally

The voice clips load with `fetch()`, so serve the folder instead of double-clicking the file:

```bash
cd jarvis/hud && python3 -m http.server 8000
```

Then open http://localhost:8000 in Chrome or Edge and press **Wake JARVIS**.

| Key   | Action                     |
|-------|----------------------------|
| Space | Wake / replay briefing     |
| /     | Type a command             |
| Esc   | Stop / close card or panel |
| M     | Sound effects on/off       |
| S     | Test controls              |
| F     | Fullscreen                 |

## Adding voice lines

Each clip is one MP3 in `voice/`, named by its id (for example `r_hello.mp3`), with its text in
the `CLIPS` table in `index.html`. Clips were trimmed of leading and trailing silence and
encoded as 64 kbps mono:

```bash
ffmpeg -i in.mp3 -af "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.04,areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.08,areverse" -ac 1 -b:a 64k voice/<id>.mp3
```
