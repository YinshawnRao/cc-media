#!/usr/bin/env bash
set -euo pipefail
cd /Users/yinshawnrao/explorer/cc-media/sandbox/zhoujielun-saddest-top5

SLUG=zhoujielun-saddest-top5
mkdir -p renders
python3 build/full_build.py
ZX_PART=A python3 build/full_build.py
ZX_PART=B python3 build/full_build.py

target_for() {
  python3 -c "import json;print(int(round(json.load(open('build/timeline.json'))['$1'])))"
}

render_one() {
  local comp="$1" out="$2" target="$3" i d log
  for i in $(seq 1 8); do
    pkill -9 -f "Chrome.*headless" 2>/dev/null || true
    pkill -9 -f "hyperframes" 2>/dev/null || true
    pkill -9 -f chrome_crashpad 2>/dev/null || true
    sleep 2
    log="renders/log_$(basename "$out" .mp4)_$i.log"
    rm -f "$out" 2>/dev/null || true
    echo "=== $comp attempt $i -> $out ==="
    npx --yes hyperframes@0.6.69 render -c "$comp" --output "$out" --sdr -w 1 > "$log" 2>&1 || true
    d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$out" 2>/dev/null | cut -d. -f1 || true)
    echo "  dur=${d:-none}s target~${target}s"
    if [ -n "${d:-}" ] && [ "$d" -ge "$((target-3))" ]; then
      return 0
    fi
    tr '\r' '\n' < "$log" | grep -oE "(Streaming|Capturing) frame [0-9]+/[0-9]+" | tail -1 || true
  done
  echo "FAIL $out"
  return 1
}

pa=$(target_for partA)
pb=$(target_for partB)
render_one segments/partA.html renders/partA.mp4 "$pa"
render_one segments/partB.html renders/partB.mp4 "$pb"

printf "file 'partA.mp4'\nfile 'partB.mp4'\n" > renders/concat_parts.txt
ffmpeg -v error -f concat -safe 0 -i renders/concat_parts.txt -c copy renders/full_raw.mp4 -y
ffmpeg -v error -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest "renders/${SLUG}.mp4" -y
ffprobe -v error -show_entries format=duration -of csv=p=0 "renders/${SLUG}.mp4"
