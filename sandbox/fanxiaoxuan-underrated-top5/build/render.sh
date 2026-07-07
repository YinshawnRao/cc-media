#!/usr/bin/env bash
cd /Users/yinshawnrao/explorer/cc-media/sandbox/fanxiaoxuan-underrated-top5
export HYPERFRAMES_EXTRACT_CACHE_DIR=.extract_cache
for attempt in 1 2 3 4; do
  echo "=== render attempt $attempt ==="
  if npx --yes hyperframes@0.6.69 render --output renders/full_raw.mp4 --sdr -w 2 2>&1 | tail -4; then
    if [ -f renders/full_raw.mp4 ] && [ "$(ffprobe -v error -show_entries format=duration -of csv=p=0 renders/full_raw.mp4 2>/dev/null | cut -d. -f1)" -ge 290 ]; then
      echo "RENDER_OK dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 renders/full_raw.mp4)"
      exit 0
    fi
  fi
  echo "attempt $attempt incomplete, retrying..."; sleep 3
done
echo "RENDER_FAILED after retries"; exit 1
