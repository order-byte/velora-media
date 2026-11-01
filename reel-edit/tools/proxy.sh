#!/bin/bash
# HDR (HLG) iPhone clips -> 1080x1920 SDR H.264 proxies at native fps
S=/tmp/claude-0/-home-user-velora-media/abd97aec-73af-531e-81b2-3a526db91b4e/scratchpad
F=$S/drive/footage; O=$S/work/proxy
TM="zscale=w=1080:h=1920,zscale=tin=arib-std-b67:min=bt2020nc:pin=bt2020:rin=tv:t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=mobius:param=0.5:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p"
for f in $F/IMG_*.MOV; do
  b=$(basename "$f" .MOV)
  [ "$b" = "IMG_4985_2" ] && continue
  [ -s "$O/$b.mp4" ] && continue
  ffmpeg -v error -y -i "$f" -vf "$TM" -c:v libx264 -preset veryfast -crf 17 -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709 -c:a aac -b:a 192k -movflags +faststart "$O/$b.mp4" && echo "done $b"
done
echo ALL PROXIES DONE
