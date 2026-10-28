#!/usr/bin/env bash
# Downloads the Noto fonts used by plan.html (SIL Open Font License) into ./fonts.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p fonts
base=https://raw.githubusercontent.com/google/fonts/main/ofl
fetch() { [ -f "fonts/$1" ] || curl -fsSL -o "fonts/$1" "$base/$2"; }
fetch NotoSerif.ttf        'notoserif/NotoSerif%5Bwdth,wght%5D.ttf'
fetch NotoSerif-Italic.ttf 'notoserif/NotoSerif-Italic%5Bwdth,wght%5D.ttf'
fetch NotoSans.ttf         'notosans/NotoSans%5Bwdth,wght%5D.ttf'
