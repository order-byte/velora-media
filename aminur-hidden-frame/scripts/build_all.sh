#!/usr/bin/env bash
# Rebuild the reel from the raw take. Needs ffmpeg (with zscale), python3 (numpy, scipy, onnxruntime), node 18+ and ImageMagick.
#   scripts/build_all.sh raw/raw.mp4
# Set REMOTION_BROWSER to a Chromium/headless_shell binary if Remotion can't download its own.
set -euo pipefail
RAW="${1:-raw/raw.mp4}"
mkdir -p work out public/media sfx music

# 1. cut the selects from the EDL: HLG->SDR tone-map + soft aesthetic grade + cleaned voice
python3 scripts/build_selects.py "$RAW" scripts/edl.json work

# 2. person matte (Robust Video Matting) -> alpha cut-out layer for text-behind-person shots
[ -s work/rvm_mobilenetv3_fp32.onnx ] || curl -fsSL -o work/rvm_mobilenetv3_fp32.onnx \
  https://github.com/PeterL1n/RobustVideoMatting/releases/download/v1.0.0/rvm_mobilenetv3_fp32.onnx
python3 scripts/matte_rvm.py work/selects.mp4 work/rvm_mobilenetv3_fp32.onnx work/matte.mp4
ffmpeg -v error -y -i work/selects.mp4 -i work/matte.mp4 \
  -filter_complex "[1:v]format=gray,lutyuv=y='clip((val-16)*1.08,0,255)'[m];[0:v][m]alphamerge,format=yuva420p" \
  -c:v libvpx-vp9 -pix_fmt yuva420p -b:v 6M -deadline good -cpu-used 4 -row-mt 1 -auto-alt-ref 0 public/media/person.webm
cp work/selects.mp4 public/media/selects.mp4
ffmpeg -v error -y -i work/selects.mp4 -vf "fps=48/37.33,scale=216:384,tile=8x6" -frames:v 1 -q:v 3 public/media/thumbs.jpg

# 3. picture (Remotion)
npx remotion render src/index.ts Reel out/picture.mp4 --codec=h264 --crf=16 --muted \
  ${REMOTION_BROWSER:+--browser-executable="$REMOTION_BROWSER"}

# 4. sound: fetch SFX + music, measure the SFX, mix voice + SFX + music bed
scripts/fetch_sfx.sh sfx
scripts/fetch_music.sh music
python3 scripts/sfx_info.py sfx work/sfx_info.json
python3 scripts/mix_audio.py work/voice.wav scripts/sfx_cues.json sfx work/sfx_info.json 38.9333 work/mix.wav music

# 5. master + captions + cover
scripts/finish.sh out/picture.mp4 work/mix.wav out/aminur_hidden_frame.mp4
python3 scripts/make_srt.py src/data.ts out/aminur_hidden_frame.srt
npx remotion still src/index.ts Reel out/cover.jpg --frame=50 --image-format=jpeg \
  ${REMOTION_BROWSER:+--browser-executable="$REMOTION_BROWSER"}
echo "done: out/aminur_hidden_frame.mp4"
