#!/usr/bin/env bash
set -uo pipefail
cd /Users/yinshawnrao/explorer/cc-media/sandbox/yangnaiwen-underrated-top5
export HYPERFRAMES_EXTRACT_CACHE_DIR=.extract_cache
RAW=renders/full_raw.mp4
OUT=renders/yangnaiwen-underrated-top5.mp4
mkdir -p renders
# render with retry: try -w2 then -w1 (HF GPU screenshot can flake; single footage_track is light)
ok=0
for attempt in 1 2 3 4; do
  W=2; [ $attempt -ge 3 ] && W=1
  echo "=== render attempt $attempt (-w$W) ==="
  npx --yes hyperframes@0.6.69 render --output "$RAW" --sdr -w$W 2>&1 | tail -6
  if [ -f "$RAW" ] && [ "$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$RAW" 2>/dev/null | cut -d. -f1)" -ge 295 ] 2>/dev/null; then
    ok=1; echo "render OK ($(ffprobe -v error -show_entries format=duration -of csv=p=0 "$RAW")s)"; break
  fi
  echo "render incomplete, retrying..."; rm -f "$RAW"
done
[ $ok -eq 0 ] && { echo "RENDER FAILED after retries"; exit 1; }
# mux master.wav over rendered video
ffmpeg -v error -i "$RAW" -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest "$OUT" -y
echo "MUXED -> $OUT  ($(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")s, $(ffprobe -v error -select_streams v:0 -show_entries stream=width,height,codec_name -of csv=p=0:s=x "$OUT"))"
