#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
RAW="renders/full_raw.mp4"
FINAL="renders/eason-saddest-top5.mp4"
HF="/Users/yinshawnrao/.npm-cache/_npx/9034813775a58c19/node_modules/.bin/hyperframes"
mkdir -p renders
min_dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 master.wav | awk '{printf "%d", $1 - 2}')
ok=0
for attempt in 1 2 3 4 5; do
  echo "=== render attempt $attempt ==="
  rm -f "$RAW"
  "$HF" render --output "$RAW" --sdr
  if [ -f "$RAW" ]; then
    d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$RAW" 2>/dev/null | cut -d. -f1)
    if [ -n "$d" ] && [ "$d" -ge "$min_dur" ]; then
      echo "RENDER_OK attempt $attempt dur=$d"
      ok=1
      break
    fi
    echo "attempt $attempt short (dur=$d), retry"
  else
    echo "attempt $attempt no output, retry"
  fi
  sleep 3
done
if [ "$ok" != "1" ]; then
  echo "RENDER_FAILED"
  exit 1
fi
ffmpeg -v error -i "$RAW" -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest "$FINAL" -y
echo "MUXED -> $FINAL ($(ffprobe -v error -show_entries format=duration -of csv=p=0 "$FINAL")s)"
