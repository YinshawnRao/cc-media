#!/usr/bin/env bash
cd /Users/yinshawnrao/explorer/cc-media/sandbox/fws-no-jay
D=qa_frames
ROWS=("s2 16 28 50" "s3 14 26 46" "s4 17 30 51" "s5 17 30 50" "s6 14 26 48" "s7 13 25 55")
for row in "${ROWS[@]}"; do
  set -- $row; k=$1
  ffmpeg -nostdin -v error -i clips/vert_${k}.mp4 -ss $2 -frames:v 1 -vf "scale=240:427" $D/q_${k}_a.png -y </dev/null
  ffmpeg -nostdin -v error -i clips/vert_${k}.mp4 -ss $3 -frames:v 1 -vf "scale=240:427" $D/q_${k}_b.png -y </dev/null
  ffmpeg -nostdin -v error -i clips/vert_${k}.mp4 -ss $4 -frames:v 1 -vf "scale=240:427" $D/q_${k}_c.png -y </dev/null
done
ffmpeg -v error -i $D/q_s2_a.png -i $D/q_s2_b.png -i $D/q_s2_c.png -i $D/q_s3_a.png -i $D/q_s3_b.png -i $D/q_s3_c.png -i $D/q_s4_a.png -i $D/q_s4_b.png -i $D/q_s4_c.png -filter_complex "hstack=9" $D/QA_234.png -y
ffmpeg -v error -i $D/q_s5_a.png -i $D/q_s5_b.png -i $D/q_s5_c.png -i $D/q_s6_a.png -i $D/q_s6_b.png -i $D/q_s6_c.png -i $D/q_s7_a.png -i $D/q_s7_b.png -i $D/q_s7_c.png -filter_complex "hstack=9" $D/QA_567.png -y
echo DONE
