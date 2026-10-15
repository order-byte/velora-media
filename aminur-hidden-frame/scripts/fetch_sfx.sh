#!/usr/bin/env bash
# Download the sound effects used in scripts/sfx_cues.json from Mixkit (free license, see CREDITS.md).
# They are fetched rather than committed because the Mixkit license does not allow redistributing the files.
# Usage: scripts/fetch_sfx.sh <out_dir>
set -euo pipefail
out="${1:-sfx}"; mkdir -p "$out"
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"
for id in 216 273 701 704 772 788 950 957 1063 1092 1096 1105 1110 1111 1133 1365 1368 1430 1438 1441 1444 1457 1530 1998 1999 2069 2299 2301 2303 2354 2356 2357 2531 2533 2574 2582 2595 2617 2847 2870 2897 2900 2908 2951 2964 2997 3013 3102 3120; do
  [ -s "$out/$id.wav" ] && continue
  if ! curl -fsS -A "$UA" -o "$out/$id.wav" "https://assets.mixkit.co/active_storage/sfx/$id/$id.wav"; then
    # a few sounds only expose the preview MP3
    curl -fsS -A "$UA" -o "$out/$id.mp3" "https://assets.mixkit.co/active_storage/sfx/$id/$id-preview.mp3"
    ffmpeg -v error -y -i "$out/$id.mp3" "$out/$id.wav" && rm "$out/$id.mp3"
  fi
done
echo "fetched 49 sounds into $out"
