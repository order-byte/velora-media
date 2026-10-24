#!/usr/bin/env bash
# Encode rendered frames + soundtrack into the delivery MP4 (H.264 High, yuv420p, 60 fps).
# usage: scripts/encode.sh <frames dir> <soundtrack.wav> <out.mp4>
set -euo pipefail
frames="$1"; audio="$2"; out="$3"
mkdir -p "$(dirname "$out")"
ffmpeg -y -v error -stats \
  -framerate 60 -i "$frames/f_%05d.png" -i "$audio" \
  -map 0:v -map 1:a \
  -c:v libx264 -preset slow -crf 15 -tune film -pix_fmt yuv420p -profile:v high -level 4.2 \
  -x264-params "aq-mode=3:deblock=-1,-1" \
  -c:a aac -b:a 320k -ar 48000 \
  -shortest -movflags +faststart "$out"
