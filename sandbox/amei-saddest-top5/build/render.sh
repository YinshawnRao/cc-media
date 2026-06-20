#!/usr/bin/env bash
# Render with retry (本机 GPU 截帧偶发静默崩 → 重试). --sdr 必加. mux 预混 master.wav.
cd "$(dirname "$0")/.."
RAW="renders/full_raw.mp4"
FINAL="renders/amei-saddest-top5.mp4"
mkdir -p renders
ok=0
for attempt in 1 2 3 4 5; do
  echo "=== render attempt $attempt ==="
  rm -f "$RAW"
  npx -y hyperframes@latest render --output "$RAW" --sdr 2>&1 | tail -15
  if [ -f "$RAW" ]; then
    d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$RAW" 2>/dev/null | cut -d. -f1)
    if [ -n "$d" ] && [ "$d" -ge 298 ]; then echo "RENDER_OK attempt $attempt dur=$d"; ok=1; break; fi
    echo "attempt $attempt short (dur=$d), retry"
  else
    echo "attempt $attempt no output, retry"
  fi
  sleep 3
done
if [ "$ok" != "1" ]; then echo "RENDER_FAILED"; exit 1; fi
# mux pre-mixed master.wav over rendered video (HF flattens audio dynamics)
ffmpeg -v error -i "$RAW" -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest "$FINAL" -y
echo "MUXED -> $FINAL ($(ffprobe -v error -show_entries format=duration -of csv=p=0 "$FINAL")s)"
