#!/usr/bin/env bash
# mux master.wav onto rendered video + QA. Run after full_raw.mp4 is rendered.
set -e
cd /Users/yinshawnrao/explorer/cc-media/sandbox/linzhixuan-hardest
ffmpeg -v error -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a \
  -c:v copy -c:a aac -b:a 192k -shortest renders/linzhixuan-hardest.mp4 -y
echo "=== final spec ==="
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height,pix_fmt -of default=noprint_wrappers=1 renders/linzhixuan-hardest.mp4 | head -12
echo "=== silence (>1s <-35dB) ==="
ffmpeg -v error -i renders/linzhixuan-hardest.mp4 -af silencedetect=n=-35dB:d=1 -f null - 2>&1 | grep silence_ || echo "  NONE (good)"
echo "=== per-song showcase loudness (mean) ==="
# showcase ends: 05~64 04~110 03~158 02~206 01~259
for kv in "05:54:64" "04:100:110" "03:148:158" "02:196:206" "01:247:259"; do
  no=${kv%%:*}; a=$(echo $kv|cut -d: -f2); b=$(echo $kv|cut -d: -f3); d=$((b-a))
  v=$(ffmpeg -hide_banner -ss $a -t $d -i renders/linzhixuan-hardest.mp4 -af volumedetect -f null - 2>&1 | grep mean_volume | grep -oE '[-0-9.]+ dB')
  echo "  #$no showcase ${a}-${b}s: $v"
done
echo "=== narration loudness (should be lower) ==="
for kv in "05n:24:38" "01n:214:228"; do
  no=${kv%%:*}; a=$(echo $kv|cut -d: -f2); b=$(echo $kv|cut -d: -f3); d=$((b-a))
  v=$(ffmpeg -hide_banner -ss $a -t $d -i renders/linzhixuan-hardest.mp4 -af volumedetect -f null - 2>&1 | grep mean_volume | grep -oE '[-0-9.]+ dB')
  echo "  $no ${a}-${b}s: $v"
done
