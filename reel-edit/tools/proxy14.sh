#!/bin/bash
# 4K HLG iPhone clips -> 1440x2560 SDR proxies (for the landscape 1440x1014 crop)
S=/tmp/claude-0/-home-user-velora-media/abd97aec-73af-531e-81b2-3a526db91b4e/scratchpad
F=$S/drive/footage; O=$S/work/proxy14
TM="zscale=w=1440:h=2560,zscale=tin=arib-std-b67:min=bt2020nc:pin=bt2020:rin=tv:t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=mobius:param=0.5:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p"
for b in IMG_4960 IMG_4962 IMG_4963 IMG_4964 IMG_4965 IMG_4966 IMG_4967 IMG_4968 IMG_4969 IMG_4972 IMG_4974 IMG_4976 IMG_4977 IMG_4978 IMG_4979 IMG_4980 IMG_4982 IMG_4985; do
  [ -s "$O/$b.mp4" ] && continue
  ffmpeg -v error -y -i "$F/$b.MOV" -vf "$TM" -an -c:v libx264 -preset veryfast -crf 16 -pix_fmt yuv420p "$O/$b.mp4" && echo "done $b"
done
echo ALL DONE
