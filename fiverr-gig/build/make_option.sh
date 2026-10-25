#!/bin/bash
# make_option.sh ID : music edit -> -12 LUFS -> + v1 SFX -> -14 LUFS master -> 720p preview mux
set -e
W=/tmp/claude-0/-home-user-velora-media/4a14988d-28db-5a70-b10e-dd2bb40ffc21/scratchpad/work
A=/tmp/claude-0/-home-user-velora-media/4a14988d-28db-5a70-b10e-dd2bb40ffc21/scratchpad/audio
id=$1
I=$(ffmpeg -hide_banner -i $W/edits/$id.wav -af ebur128=framelog=quiet -f null - 2>&1 | grep -E "^\s+I:" | tail -1 | awk '{print $2}')
G=$(python3 -c "print(-12.0 - ($I))")
ffmpeg -v error -y -i $W/edits/$id.wav -af "volume=${G}dB" -c:a pcm_f32le $W/edits/${id}_n.wav
python3 -I $W/mix.py $A/v1.wav $W/edits/${id}_n.wav $W/cues.json $W/edits/${id}_mix.wav > /dev/null
J=$(ffmpeg -hide_banner -i $W/edits/${id}_mix.wav -af loudnorm=I=-14:TP=-1.0:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
set -- $(echo "$J" | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['input_i'],d['input_tp'],d['input_lra'],d['input_thresh'],d['target_offset'])")
ffmpeg -v error -y -i $W/edits/${id}_mix.wav -af "loudnorm=I=-14:TP=-1.0:LRA=11:measured_I=$1:measured_TP=$2:measured_LRA=$3:measured_thresh=$4:offset=$5:linear=true" -ar 48000 $W/edits/${id}_master.wav
ffmpeg -v error -y -i $W/reel_720_noaudio.mp4 -i $W/edits/${id}_master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 160k -shortest -movflags +faststart $W/edits/reel-$id-720p.mp4
echo "$id music_in=${I}LUFS gain=${G}dB done $(stat -c%s $W/edits/reel-$id-720p.mp4) bytes"
