#!/bin/bash
# make_gig2.sh MUSIC_EDIT.wav OUT_PREFIX : -12 LUFS music + v1 SFX (cues2.json) -> -14 LUFS / -2 dBTP master
#   -> OUT_PREFIX-1080p.mp4 (Fiverr) and OUT_PREFIX-720p.mp4 (board preview)
set -e
W=/tmp/claude-0/-home-user-velora-media/4a14988d-28db-5a70-b10e-dd2bb40ffc21/scratchpad/work
A=/tmp/claude-0/-home-user-velora-media/4a14988d-28db-5a70-b10e-dd2bb40ffc21/scratchpad/audio
M=$1; P=$2
I=$(ffmpeg -hide_banner -i $M -af ebur128=framelog=quiet -f null - 2>&1 | grep -E "^\s+I:" | tail -1 | awk '{print $2}')
G=$(python3 -c "print(-12.0 - ($I))")
ffmpeg -v error -y -i $M -af "volume=${G}dB" -c:a pcm_f32le ${P}_n.wav
SFX_GAIN=${SFX_GAIN:-1.1} python3 -I $W/mix.py ${SFX_SRC:-$A/v1.wav} ${P}_n.wav $W/cues2.json ${P}_mix.wav > /dev/null
J=$(ffmpeg -hide_banner -i ${P}_mix.wav -af loudnorm=I=-14:TP=-2.0:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
set -- $(echo "$J" | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['input_i'],d['input_tp'],d['input_lra'],d['input_thresh'],d['target_offset'])")
ffmpeg -v error -y -i ${P}_mix.wav -af "loudnorm=I=-14:TP=-2.0:LRA=11:measured_I=$1:measured_TP=$2:measured_LRA=$3:measured_thresh=$4:offset=$5:linear=true,afade=t=in:d=0.03:curve=qsin" -ar 48000 -c:a pcm_s16le ${P}_master.wav
ffmpeg -v error -y -i $W/reel2_video.mp4 -i ${P}_master.wav -map 0:v -map 1:a -c:v libx264 -preset slow -crf 16 -maxrate 10000k -bufsize 20000k -profile:v high -pix_fmt yuv420p -r 30 -c:a aac -b:a 256k -ar 48000 -movflags +faststart -shortest ${P}-1080p.mp4
ffmpeg -v error -y -i ${P}-1080p.mp4 -vf scale=1280:720:flags=lanczos -c:v libx264 -preset slow -b:v 1800k -maxrate 2300k -bufsize 4600k -pix_fmt yuv420p -c:a aac -b:a 160k -movflags +faststart ${P}-720p.mp4
for f in ${P}-1080p.mp4 ${P}-720p.mp4; do echo "$f $(stat -c%s $f) B $(ffprobe -v error -show_entries format=duration -of csv=p=0 $f)s $(ffmpeg -hide_banner -i $f -map 0:a -af ebur128=framelog=quiet:peak=true -f null - 2>&1 | grep -E 'I:|Peak:' | tr -s ' ' | tr '\n' ' ')"; done
