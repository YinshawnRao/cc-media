#!/usr/bin/env bash
# 本机 HyperFrames GPU 截帧随机崩 → -w1 反复重试直到产物完整（按时长判）。--sdr 强制 H.264。
HF=/Users/yinshawnrao/explorer/cc-media/sandbox/linjunjie-variety-top5/hf
OUT="$HF/renders/full_raw.mp4"
TARGET=237   # 目标 238.6s，>=237 视为完整
cd "$HF" || exit 1
mkdir -p renders
for i in $(seq 1 14); do
  echo "===== render attempt $i ($(date +%H:%M:%S)) ====="
  pkill -9 -f "Chrome.*headless" 2>/dev/null; sleep 1
  rm -f "$OUT"
  npx --yes hyperframes@0.6.47 render --output renders/full_raw.mp4 --sdr -w 1 --quiet 2>&1 | tail -4
  if [ -f "$OUT" ]; then
    d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT" 2>/dev/null | cut -d. -f1)
    echo "attempt $i -> duration=${d:-NA}s"
    if [ "${d:-0}" -ge "$TARGET" ]; then echo "RENDER_OK $OUT ${d}s"; exit 0; fi
  else
    echo "attempt $i -> no output (crashed)"
  fi
done
echo "RENDER_FAILED after 14 attempts"; exit 1
