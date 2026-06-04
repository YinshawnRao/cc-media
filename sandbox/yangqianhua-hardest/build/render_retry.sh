#!/usr/bin/env bash
cd /Users/yinshawnrao/explorer/cc-media/sandbox/yangqianhua-hardest
OUT=renders/full_raw.mp4
for try in 1 2 3 4 5; do
  echo "=== render attempt $try ($(date +%H:%M:%S)) ==="
  rm -f "$OUT"
  npx hyperframes render --output "$OUT" --sdr -w1 2>&1 | tail -4
  if [ -f "$OUT" ]; then
    d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT" 2>/dev/null | cut -d. -f1)
    echo "  output dur=${d}s"
    if [ -n "$d" ] && [ "$d" -ge 270 ]; then echo "RENDER OK ($d s)"; exit 0; fi
  fi
  echo "  incomplete, retrying..."
done
echo "RENDER FAILED after retries"; exit 1
