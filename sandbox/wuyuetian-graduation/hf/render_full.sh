#!/usr/bin/env bash
cd "$(dirname "$0")"
OUT="renders/full_raw.mp4"
rm -f "$OUT" 2>/dev/null
for i in 1 2 3 4 5 6; do
  echo "=== render attempt $i ==="
  npx --yes hyperframes@0.6.47 render --output "$OUT" --sdr -w1 > "renders/full_$i.log" 2>&1
  if [ -f "$OUT" ] && [ "$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT" 2>/dev/null | cut -d. -f1)" -ge 330 ] 2>/dev/null; then
    echo "=== SUCCESS attempt $i: $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")s ==="; exit 0
  fi
  echo "attempt $i incomplete; tail:"; tail -5 "renders/full_$i.log"; rm -f "$OUT" 2>/dev/null
done
echo "=== ALL ATTEMPTS FAILED ==="; exit 1
