#!/usr/bin/env bash
# 样片竖屏化：letterbox 保原比例 + 冷/暖分级 + 裁水印/烧词带。输出 clips/*.mp4 (1080x1920, 30fps, 密集关键帧)。
set -uo pipefail
cd /Users/yinshawnrao/explorer/cc-media/sandbox/guocaijie-sweet
R=raw; C=clips; mkdir -p "$C"

COLD='eq=saturation=0.44:contrast=1.12:brightness=-0.02,colorbalance=rm=-0.04:gm=-0.02:bm=0.07:rs=-0.04:bs=0.06'
WARM='eq=brightness=0.085:saturation=1.22:contrast=1.05,colorbalance=rm=0.10:gm=-0.01:bm=-0.09:rs=0.05:rh=0.04:bh=-0.05'

vgrade() { # src ss dur crop grade bgsat out
  local src=$1 ss=$2 dur=$3 crop=$4 grade=$5 bgsat=$6 out=$7
  ffmpeg -v error -i "$src" -ss "$ss" -t "$dur" -filter_complex \
"[0:v]${crop},${grade},split=2[bg][fg];\
[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=26,eq=brightness=-0.17:saturation=${bgsat}[bgb];\
[fg]scale=1080:-2[fgs];\
[bgb][fgs]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]" \
  -map "[v]" -an -c:v libx264 -preset veryfast -r 30 -g 30 -keyint_min 30 -pix_fmt yuv420p "$C/$out" -y
  echo "wrote $C/$out ($(ffprobe -v error -show_entries stream=width,height,duration -of csv=p=0:s=x "$C/$out"))"
}

# 冷顾里 (film 1920x1080；裁掉左上4K徽标/左下CTA/底部双语字幕：crop=1680:920:240:0)
vgrade "$R/xsd1_film.mp4"  38  12 "crop=1680:920:240:0" "$COLD" 0.30 "cold_car.mp4"
vgrade "$R/xsd1_film.mp4" 124  16 "crop=1680:920:240:0" "$COLD" 0.30 "cold_walk.mp4"

# 暖甜 给他 (1920x1080；裁底部烧词：crop=1920:900:0:0)
vgrade "$R/gei_ta_mv.mkv"  70  14 "crop=1920:900:0:0" "$WARM" 1.0 "sweet_play1.mp4"
vgrade "$R/gei_ta_mv.mkv"  88  14 "crop=1920:900:0:0" "$WARM" 1.0 "sweet_close.mp4"
vgrade "$R/gei_ta_mv.mkv" 150  14 "crop=1920:900:0:0" "$WARM" 1.0 "sweet_play2.mp4"

# 暖甜 隐形超人 (712x480；裁底部烧词：crop=712:400:0:0)
vgrade "$R/yxcr_mv.webm"  104 14 "crop=712:400:0:0" "$WARM" 1.0 "sweet_yx_close.mp4"
vgrade "$R/yxcr_mv.webm"   50 14 "crop=712:400:0:0" "$WARM" 1.0 "sweet_yx_garden.mp4"

echo "===== all clips ====="
ls -la "$C"/*.mp4
