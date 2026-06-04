#!/usr/bin/env bash
# render.sh <fps> <workers> <output_basename>
# 本机 GPU 截帧随机崩 → 重试循环 + 渲前清理 stale Chrome；--sdr 必加。
FPS=${1:-30}; W=${2:-auto}; OUT=${3:-full_raw}
HF=/Users/yinshawnrao/explorer/cc-media/sandbox/linxi-faye-fengshen/hf
cd "$HF" || exit 1
TARGET=98.2
for i in 1 2 3 4 5; do
  pkill -9 -f "Google Chrome for Testing" 2>/dev/null
  pkill -9 -f "hyperframes" 2>/dev/null
  sleep 1
  rm -f "renders/$OUT.mp4"
  echo "=== render attempt $i (fps=$FPS workers=$W) ==="
  npx --yes hyperframes@0.6.47 render --output "renders/$OUT.mp4" --sdr --fps "$FPS" -w "$W" 2>&1 | tail -4
  dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "renders/$OUT.mp4" 2>/dev/null || echo 0)
  ok=$(python3 -c "print(1 if abs(float('${dur:-0}' or 0)-$TARGET)<1.2 else 0)" 2>/dev/null || echo 0)
  echo "attempt $i -> dur=$dur ok=$ok"
  [ "$ok" = "1" ] && { echo "RENDER OK: renders/$OUT.mp4"; exit 0; }
done
echo "RENDER FAILED after retries"; exit 1
