# AMINUR_REX logo reel

- `aminur_rex_logo_reel.mp4`: final 720x1280, 30fps, 10.5s reel with the original audio.
- `compare_side_by_side.mp4`: the original video on the left, the new version on the right.

## What changed from the original
- The pink "PHANTOM" logo is replaced with a lime-green **AMINUR_REX** graffiti logo (Metal Mania font, with 3D extrusion, gloss and drips).
- New logo animation: neon write-on strokes, letter-by-letter pop, an impact flash with sparks, a glossy shine sweep, growing drips and floating embers, then a quick collapse out. It loops in sync with the After Effects playhead, every ~2.15s.
- The caption now reads "POV: Client asked for a demo logo animation 👀" in Instagram-style white rounded boxes.
- The laptop, the After Effects UI, the timeline, the camera movement and the audio are all kept from the original footage.

## Pipeline (`pipeline/`)
1. `track.py`: SIFT + RANSAC homography from the screen to each frame.
2. `rectify.py`: rectifies the screen plane so the logo gets the right perspective.
3. `umap.py`: maps each frame to the loop time of the original animation.
4. `logo.js` + `render.js`: render the logo in Chromium/canvas as a solid pass and an additive light pass.
5. `caption.js`: renders the Instagram-style caption.
6. `prep.py`: builds a clean background plate from logo-free frames and a mask of the old caption.
7. `comp.py`: puts in the clean plate, warps in the tracked logo with motion blur, camera softness and grain, inpaints the old caption, then lays the new caption on top.
