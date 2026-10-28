#!/usr/bin/env bash
# Downloads the fonts used by video.html (SIL Open Font License) into ./fonts.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p fonts
base=https://raw.githubusercontent.com/google/fonts/main/ofl
fetch() { [ -f "fonts/$1" ] || curl -fsSL -o "fonts/$1" "$base/$2"; }
fetch Inter.ttf                'inter/Inter%5Bopsz,wght%5D.ttf'
fetch HindSiliguri-Medium.ttf  'hindsiliguri/HindSiliguri-Medium.ttf'
fetch HindSiliguri-SemiBold.ttf 'hindsiliguri/HindSiliguri-SemiBold.ttf'
