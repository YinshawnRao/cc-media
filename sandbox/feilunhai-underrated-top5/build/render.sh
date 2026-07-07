#!/usr/bin/env bash
set -euo pipefail
cd /Users/yinshawnrao/explorer/cc-media/sandbox/feilunhai-underrated-top5
SLUG=feilunhai-underrated-top5
mkdir -p renders
export HYPERFRAMES_EXTRACT_CACHE_DIR="$PWD/.hf_extract_cache"
mkdir -p "$HYPERFRAMES_EXTRACT_CACHE_DIR"

target=$(python3 -c "import json;print(int(round(json.load(open('build/timeline.json'))['total'])))")
out=renders/full_raw.mp4

for i in $(seq 1 8); do
  pkill -9 -f "Chrome.*headless" 2>/dev/null || true
  pkill -9 -f "hyperframes" 2>/dev/null || true
  pkill -9 -f chrome_crashpad 2>/dev/null || true
  sleep 2
  log="renders/log_full_$i.log"
  rm -f "$out" 2>/dev/null || true
  echo "=== render attempt $i -> $out (target ${target}s) ==="
  npx --yes hyperframes@0.6.69 render -c index.html --output "$out" --sdr -w 1 > "$log" 2>&1 || true
  d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$out" 2>/dev/null | cut -d. -f1 || true)
  echo "  dur=${d:-none}s target~${target}s"
  if [ -n "${d:-}" ] && [ "$d" -ge "$((target-3))" ]; then
    echo "  render OK"
    break
  fi
  tr '\r' '\n' < "$log" | grep -oE "(Streaming|Capturing) frame [0-9]+/[0-9]+" | tail -1 || true
done

# mux master audio over rendered video
ffmpeg -v error -i "$out" -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest "renders/${SLUG}.mp4" -y
echo "=== final: renders/${SLUG}.mp4 ==="
ffprobe -v error -show_entries format=duration -of csv=p=0 "renders/${SLUG}.mp4"
