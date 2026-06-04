#!/bin/bash
# 本机 HF render flaky GPU 随机崩 → 单 worker + 重试循环直到出完整片。
# 用法: bash build/retry_render.sh <out.mp4> <target_dur_sec> [max_tries]
cd /Users/yinshawnrao/explorer/cc-media/sandbox/tanyonglin-underrated
OUT="$1"; TGT="$2"; MAX="${3:-8}"
mkdir -p renders
for i in $(seq 1 "$MAX"); do
  pkill -9 -f "Chrome.*headless" 2>/dev/null; pkill -9 -f "hyperframes" 2>/dev/null; sleep 1
  echo "=== attempt $i → $OUT ==="
  npx hyperframes render --output "$OUT" --sdr -w 1 > "renders/log_$(basename $OUT .mp4)_$i.log" 2>&1
  d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT" 2>/dev/null | cut -d. -f1)
  echo "  attempt $i: dur=${d:-none}s (target ~${TGT}s)"
  if [ -n "$d" ] && [ "$d" -ge "$((TGT-3))" ]; then echo "RENDER_OK $OUT $d"; exit 0; fi
  tail -3 "renders/log_$(basename $OUT .mp4)_$i.log"
done
echo "RENDER_FAILED after $MAX tries"; exit 1
