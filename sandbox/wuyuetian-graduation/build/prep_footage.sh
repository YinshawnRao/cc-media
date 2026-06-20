#!/usr/bin/env bash
set -uo pipefail
cd /Users/yinshawnrao/explorer/cc-media/sandbox/wuyuetian-graduation
VF=../../tools/video/vfill.sh
prep () {
  local key=$1 win=$2 len=$3 crop=$4 grade=$5 br=$6
  echo "=== $key: cut(win=$win len=$len) ==="
  ffmpeg -v error -i raw/${key}_full.mkv -ss $win -t $len -c:v libx264 -preset veryfast -crf 18 -g 30 -keyint_min 30 -c:a aac -b:a 192k raw/${key}_win.mp4 -y
  echo "=== $key: grade ==="
  ffmpeg -v error -i raw/${key}_win.mp4 -vf "$grade" -c:v libx264 -preset veryfast -crf 18 -c:a copy raw/${key}_graded.mp4 -y
  echo "=== $key: vfill ==="
  bash "$VF" raw/${key}_graded.mp4 clips/vert_${key}.mp4 "$crop" "$br" 1.0
}
prep sgj    97  64 "1440:890:0:0"  "eq=brightness=0.05:saturation=0.74:contrast=1.06,colorbalance=rm=0.12:rh=0.06:gm=0.02:bm=-0.14:bh=-0.06" -0.14
prep ganbei 272 71 "1920:945:0:0"  "eq=brightness=0.05:saturation=1.05:contrast=1.03,colorbalance=rm=0.07:gm=0.02:bm=-0.06" -0.20
prep hldwm  220 63 "1920:975:0:0"  "eq=brightness=-0.01:saturation=0.90:contrast=1.05,colorbalance=rm=-0.07:gm=-0.01:bm=0.13:bh=0.06" -0.22
prep zyjs   209 75 "1920:1080:0:0" "eq=brightness=0.09:saturation=1.08:contrast=1.03,colorbalance=rm=0.07:rh=0.04:gm=0.03:bm=-0.05" 0.0
echo "=== FOOTAGE PREP DONE ==="
for k in sgj ganbei hldwm zyjs; do printf "%-8s " $k; ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x clips/vert_${k}.mp4 2>/dev/null; ffprobe -v error -show_entries format=duration -of csv=p=0 clips/vert_${k}.mp4 2>/dev/null; done
