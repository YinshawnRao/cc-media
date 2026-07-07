#!/usr/bin/env bash
# 单条 footage_track + 重试循环（本机随机 protocolTimeout/GPU 崩→重试；前2次-w2，之后-w1更稳）。
cd /Users/yinshawnrao/explorer/cc-media/sandbox/wubai-female-singers-top10
export HYPERFRAMES_EXTRACT_CACHE_DIR=/Users/yinshawnrao/explorer/cc-media/sandbox/wubai-female-singers-top10/renders/extract_cache
mkdir -p "$HYPERFRAMES_EXTRACT_CACHE_DIR" renders
MINDUR=${MINDUR:-540}
find renders -maxdepth 1 -name 'work-*' -exec rm -rf {} + 2>/dev/null
for i in $(seq 1 10); do
  rm -f renders/full_raw.mp4 2>/dev/null
  W=2; [ "$i" -ge 3 ] && W=1
  echo "=== render attempt $i ($(date +%H:%M:%S)) -w$W ==="
  npx --yes hyperframes@0.6.69 render --output renders/full_raw.mp4 --sdr -w $W 2>&1 | tail -4
  d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 renders/full_raw.mp4 2>/dev/null | cut -d. -f1)
  echo "  -> output dur=${d:-none}s (need >=${MINDUR}, $(date +%H:%M:%S))"
  if [ -n "$d" ] && [ "$d" -ge "$MINDUR" ]; then echo "RENDER_OK attempt $i"; break; fi
  echo "  incomplete/crashed, retry"
done
echo "RENDER_LOOP_DONE"
