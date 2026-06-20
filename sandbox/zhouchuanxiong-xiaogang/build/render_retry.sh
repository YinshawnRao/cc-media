#!/usr/bin/env bash
# HyperFrames 本机 render 随机帧静默崩 → 重试循环。先 auto workers(快),崩了降 -w1(稳)。
# 校验产物时长 ≈ 计划(344.9s) 才算成功,防静默截断。
set -uo pipefail
cd /Users/yinshawnrao/explorer/cc-media/sandbox/zhouchuanxiong-xiaogang/hf
PLAN=414.9
for i in 1 2 3 4 5; do
  find . -maxdepth 2 -name 'work-*' -type d -exec rm -rf {} + 2>/dev/null
  if [ $i -le 2 ]; then W=auto; else W=1; fi
  echo "=== render attempt $i (workers=$W) ==="
  npx hyperframes render --output renders/full_raw.mp4 --sdr -w "$W" > "renders/render_$i.log" 2>&1
  D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 renders/full_raw.mp4 2>/dev/null || echo 0)
  OK=$(awk -v d="$D" -v p="$PLAN" 'BEGIN{print (d>=p-2 && d<=p+2)?1:0}')
  echo "attempt $i: duration=$D (plan $PLAN) ok=$OK"
  if [ "$OK" = "1" ]; then echo "RENDER_OK attempt $i"; break; fi
  echo "attempt $i failed tail:"; tail -4 "renders/render_$i.log"
done
echo "RENDER_DONE dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 renders/full_raw.mp4 2>/dev/null)"