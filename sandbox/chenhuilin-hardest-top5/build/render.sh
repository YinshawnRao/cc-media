#!/usr/bin/env bash
# 渲染（--sdr 必加）+ 重试循环（本机 GPU 截帧偶发静默崩 → 校验输出时长，不足则重试）。
set -uo pipefail
ROOT="/Users/yinshawnrao/explorer/cc-media/sandbox/chenhuilin-hardest-top5"
cd "$ROOT"
OUT="renders/full_raw.mp4"
TARGET=339   # master 340.1s，输出应 ≥339s
for attempt in 1 2 3 4 5; do
  echo "=== render attempt $attempt ==="
  rm -f "$OUT" 2>/dev/null
  npx hyperframes render --output "$OUT" --sdr 2>&1 | tail -3
  if [ -f "$OUT" ]; then
    d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT" 2>/dev/null | cut -d. -f1)
    echo "  output duration: ${d}s"
    if [ -n "$d" ] && [ "$d" -ge "$TARGET" ]; then
      echo "=== render OK (${d}s) ==="
      break
    fi
  fi
  echo "  incomplete, retrying..."
done
echo "=== render.sh done ==="
ffprobe -v error -show_entries format=duration:stream=width,height,codec_name -of default=nw=1 "$OUT" 2>/dev/null | head