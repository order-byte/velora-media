# POV: you hire me as your editor — HP Victus × After Effects

A remake of the "POV: you hire me as your editor" reel. The original showed a
MacBook running DaVinci Resolve. This version shows an **HP Victus 15** (black,
backlit keyboard) running **Adobe After Effects 2025 on Windows 11**, with the
McLaren F1 edit playing in the comp and the timeline in sync with it.

Final video: [`output/pov_editor_hp_victus_after_effects.mp4`](output/pov_editor_hp_victus_after_effects.mp4)
(1080×1920, 30 fps, 31.9 s, the edit's own audio).

## What stays the same as the original reel

- The caption, its position and size.
- The camera move: the phone starts low over the keyboard, rises and pushes
  into the screen, then holds handheld. It is tracked from the original reel
  frame by frame, so it shakes and drifts the same way.
- The dark room, warm lamp on the keyboard and screen glow.
- The structure: the full edit plays once in the viewer, start to end.

## What changed

| Original | This version |
| --- | --- |
| MacBook (notch, Mac keyboard) | HP Victus 15: webcam bezel, deep chin with the grey V chevron, black deck with white-backlit keys, numpad, ⏻ after F12, VICTUS / B&O marks |
| DaVinci Resolve on macOS | After Effects 2025 on Windows 11 (title bar, menus, Tools, Project / Composition / Timeline / Effects & Presets panels, taskbar) |
| LA travel edit | The McLaren F1 edit |
| Red playhead over Resolve clips | Blue CTI over a 19-layer AE staircase. Every layer ends exactly on a cut of the edit, and the green RAM-preview line grows behind the CTI |

The edit is 32 s but the original shot is 14 s. After the camera settles, the
handheld hold is played forwards and backwards to cover the remaining time.

## Re-rendering

```bash
pip install opencv-python-headless numpy pillow
cd render
python3 render.py --edit /path/to/mclaren_edit.mp4 --out ../output/pov_editor_hp_victus_after_effects.mp4
# a few frames as PNG for checking:
python3 render.py --edit /path/to/mclaren_edit.mp4 --preview 0,45,300 --png /tmp
```

It renders on all CPU cores; four cores take a few minutes.

To use a different edit, update `SHOTS` and `TOTAL_FRAMES` in
`render/ae_ui.py` (layer names and cut frames) so the timeline matches the
new cuts.

## Layout

- `render/ae_ui.py`: the After Effects screen at the panel's native
  1920×1080, plus the per-frame CTI, timecodes and preview cache.
- `render/victus.py`: the lid and keyboard-deck textures, in millimetres.
- `render/camera.py`: the tracked camera path and the fitted lid/deck geometry.
- `render/render.py`: projects everything through the camera, then adds a
  short-shutter motion blur, screen haze, bloom, lens softness, sensor noise
  and the caption.
- `tools/`: how `data/` was made from the reference reel (SIFT plane
  tracking, row-lock repair by frame chaining, and a fit of focal length, lid
  angle and hinge line against the keyboard's motion).
- `render/fonts/Orbitron.ttf`: stands in for HP's squared key lettering
  (SIL Open Font License, see `OFL.txt`).
