#!/usr/bin/env bash
# Mux pre-mixed master.wav over the HyperFrames render (HF flattens audio dynamics -> must post-mux).
set -e
cd /Users/yinshawnrao/explorer/cc-media/sandbox/guangliang-underrated-top5
RAW="renders/full_raw.mp4"
OUT="renders/guangliang-underrated-top5.mp4"
ffmpeg -v error -i "$RAW" -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest "$OUT" -y
echo "wrote $OUT"
ffprobe -v error -show_entries format=duration:stream=width,height,codec_name -of default=nw=1 "$OUT" | head -8
