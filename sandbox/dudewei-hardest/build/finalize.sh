#!/usr/bin/env bash
# Run after renders/full_raw.mp4 exists.
set -euo pipefail
cd /Users/yinshawnrao/explorer/cc-media/sandbox/dudewei-hardest

ffmpeg -v error -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a \
  -c:v copy -c:a aac -b:a 192k -shortest renders/dudewei-hardest.mp4 -y

echo "=== final spec ==="
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height,pix_fmt -of default=noprint_wrappers=1 renders/dudewei-hardest.mp4 | head -12

echo "=== silence (>1s <-35dB) ==="
ffmpeg -v error -i renders/dudewei-hardest.mp4 -af silencedetect=n=-35dB:d=1 -f null - 2>&1 | grep silence_ || echo "  NONE"

echo "=== showcase loudness ==="
for kv in "05:54:64" "04:100:110" "03:145:155" "02:193:203" "01:245:255"; do
  no=${kv%%:*}
  a=$(echo "$kv" | cut -d: -f2)
  b=$(echo "$kv" | cut -d: -f3)
  d=$((b-a))
  v=$(ffmpeg -hide_banner -ss "$a" -t "$d" -i renders/dudewei-hardest.mp4 -af volumedetect -f null - 2>&1 | grep mean_volume | grep -oE '[-0-9.]+ dB')
  echo "  #$no ${a}-${b}s: $v"
done
