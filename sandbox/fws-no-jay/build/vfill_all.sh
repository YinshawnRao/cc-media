#!/usr/bin/env bash
cd /Users/yinshawnrao/explorer/cc-media/sandbox/fws-no-jay
# key WSTART winlen crop
ROWS="
s2 197 57 800:395:0:30
s3 217 53 1920:910:0:10
s4 183 58 1600:1040:0:20
s5 136 57 1920:1040:0:20
s6 213 55 1920:1040:0:20
s7 52 61 1280:780:0:10
"
echo "$ROWS" | while read k ws wl crop; do
  [ -z "$k" ] && continue
  echo "===== vfill $k  win=$ws+$wl crop=$crop ====="
  ffmpeg -v error -i raw/${k}_full.mp4 -ss $ws -t $wl -c:v libx264 -preset veryfast -crf 19 -r 30 -g 30 -keyint_min 30 -c:a aac -b:a 192k raw/${k}_win.mp4 -y
  bash ../../tools/video/vfill.sh raw/${k}_win.mp4 clips/vert_${k}.mp4 "$crop"
done
echo "ALL VFILL DONE"
