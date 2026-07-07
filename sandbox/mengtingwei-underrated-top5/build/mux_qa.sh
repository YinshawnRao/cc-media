#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
RAW=renders/full_raw.mp4
OUT=renders/mengtingwei-underrated-top5.mp4
echo "== mux master.wav over rendered video =="
ffmpeg -v error -i "$RAW" -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest "$OUT" -y
echo "  final: $OUT  $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")s  $(ffprobe -v error -select_streams v:0 -show_entries stream=width,height,codec_name -of csv=p=0 "$OUT")"
echo "== silencedetect final =="
ffmpeg -v error -i "$OUT" -af "silencedetect=n=-35dB:d=1" -f null - 2>&1 | grep -i silence || echo "  无 >1s 静音"
