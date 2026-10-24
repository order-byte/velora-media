# Monthly package reel: edit project

Code-driven edit of the Aminur Rex Team monthly-package reel.

- `tools/`: footage pipeline (Whisper transcription, take selection, energy-based cut points, base render with grade + voice chain)
- `data/`: transcript, cut list (`edl.json`) and the output timeline with word timings (`timeline.json`)
- `reel/`: Remotion project (captions, motion graphics, scenes, SFX map). Media in `reel/public/` is not committed.

Render: `cd reel && npm install && npx remotion render src/index.ts Reel out/reel.mp4`
