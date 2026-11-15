#!/usr/bin/env bash
# Full render: Playwright workers write sub-frames, accumulate.py averages them (motion blur) and encodes.
# Usage: ./build.sh <workDir> <out.mp4>      (env: FPS=60, SHUTTER=0.6, WORKERS=3)
set -euo pipefail
cd "$(dirname "$0")"
WORK="${1:?work dir}"; OUT="${2:?out mp4}"
FPS="${FPS:-60}"; SHUTTER="${SHUTTER:-0.6}"; WORKERS="${WORKERS:-3}"
rm -rf "$WORK"; mkdir -p "$WORK"
read -r -a CUTS <<< "$(node probe.js "$WORKERS" "$FPS" "$SHUTTER" | sed -n 's/^CUTS //p')"
FRAMES="${CUTS[${#CUTS[@]}-1]}"
echo "frames=$FRAMES cuts=${CUTS[*]}"
for ((i = 0; i < WORKERS; i++)); do
  node render.js "$WORK" "${CUTS[$i]}" "${CUTS[$((i + 1))]}" "$FPS" "$SHUTTER" > "$WORK/worker$i.log" 2>&1 &
done
python3 accumulate.py "$WORK" "$FRAMES" "$OUT" "$FPS"
wait
cat "$WORK"/worker*.log
