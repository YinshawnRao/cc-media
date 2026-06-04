#!/usr/bin/env bash
# mux 预混 master.wav 覆盖渲染产物音轨（HyperFrames 会压平动态）→ 成片
set -e
cd "$(dirname "$0")/.."
RAW=hf/renders/full_raw.mp4
OUT=renders/linxi-faye-fengshen-sample.mp4
mkdir -p renders
ffmpeg -v error -i "$RAW" -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest "$OUT" -y
echo "=== final ==="
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height,channels -of default=noprint_wrappers=1 "$OUT"
echo "OUT: $(cd "$(dirname "$0")/.." && pwd)/$OUT"
