# JARVIS HUD · build 0.2 (interface test)

Single-file test of the JARVIS interface. No live data yet: panels show demo values,
and the morning briefing (time, date, last night's sleep) is spoken with the browser's
built-in English voice as a temporary stand-in for ElevenLabs.

## Run it

Open `index.html` in Chrome or Edge, then press **Wake JARVIS**.

The boot plays like a film HUD: panels fly off screen, the reactor core powers up ring
by ring, then each panel flies back in and latches into place. Every move has a
synthesized robotic sound (whoosh, servo, latch click, data chatter); no audio files.
Click any panel to pull it to the centre; click again or press Esc to send it back.

| Key   | Action               |
|-------|----------------------|
| Space | Play / stop briefing |
| Esc   | Stop / close panel   |
| M     | Sound effects on/off |
| S     | Test controls        |
| F     | Fullscreen           |

**Test controls** let you change the form of address, hours slept, sleep target,
wake-up time, voice, speed, pitch and effects volume. They are saved in the browser.
