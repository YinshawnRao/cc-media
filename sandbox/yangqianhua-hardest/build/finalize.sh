#!/usr/bin/env bash
# mux 预混 master.wav 覆盖渲染产物音轨 + QA。在 full_raw.mp4 渲染完成后运行。
set -e
cd /Users/yinshawnrao/explorer/cc-media/sandbox/yangqianhua-hardest
ffmpeg -v error -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a \
  -c:v copy -c:a aac -b:a 192k -shortest renders/yangqianhua-hardest.mp4 -y
echo "=== final spec ==="
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height,pix_fmt -of default=noprint_wrappers=1 renders/yangqianhua-hardest.mp4 | head -12
echo "=== silence (>1s <-35dB) ==="
ffmpeg -v error -i renders/yangqianhua-hardest.mp4 -af silencedetect=n=-35dB:d=1 -f null - 2>&1 | grep silence_ || echo "  NONE (good)"
echo "=== per-song showcase loudness (mean) ==="
for kv in "05:46:62" "04:93:109" "03:139:155" "02:185:201" "01:234:254"; do
  no=${kv%%:*}; a=$(echo $kv|cut -d: -f2); b=$(echo $kv|cut -d: -f3); d=$((b-a))
  v=$(ffmpeg -hide_banner -ss $a -t $d -i renders/yangqianhua-hardest.mp4 -af volumedetect -f null - 2>&1 | grep mean_volume | grep -oE '[-0-9.]+ dB')
  echo "  #$no ${a}-${b}s: $v"
done