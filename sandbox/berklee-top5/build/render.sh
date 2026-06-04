#!/usr/bin/env bash
cd /Users/yinshawnrao/explorer/cc-media/sandbox/berklee-top5/hf
OUT=/Users/yinshawnrao/explorer/cc-media/sandbox/berklee-top5/renders/full_raw.mp4
ok=0
for i in 1 2 3 4 5; do
  echo "=== render attempt $i ==="
  npx hyperframes render --output "$OUT" --sdr 2>&1 | tail -6
  d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT" 2>/dev/null)
  echo "attempt $i duration=$d"
  if [ -n "$d" ] && awk "BEGIN{exit !($d>330)}"; then ok=1; echo "RENDER OK ($d s)"; break; fi
  echo "retry..."
done
[ "$ok" = 1 ] || { echo "RENDER FAILED after retries"; exit 1; }
# mux master.wav over rendered video
MASTER=/Users/yinshawnrao/explorer/cc-media/sandbox/berklee-top5/master.wav
FINAL=/Users/yinshawnrao/explorer/cc-media/sandbox/berklee-top5/renders/berklee-top5.mp4
ffmpeg -v error -i "$OUT" -i "$MASTER" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest "$FINAL" -y
echo "MUXED -> $FINAL"
ffprobe -v error -show_entries format=duration:stream=codec_type,codec_name,width,height -of default=nw=1 "$FINAL" | head
