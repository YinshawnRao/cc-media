#!/usr/bin/env bash
# MUX 预混 master.wav 覆盖渲染产物音轨（HyperFrames 会压平音频动态 → 必须后期 mux）。
set -e
cd /Users/yinshawnrao/explorer/cc-media/sandbox/lizongsheng-underrated-top5
RAW="renders/full_raw.mp4"
OUT="renders/lizongsheng-underrated-top5.mp4"
[ -f "$RAW" ] || { echo "missing $RAW (render first)"; exit 1; }
ffmpeg -v error -i "$RAW" -i master.wav -map 0:v -map 1:a \
  -c:v copy -c:a aac -b:a 192k -shortest "$OUT" -y
echo "wrote $OUT"
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height -of default=noprint_wrappers=1 "$OUT"
