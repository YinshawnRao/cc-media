#!/usr/bin/env bash
# 样片 v2 暖甜 clips：以隐形超人(solo, 无他人/无字幕)为主 + 给他 verified 特写。冷顾里改用静帧 ken-burns。
set -uo pipefail
cd /Users/yinshawnrao/explorer/cc-media/sandbox/guocaijie-sweet
R=raw; C=clips; mkdir -p "$C"
WARM='eq=brightness=0.085:saturation=1.22:contrast=1.05,colorbalance=rm=0.10:gm=-0.01:bm=-0.09:rs=0.05:rh=0.04:bh=-0.05'

vgrade() { # src ss dur crop out
  ffmpeg -v error -i "$1" -ss "$2" -t "$3" -filter_complex \
"[0:v]${4},${WARM},split=2[bg][fg];\
[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=26,eq=brightness=-0.17:saturation=1.0[bgb];\
[fg]scale=1080:-2[fgs];\
[bgb][fgs]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]" \
  -map "[v]" -an -c:v libx264 -preset veryfast -r 30 -g 30 -keyint_min 30 -pix_fmt yuv420p "$C/$5" -y
  echo "wrote $C/$5 ($(ffprobe -v error -show_entries stream=duration -of csv=p=0 "$C/$5"))"
}

# 隐形超人 (712x480, 裁底烧词 crop=712:400:0:0) — solo MV, 干净
vgrade "$R/yxcr_mv.webm"  66 10 "crop=712:400:0:0" "w_yx_a.mp4"       # 红格转身特写
vgrade "$R/yxcr_mv.webm" 100  8 "crop=712:400:0:0" "w_yx_b.mp4"       # 天真大眼特写(hero)
vgrade "$R/yxcr_mv.webm" 128 10 "crop=712:400:0:0" "w_yx_c.mp4"       # 收尾特写
vgrade "$R/yxcr_mv.webm"  50 10 "crop=712:400:0:0" "w_yx_garden.mp4"  # 花园发光爱心童话
# 给他 (1920x1080, 裁底烧词 crop=1920:900:0:0) — 取她的特写窗(避乐队/雕塑)
vgrade "$R/gei_ta_mv.mkv"  77  6 "crop=1920:900:0:0" "w_geita_a.mp4"  # 贝雷帽特写+书房
vgrade "$R/gei_ta_mv.mkv" 158  5 "crop=1920:900:0:0" "w_geita_b.mp4"  # 微笑举手粉调特写
echo "===== warm clips ====="; ls -la "$C"/w_*.mp4
