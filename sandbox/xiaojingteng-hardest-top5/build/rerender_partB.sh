#!/usr/bin/env bash
set -euo pipefail
cd /Users/yinshawnrao/explorer/cc-media/sandbox/xiaojingteng-hardest-top5
SLUG=xiaojingteng-hardest-top5
PY=../../tools/tts/venv/bin/python
ZX_PART=B $PY build/full_build.py
pb=$($PY -c "import json;print(int(round(json.load(open('build/timeline.json'))['partB'])))")
for i in $(seq 1 8); do
  pkill -9 -f "Chrome.*headless" 2>/dev/null || true
  pkill -9 -f "hyperframes" 2>/dev/null || true
  sleep 2
  rm -f renders/partB.mp4 2>/dev/null || true
  echo "=== partB attempt $i (target ${pb}s) ==="
  npx --yes hyperframes@0.6.69 render -c segments/partB.html --output renders/partB.mp4 --sdr -w 1 > renders/log_partB_re2_$i.log 2>&1 || true
  d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 renders/partB.mp4 2>/dev/null | cut -d. -f1 || true)
  echo "  dur=${d:-none}s"
  if [ -n "${d:-}" ] && [ "$d" -ge "$((pb-3))" ]; then break; fi
done
printf "file 'partA.mp4'\nfile 'partB.mp4'\n" > renders/concat_parts.txt
ffmpeg -v error -f concat -safe 0 -i renders/concat_parts.txt -c copy renders/full_raw.mp4 -y
ffmpeg -v error -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest "renders/${SLUG}.mp4" -y
echo "FINAL dur: $(ffprobe -v error -show_entries format=duration -of csv=p=0 "renders/${SLUG}.mp4")"
echo "RERENDER_B_DONE"
