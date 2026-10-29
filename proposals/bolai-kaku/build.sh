#!/usr/bin/env bash
# স্লাইড + বাংলা ভয়েস থেকে ভিডিও বানায়।
# দরকার: node + playwright, ffmpeg, edge-tts (pip install edge-tts)
# ব্যবহার: ./build.sh [build ফোল্ডার]   ভয়েস বদলাতে: VOICE=bn-IN-TanishaaNeural ./build.sh
set -euo pipefail
cd "$(dirname "$0")"
B="$(realpath -m "${1:-build}")"
VOICE="${VOICE:-bn-IN-BashkarNeural}"
RATE="${RATE:-+0%}"
EDGE_TTS="${EDGE_TTS:-edge-tts}"
PROXY_ARGS=()
[ -n "${HTTPS_PROXY:-}" ] && PROXY_ARGS=(--proxy "$HTTPS_PROXY")

node render.js "$B"
mkdir -p "$B/audio" "$B/clips"
: > "$B/clips/list.txt"

for say in "$B"/say/*.txt; do
  n="$(basename "$say" .txt)"
  "$EDGE_TTS" "${PROXY_ARGS[@]}" --voice "$VOICE" --rate="$RATE" -f "$say" --write-media "$B/audio/$n.mp3"
  a="$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$B/audio/$n.mp3")"
  # সামনে ০.৩ সেকেন্ড, পেছনে ০.৭ সেকেন্ড ফাঁকা
  d="$(echo "$a + 1.0" | bc -l)"
  ffmpeg -v error -y -loop 1 -framerate 25 -i "$B/png/$n.png" -i "$B/audio/$n.mp3" \
    -filter_complex "[1:a]adelay=300:all=1,apad[a];[0:v]format=yuv420p,fade=t=in:st=0:d=0.3:color=0xfefce8,fade=t=out:st=$(echo "$d - 0.3" | bc -l):d=0.3:color=0xfefce8[v]" \
    -map "[v]" -map "[a]" -t "$d" -c:v libx264 -preset medium -tune stillimage -crf 22 -r 25 \
    -c:a aac -b:a 96k -ar 48000 -ac 1 "$B/clips/$n.mp4"
  echo "file '$n.mp4'" >> "$B/clips/list.txt"
  echo "$n: ${a}s"
done

ffmpeg -v error -y -f concat -safe 0 -i "$B/clips/list.txt" -c copy -movflags +faststart "$B/bolai-kaku-plan.mp4"
echo "done: $B/bolai-kaku-plan.mp4"
