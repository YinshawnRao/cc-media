#!/usr/bin/env bash
set -euo pipefail

# Cut the selected sung windows, then convert to 1080x1920 with blurred fill.
# Window rule: target vocal onset lands about 2s before the narration finishes.

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO="$(cd "$ROOT/../.." && pwd)"

cut_src() {
  local key="$1"
  local start="$2"
  local dur="$3"
  local crop="$4"

  local src="$ROOT/raw/src_${key}.mp4"
  local seg="$ROOT/raw/seg_${key}.mp4"
  local out="$ROOT/clips/vert_${key}.mp4"

  echo "==> $key start=$start dur=$dur crop=$crop"
  ffmpeg -v error -y -i "$src" -ss "$start" -t "$dur" \
    -c:v libx264 -preset veryfast -r 30 -g 30 -keyint_min 30 \
    -c:a aac -b:a 192k "$seg"
  bash "$REPO/tools/video/vfill.sh" "$seg" "$out" "$crop"
}

cut_src "gaomei"    "129.00" "55.65" "640:360:0:0"
cut_src "feihua"    "107.55" "56.60" "1920:650:0:0"
cut_src "yueban"    "190.25" "55.70" "640:480:0:0"
cut_src "dahuitang" "192.40" "56.15" "640:480:0:0"
cut_src "buhui"     "105.05" "57.33" "640:270:0:50"
