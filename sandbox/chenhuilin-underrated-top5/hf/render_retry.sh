#!/usr/bin/env bash
# Local render retry loop for flaky browser/GPU captures.
cd "$(dirname "$0")"
OUT="${1:-renders/full_raw.mp4}"
MIN="${2:-280}"
mkdir -p renders
rm -f "$OUT" 2>/dev/null
for i in 1 2 3 4 5 6 7 8; do
  echo "=== render attempt $i ($OUT, min ${MIN}s) $(date +%H:%M:%S) ==="
  npx --yes hyperframes@0.6.47 render --output "$OUT" --sdr -w1 > "renders/log_$i.log" 2>&1
  if [ -f "$OUT" ] && [ "$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT" 2>/dev/null | cut -d. -f1)" -ge "$MIN" ] 2>/dev/null; then
    echo "=== SUCCESS attempt $i: $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")s $(date +%H:%M:%S) ==="
    exit 0
  fi
  echo "attempt $i incomplete; tail:"
  tail -6 "renders/log_$i.log"
  rm -f "$OUT" 2>/dev/null
done
echo "=== ALL ATTEMPTS FAILED ==="
exit 1
