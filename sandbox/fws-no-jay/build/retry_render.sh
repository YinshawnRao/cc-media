#!/usr/bin/env bash
set -uo pipefail
cd /Users/yinshawnrao/explorer/cc-media/sandbox/fws-no-jay/hf
OUT=/Users/yinshawnrao/explorer/cc-media/sandbox/fws-no-jay/renders/sample_raw.mp4
for i in 1 2 3 4 5; do
  echo "=== render attempt $i ==="
  rm -f "$OUT" 2>/dev/null
  npx --yes hyperframes@0.6.47 render --output "$OUT" --sdr -w1 2>&1 | tail -6
  if [ -f "$OUT" ] && [ "$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT" 2>/dev/null | cut -d. -f1)" -ge 70 ]; then
    echo "=== RENDER OK attempt $i ==="; ffprobe -v error -show_entries format=duration -show_entries stream=width,height,codec_name -of default=nw=1 "$OUT"; exit 0
  fi
  echo "attempt $i failed/short, retrying"; sleep 2
done
echo "=== ALL ATTEMPTS FAILED ==="; exit 1
