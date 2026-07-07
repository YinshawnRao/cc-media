#!/usr/bin/env bash
cd "$(dirname "$0")/.."
export HYPERFRAMES_EXTRACT_CACHE_DIR="$(pwd)/.extract_cache"
OUT=renders/full_raw.mp4
for try in 1 2 3 4 5; do
  echo "=== render attempt $try ($(date +%H:%M:%S)) ==="
  rm -f "$OUT"
  if npx --yes hyperframes@0.6.69 render --output "$OUT" --sdr -w 2 2>&1 | tail -3; then
    if [ -f "$OUT" ] && [ "$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT" 2>/dev/null | cut -d. -f1)" -ge 268 ]; then
      echo "RENDER_OK dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")"
      exit 0
    fi
  fi
  echo "attempt $try failed/short, retrying..."
  sleep 3
done
echo "RENDER_FAILED after retries"; exit 1
