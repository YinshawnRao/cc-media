#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

RAW="hf/renders/full_raw.mp4"
OUT="renders/ashin-fish-leong-timeline.mp4"
MASTER="hf/master.wav"

mkdir -p hf/renders renders qa_frames

../../tools/tts/venv/bin/python build/full_build.py

cd hf
npx --yes hyperframes@0.6.47 lint
npx --yes hyperframes@0.6.47 validate
npx --yes hyperframes@0.6.47 inspect --samples 12
mkdir -p renders/parts
for html in parts_html/part_*.html; do
  base="$(basename "$html" .html)"
  npx --yes hyperframes@0.6.47 render --composition "$html" --output "renders/parts/${base}.mp4" --sdr --workers=2
done
for f in "$PWD"/renders/parts/part_*.mp4; do
  printf "file '%s'\n" "$f"
done > renders/parts/concat.txt
ffmpeg -v error -f concat -safe 0 -i renders/parts/concat.txt -c copy renders/full_raw.mp4 -y
cd ..

ffmpeg -v error -i "$RAW" -i "$MASTER" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest "$OUT" -y
ffmpeg -v error -ss 8 -i "$OUT" -frames:v 1 renders/cover.png -y

ffprobe -v error -select_streams v -show_entries stream=width,height,duration,avg_frame_rate -of default=noprint_wrappers=1 "$OUT"
ffprobe -v error -select_streams a -show_entries stream=channels,sample_rate,duration -of default=noprint_wrappers=1 "$OUT"

ffmpeg -hide_banner -i "$OUT" -af silencedetect=n=-35dB:d=1 -f null - 2>&1 | grep -E "silence_(start|end|duration)" || true
ffmpeg -hide_banner -i "$OUT" -af volumedetect -f null - 2>&1 | grep -E "(mean|max)_volume"

for item in \
  "0:cover" \
  "8:intro_title" \
  "45:rainbow_full" \
  "124:beautiful_full" \
  "195:cant_hear_full" \
  "267:swallowtail_full" \
  "343:innocence_full" \
  "421:silkroad_full" \
  "501:coke_ring_full" \
  "564:cta"; do
  t="${item%%:*}"
  name="${item##*:}"
  ffmpeg -v error -ss "$t" -i "$OUT" -frames:v 1 "qa_frames/${name}_t${t}.png" -y
done

echo "$OUT"
