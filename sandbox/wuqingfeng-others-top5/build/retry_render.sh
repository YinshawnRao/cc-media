#!/usr/bin/env bash
# 本机 HyperFrames GPU 截帧随机崩 → -w1 反复重试直到产物完整（按时长判）。
HF=/Users/yinshawnrao/explorer/cc-media/sandbox/wuqingfeng-others-top5/hf
OUT="$HF/renders/full_raw.mp4"
TARGET=236   # 目标 237.125s，>=236 视为完整
cd "$HF" || exit 1
for i in $(seq 1 10); do
  echo "===== render attempt $i ($(date +%H:%M:%S)) ====="
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
echo "RENDER_FAILED after 10 attempts"; exit 1
