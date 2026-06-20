#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO="$(cd "$ROOT/../.." && pwd)"
RAW="$ROOT/raw"
CUT="$ROOT/raw/cuts"
CLIPS="$ROOT/clips"
mkdir -p "$CUT" "$CLIPS"

cut_clip() {
  local src="$1"
  local start="$2"
  local dur="$3"
  local out="$4"
  ffmpeg -v error -i "$src" -ss "$start" -t "$dur" \
    -c:v libx264 -preset veryfast -r 30 -g 30 -keyint_min 30 \
    -c:a aac -b:a 192k -movflags +faststart "$out" -y
}

# Starts back-solve from the detected vocal entry so full-volume music begins on singing.
cut_clip "$RAW/chuan.mp4" 213.60 48.0 "$CUT/chuan_cut.mp4"
cut_clip "$RAW/nideshiwoderen_bili.mp4" 213.90 51.0 "$CUT/nideshiwoderen_cut.mp4"
cut_clip "$RAW/wanqianli.mp4" 110.10 51.0 "$CUT/wanqianli_cut.mp4"
cut_clip "$RAW/baisixian.mp4" 204.70 48.0 "$CUT/baisixian_cut.mp4"
cut_clip "$RAW/yuandu.mp4" 153.40 54.0 "$CUT/yuandu_cut.mp4"

bash "$REPO/tools/video/vfill.sh" "$CUT/chuan_cut.mp4" "$CLIPS/vert_chuan.mp4" "712:400:0:0" -0.24 1.06
bash "$REPO/tools/video/vfill.sh" "$CUT/nideshiwoderen_cut.mp4" "$CLIPS/vert_nideshiwoderen.mp4" "1080:900:0:0" -0.22 1.04
bash "$REPO/tools/video/vfill.sh" "$CUT/wanqianli_cut.mp4" "$CLIPS/vert_wanqianli.mp4" "712:392:0:0" -0.25 1.08
bash "$REPO/tools/video/vfill.sh" "$CUT/baisixian_cut.mp4" "$CLIPS/vert_baisixian.mp4" "712:340:0:0" -0.20 1.07
bash "$REPO/tools/video/vfill.sh" "$CUT/yuandu_cut.mp4" "$CLIPS/vert_yuandu.mp4" "712:400:0:0" -0.24 1.08
