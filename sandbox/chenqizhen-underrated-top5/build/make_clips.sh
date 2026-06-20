#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p clips raw/segments probes

VFILL="../../tools/video/vfill.sh"

make_one() {
  local key="$1"
  local start="$2"
  local crop="$3"
  local br="${4:--0.30}"
  local sat="${5:-1.04}"
  ffmpeg -v error -i "raw/${key}.mp4" -ss "$start" -t 64 \
    -c:v libx264 -preset veryfast -r 30 -g 30 -keyint_min 30 \
    -c:a aac -b:a 192k "raw/segments/${key}_seg.mp4" -y
  bash "$VFILL" "raw/segments/${key}_seg.mp4" "clips/vert_${key}.mp4" "$crop" "$br" "$sat"
}

# Starts align the full-volume music window with detected vocal segments.
# Crops remove official lyric bands where practical; yigui_live is a stable single-subject exception.
make_one "juli" "00:01:05" "1440:900:0:0" "-0.30" "1.04"
make_one "taicongming" "00:02:33" "640:400:0:0" "-0.30" "1.04"
make_one "yigui_live" "00:02:51.5" "760:960:580:0" "-0.25" "1.04"
mv clips/vert_yigui_live.mp4 clips/vert_yigui.mp4
make_one "wanmei80" "00:00:57" "1920:1080:0:0" "-0.26" "1.06"
make_one "fuxiu" "00:02:13" "1920:1080:0:0" "-0.30" "1.05"

for f in clips/vert_*.mp4; do
  echo "$f $(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$f")"
done
