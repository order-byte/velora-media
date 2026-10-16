#!/usr/bin/env bash
# Download the music bed ("Daylight Robbery", Michael Ramir C., Mixkit id 1136, Mixkit Stock Music Free License).
# Fetched rather than committed because the Mixkit license does not allow redistributing the file.
# Usage: scripts/fetch_music.sh <out_dir>
set -euo pipefail
out="${1:-music}"; mkdir -p "$out"
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"
[ -s "$out/1136.mp3" ] || curl -fsS -A "$UA" -o "$out/1136.mp3" "https://assets.mixkit.co/music/1136/1136.mp3"
echo "music in $out"
