#!/usr/bin/env bash
cd /Users/yinshawnrao/explorer/cc-media/sandbox/xiaojingteng-underrated-top5
export HYPERFRAMES_EXTRACT_CACHE_DIR=.extract_cache
OUT=renders/full_raw.mp4
for i in $(seq 1 8); do
  echo "=== render attempt $i ($(date +%H:%M:%S)) ==="
  rm -rf renders/work-* 2>/dev/null
  npx --yes hyperframes@0.6.69 render --output "$OUT" --sdr -w1 2>&1 | tail -3
  if [ -f "$OUT" ]; then
    d=$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$OUT" 2>/dev/null)
    ok=$(python3 -c "print(1 if $d and float('${d:-0}')>300 else 0)" 2>/dev/null)
    if [ "$ok" = "1" ]; then echo "=== SUCCESS attempt $i, dur=$d ==="; break; fi
  fi
  echo "=== attempt $i failed (dur=${d:-none}), retrying ==="
  sleep 3
done
ls -la "$OUT" 2>/dev/null
