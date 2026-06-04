#!/usr/bin/env bash
cd /Users/yinshawnrao/explorer/cc-media/sandbox/fws-no-jay
ROWS=("s3 217 53 1920:910:0:10" "s4 183 58 1600:1040:0:20" "s6 213 55 1920:1040:0:20" "s7 52 61 1280:780:0:10")
for row in "${ROWS[@]}"; do
  set -- $row; k=$1; ws=$2; wl=$3; crop=$4
  echo "===== vfill $k win=$ws+$wl crop=$crop ====="
  ffmpeg -nostdin -v error -i raw/${k}_full.mp4 -ss $ws -t $wl -c:v libx264 -preset veryfast -crf 19 -r 30 -g 30 -keyint_min 30 -c:a aac -b:a 192k raw/${k}_win.mp4 -y < /dev/null
  bash ../../tools/video/vfill.sh raw/${k}_win.mp4 clips/vert_${k}.mp4 "$crop" < /dev/null
done
echo "REST VFILL DONE"
