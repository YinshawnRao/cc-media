#!/usr/bin/env bash
# 样片渲染（单 composition index.html，--sdr，崩则重试）→ mux 预混 master.wav。
PROJ=/Users/yinshawnrao/explorer/cc-media/sandbox/chenwei-elva
HF="$PROJ/hf"
cd "$HF" || exit 1
TARGET=$(python3 -c "import json;print(json.load(open('../timeline.json'))['TOTAL'])")
mkdir -p renders
ok=0
for i in 1 2 3 4 5; do
  pkill -9 -f "Google Chrome for Testing" 2>/dev/null
  pkill -9 -f hyperframes 2>/dev/null
  sleep 1
  rm -f renders/full_raw.mp4
  npx --yes hyperframes@0.6.69 render --output renders/full_raw.mp4 --sdr -w auto >/dev/null 2>&1
  d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 renders/full_raw.mp4 2>/dev/null || echo 0)
  ok=$(python3 -c "print(1 if abs(float('${d:-0}' or 0)-$TARGET)<1.5 else 0)" 2>/dev/null || echo 0)
  echo "attempt $i  dur=$d  target=$TARGET  ok=$ok"
  [ "$ok" = "1" ] && break
done
if [ "$ok" != "1" ]; then
  echo "=== auto-workers failed, trying -w1 ==="
  for i in 1 2 3; do
    pkill -9 -f "Google Chrome for Testing" 2>/dev/null; sleep 1; rm -f renders/full_raw.mp4
    npx --yes hyperframes@0.6.69 render --output renders/full_raw.mp4 --sdr -w 1 >/dev/null 2>&1
    d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 renders/full_raw.mp4 2>/dev/null || echo 0)
    ok=$(python3 -c "print(1 if abs(float('${d:-0}' or 0)-$TARGET)<1.5 else 0)" 2>/dev/null || echo 0)
    echo "w1 attempt $i  dur=$d  ok=$ok"; [ "$ok" = "1" ] && break
  done
fi
[ "$ok" != "1" ] && { echo "FATAL: render failed"; exit 1; }
echo "=== mux master.wav ==="
ffmpeg -v error -i renders/full_raw.mp4 -i "$PROJ/master.wav" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest "$PROJ/renders/chenwei-elva-sample.mp4" -y
echo "=== DONE ==="
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height,channels -of default=noprint_wrappers=1 "$PROJ/renders/chenwei-elva-sample.mp4"
echo "OUT: $PROJ/renders/chenwei-elva-sample.mp4"
