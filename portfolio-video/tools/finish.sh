#!/usr/bin/env bash
# Join rendered parts and add the soundtrack.
#   tools/finish.sh out/part_a.mp4 out/part_b.mp4 ...   (in order; or a single out/video.mp4)
# writes out/aminur_showreel.mp4 (music + sfx) and out/aminur_showreel_sfx_only.mp4
# (sound effects only, for adding a trending track inside Instagram).
set -euo pipefail
cd "$(dirname "$0")/.."
list=$(mktemp)
for p in "$@"; do echo "file '$(realpath "$p")'" >> "$list"; done
ffmpeg -v error -y -f concat -safe 0 -i "$list" -c copy out/video_joined.mp4
rm -f "$list"
for v in mix:aminur_showreel sfx:aminur_showreel_sfx_only; do
  a=${v%%:*}; name=${v##*:}
  ffmpeg -v error -y -i out/video_joined.mp4 -i "out/audio/$a.wav" \
    -map 0:v -map 1:a -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -profile:v high -r 60 \
    -c:a aac -b:a 320k -ar 48000 -shortest -movflags +faststart "out/$name.mp4"
done
ls -la out/aminur_showreel*.mp4
