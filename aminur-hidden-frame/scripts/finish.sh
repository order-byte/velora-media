#!/usr/bin/env bash
# Final master: add film grain to the Remotion picture, lay in the mixed audio, export H.264 for Reels.
# Usage: scripts/finish.sh <picture.mp4> <mix.wav> <out.mp4>
set -euo pipefail
ffmpeg -v error -y -i "$1" -i "$2" \
  -filter_complex "[0:v]noise=c0s=7:c0f=t+u:c1s=2:c1f=t+u:c2s=2:c2f=t+u,format=yuv420p[v]" \
  -map "[v]" -map 1:a \
  -c:v libx264 -preset slow -crf 19 -profile:v high -level 4.2 -pix_fmt yuv420p -r 30 \
  -x264-params "keyint=60:min-keyint=1:scenecut=40" \
  -c:a aac -b:a 256k -ar 48000 -movflags +faststart \
  -metadata title="I hid one frame in this video" "$3"
