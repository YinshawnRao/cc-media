#!/usr/bin/env bash
cd /Users/yinshawnrao/explorer/cc-media/sandbox/fws-no-jay
D=qa_frames
for k in s2 s3 s4 s5 s6 s7; do
  F=raw/${k}_full.mp4
  DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$F" | cut -d. -f1)
  step=$((DUR/13))
  ts=""; for n in $(seq 1 12); do ts="$ts $((step*n))"; done
  echo "===== $k dur=${DUR}s | frames@:$ts ====="
  out=""
  for t in $ts; do
    m=$(ffmpeg -ss $t -t 8 -i "$F" -af volumedetect -f null - 2>&1 | awk -F'mean_volume:' '/mean_volume/{gsub(/ /,"",$2);print $2}' | tail -1)
    out="$out ${t}=${m}"
  done
  echo "RMS:$out"
  i=0; for t in $ts; do ffmpeg -v error -i "$F" -ss $t -frames:v 1 -vf "scale=320:180,pad=320:200:0:10:black" $D/cs_${k}_$(printf %02d $i).png -y; i=$((i+1)); done
  ffmpeg -v error \
    -i $D/cs_${k}_00.png -i $D/cs_${k}_01.png -i $D/cs_${k}_02.png -i $D/cs_${k}_03.png \
    -i $D/cs_${k}_04.png -i $D/cs_${k}_05.png -i $D/cs_${k}_06.png -i $D/cs_${k}_07.png \
    -i $D/cs_${k}_08.png -i $D/cs_${k}_09.png -i $D/cs_${k}_10.png -i $D/cs_${k}_11.png \
    -filter_complex "[0][1][2][3]hstack=4[a];[4][5][6][7]hstack=4[b];[8][9][10][11]hstack=4[c];[a][b][c]vstack=3" $D/overview_${k}.png -y
done
echo "DONE"
