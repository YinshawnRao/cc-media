#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

ffmpeg -v error -i renders/full_raw.mp4 -i master.wav \
  -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest \
  renders/xietingfeng-underrated-top5.mp4 -y

echo "=== ffprobe final ==="
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height,channels \
  -of default=noprint_wrappers=0 renders/xietingfeng-underrated-top5.mp4

echo "=== silencedetect ==="
ffmpeg -v info -i renders/xietingfeng-underrated-top5.mp4 -af silencedetect=n=-35dB:d=1 -f null - 2>&1 | grep -i silence || echo "no >1s silence"

echo "=== volumedetect (whole) ==="
ffmpeg -i renders/xietingfeng-underrated-top5.mp4 -af volumedetect -f null - 2>&1 | grep -E "mean_volume|max_volume"

mkdir -p probe/qa
for t in 2 20 40 60 90 130 160 200 230 260 300 330 340; do
  ffmpeg -v error -ss "$t" -i renders/xietingfeng-underrated-top5.mp4 -frames:v 1 "probe/qa/f${t}.png" -y
done
echo "done"
