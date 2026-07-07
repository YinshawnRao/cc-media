#!/usr/bin/env bash
# 单 worker 渲染（本机 -w2 易某 worker 静默 GPU 卡死且丢弃半成品 → -w1 最稳）。重试循环。
cd /Users/yinshawnrao/explorer/cc-media/sandbox/wubai-female-singers-top10
export HYPERFRAMES_EXTRACT_CACHE_DIR=/Users/yinshawnrao/explorer/cc-media/sandbox/wubai-female-singers-top10/renders/extract_cache
mkdir -p "$HYPERFRAMES_EXTRACT_CACHE_DIR" renders
MINDUR=${MINDUR:-482}
for i in $(seq 1 6); do
  rm -f renders/full_raw.mp4 2>/dev/null
  find renders -maxdepth 1 -name 'work-*' -exec rm -rf {} + 2>/dev/null
  echo "=== render attempt $i ($(date +%H:%M:%S)) -w1 ==="
  npx --yes hyperframes@0.6.69 render --output renders/full_raw.mp4 --sdr -w 1 2>&1 | tail -4
  d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 renders/full_raw.mp4 2>/dev/null | cut -d. -f1)
  echo "  -> output dur=${d:-none}s (need >=${MINDUR}, $(date +%H:%M:%S))"
  if [ -n "$d" ] && [ "$d" -ge "$MINDUR" ]; then echo "RENDER_OK attempt $i"; break; fi
  echo "  incomplete/crashed, retry"
done
echo "RENDER_LOOP_DONE"
