#!/usr/bin/env bash
set -euo pipefail
cd /Users/yinshawnrao/explorer/cc-media/sandbox/liuhuan-hardest-top5

SLUG=liuhuan-hardest-top5
PY=../../tools/tts/venv/bin/python
mkdir -p renders

$PY build/full_build.py
LH_PART=A $PY build/full_build.py
LH_PART=B $PY build/full_build.py

target_for() {
  $PY -c "import json;print(int(round(json.load(open('build/timeline.json'))['$1'])))"
}

render_one() {
  local comp="$1" out="$2" target="$3" log d
  log="renders/log_$(basename "$out" .mp4).log"
  npx --yes hyperframes@0.6.69 render -c "$comp" --output "$out" --sdr -w 1 > "$log" 2>&1
  d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$out" 2>/dev/null | cut -d. -f1 || true)
  echo "$out duration=${d:-none}s target~${target}s"
  test -n "${d:-}" && test "$d" -ge "$((target-3))"
}

pa=$(target_for partA)
pb=$(target_for partB)
render_one segments/partA.html renders/partA.mp4 "$pa"
render_one segments/partB.html renders/partB.mp4 "$pb"

printf "file 'partA.mp4'\nfile 'partB.mp4'\n" > renders/concat_parts.txt
ffmpeg -v error -f concat -safe 0 -i renders/concat_parts.txt -c copy renders/full_raw.mp4 -y
ffmpeg -v error -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest "renders/${SLUG}.mp4" -y
echo "FINAL $(ffprobe -v error -show_entries format=duration -of csv=p=0 "renders/${SLUG}.mp4")"
