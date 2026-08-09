#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

FINAL="renders/saxophone-instrumental-top5.mp4"

ffmpeg -v error -i renders/full_raw.mp4 -i master.wav \
  -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest "$FINAL" -y

ffprobe -v error \
  -show_entries format=duration,size:stream=index,codec_name,width,height,r_frame_rate,pix_fmt,color_range,color_space,color_transfer,color_primaries,sample_rate,channels,channel_layout \
  -of json "$FINAL" > qa/final_ffprobe.json

ffmpeg -v error -i "$FINAL" -f null -
jq -e '.status == "OK" and ([.items[].status] | all(. == "OK"))' \
  probe/instrumental_plan.json > qa/instrumental_check.txt

ffmpeg -v info -i "$FINAL" -af silencedetect=n=-35dB:d=1 -f null - > qa/silencedetect.log 2>&1
ffmpeg -v info -i "$FINAL" -af volumedetect -f null - > qa/volumedetect.log 2>&1
ffmpeg -v info -i "$FINAL" -af ebur128=peak=true -f null - > qa/ebur128.log 2>&1
ffmpeg -v info -i "$FINAL" -vf "blackdetect=d=0.5:pix_th=0.10" -an -f null - > qa/blackdetect.log 2>&1

mkdir -p qa/final_frames-current qa/transition_frames-current
find qa/final_frames-current -type f -name '*.png' -delete
find qa/transition_frames-current -type f -name '*.png' -delete
TIMES="$(jq -r '[0.1, 2, .intro_end - 0.1] + ([.blocks[] | .narr_start + 0.5, .full_start + 2]) + [.outro_start + 1, .cta_start + 0.5, .duration - 0.6] | .[]' meta.json)"
index=0
for t in $TIMES; do
  ffmpeg -v error -ss "$t" -i "$FINAL" -frames:v 1 "qa/final_frames-current/frame_$(printf '%03d' "$index").png" -y
  index=$((index + 1))
done
ffmpeg -v error -framerate 1 -pattern_type glob -i 'qa/final_frames-current/frame_*.png' \
  -vf 'scale=270:-2,tile=4x4:padding=5:margin=5:color=0x111111' -frames:v 1 qa/final-contact-sheet.jpg -y

TRANSITIONS="$(jq -r '[(.blocks[1:][] | .start), .outro_start] | .[]' meta.json)"
index=0
for t in $TRANSITIONS; do
  for offset in -0.20 0.00 0.20; do
    at="$(awk -v a="$t" -v b="$offset" 'BEGIN { printf "%.3f", a+b }')"
    ffmpeg -v error -ss "$at" -i "$FINAL" -frames:v 1 "qa/transition_frames-current/frame_$(printf '%03d' "$index").png" -y
    index=$((index + 1))
  done
done
ffmpeg -v error -framerate 1 -pattern_type glob -i 'qa/transition_frames-current/frame_*.png' \
  -vf 'scale=270:-2,tile=3x5:padding=5:margin=5:color=0x111111' -frames:v 1 qa/transition-contact-sheet.jpg -y

../../tools/tts/venv/bin/python build/asr_qa.py final
echo "final: $FINAL"
