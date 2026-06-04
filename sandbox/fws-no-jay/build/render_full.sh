#!/usr/bin/env bash
set -uo pipefail
cd /Users/yinshawnrao/explorer/cc-media/sandbox/fws-no-jay/hf
OUT=/Users/yinshawnrao/explorer/cc-media/sandbox/fws-no-jay/renders/full_raw.mp4
for i in 1 2 3 4 5 6; do
  echo "=== full render attempt $i $(date +%H:%M:%S) ==="
  rm -f "$OUT" 2>/dev/null
  npx --yes hyperframes@0.6.47 render --output "$OUT" --sdr -w1 2>&1 | tail -4
  if [ -f "$OUT" ]; then
    D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT" 2>/dev/null | cut -d. -f1)
    if [ -n "$D" ] && [ "$D" -ge 410 ] 2>/dev/null; then
      echo "=== FULL RENDER OK attempt $i dur=${D}s ==="; exit 0
    fi
    echo "attempt $i short (dur=$D), retry"
  else
    echo "attempt $i no output, retry"
  fi
  sleep 3
done
echo "=== ALL FULL RENDER ATTEMPTS FAILED ==="; exit 1
