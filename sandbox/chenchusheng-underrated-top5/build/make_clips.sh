#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

cut_raw() {
  local in="$1"
  local start="$2"
  local dur="$3"
  local out="$4"
  ffmpeg -v error -ss "$start" -i "$in" -t "$dur" \
    -c:v libx264 -preset veryfast -r 30 -g 30 -keyint_min 30 \
    -c:a aac -b:a 192k -movflags +faststart "$out" -y
}

# Segment starts are chosen so each section's full-music window lands inside a continuous sung passage
# after the narration and breathing beat.
cut_raw raw/xianzheyangba_bili_minilive.mp4 105 74 raw/cut_p5_xianzhe.mp4
cut_raw raw/bianzhengguanxi_bili_musicguan.mp4 128 74 raw/cut_p4_bianzheng.mp4
cut_raw raw/35_yt_official.mp4 45 74 raw/cut_p3_sanshiwu.mp4
cut_raw raw/zhuifengzheng_bili_live.mp4 150 76 raw/cut_p2_zhuifeng.mp4
cut_raw raw/yigeren_bili_official.mp4 70 78 raw/cut_p1_yigeren.mp4

bash ../../tools/video/vfill.sh raw/cut_p5_xianzhe.mp4 clips/vert_p5_xianzhe.mp4 1280:560:0:60 -0.30 1.08
bash ../../tools/video/vfill.sh raw/cut_p4_bianzheng.mp4 clips/vert_p4_bianzheng.mp4 1440:520:0:40 -0.28 1.06
bash ../../tools/video/vfill.sh raw/cut_p3_sanshiwu.mp4 clips/vert_p3_sanshiwu.mp4 1920:880:0:0 -0.34 1.04
bash ../../tools/video/vfill.sh raw/cut_p2_zhuifeng.mp4 clips/vert_p2_zhuifeng.mp4 852:330:0:45 -0.26 1.08
bash ../../tools/video/vfill.sh raw/cut_p1_yigeren.mp4 clips/vert_p1_yigeren.mp4 1276:600:0:0 -0.28 1.06
