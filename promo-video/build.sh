#!/usr/bin/env bash
# Full render: 3 Playwright workers write sub-frames, accumulate.py averages them (motion blur) and encodes.
# Usage: ./build.sh <workDir> <out.mp4>
set -euo pipefail
cd "$(dirname "$0")"
WORK="${1:?work dir}"; OUT="${2:?out mp4}"
rm -rf "$WORK"; mkdir -p "$WORK"
CUTS=(0 210 354 660)
for i in 0 1 2; do node render.js "$WORK" "${CUTS[$i]}" "${CUTS[$((i+1))]}" > "$WORK/worker$i.log" 2>&1 & done
python3 accumulate.py "$WORK" 660 "$OUT" 30
wait
cat "$WORK"/worker*.log
