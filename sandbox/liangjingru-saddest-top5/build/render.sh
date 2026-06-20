#!/usr/bin/env bash
cd "$(dirname "$0")/.."
OUT="renders/full_raw.mp4"
for attempt in 1 2 3 4 5; do
  echo "=== render attempt $attempt ==="
  rm -f "$OUT"
  if npx -y hyperframes@latest render --output "$OUT" --sdr 2>&1 | tail -25; then
    if [ -f "$OUT" ] && [ "$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT" 2>/dev/null | cut -d. -f1)" -ge 290 ]; then
      echo "RENDER_OK attempt $attempt dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")"
      exit 0
    fi
  fi
  echo "attempt $attempt failed/short, retrying..."
  sleep 3
done
echo "RENDER_FAILED after retries"
exit 1
