#!/usr/bin/env bash
# 竖屏化（letterbox 保原比例）+ 按 mseek 预切（coupled 口型同步）+ #2 蒙太奇 + intro/outro/cover。
# letterbox: 全宽 crop → fg scale 1080 宽居中 + 模糊 bg 填充。重编码 H.264 密集关键帧。
set -euo pipefail
cd "$(dirname "$0")/.."
RAW=raw; C=clips
mkdir -p "$C"

# mkvert <in> <ss> <dur> <crop=W:H:X:Y> <out> [eq=brightness:sat]
mkvert () {
  local IN="$1" SS="$2" DUR="$3" CROP="$4" OUT="$5" EQ="${6:-0:1.04}"
  local BR="${EQ%%:*}" SAT="${EQ##*:}"
  ffmpeg -v error -ss "$SS" -i "$IN" -t "$DUR" -filter_complex \
    "[0:v]crop=${CROP},eq=brightness=${BR}:saturation=${SAT},split=2[bg][fg];\
[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=28,eq=brightness=-0.34:saturation=1.02[bgb];\
[fg]scale=1080:-2[fgs];\
[bgb][fgs]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]" \
    -map "[v]" -an -c:v libx264 -preset veryfast -r 30 -g 30 -keyint_min 30 "$OUT" -y
  echo "  vert: $OUT ($(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")s)"
}

echo "== #5 爱你太真 (B站 coupled, crop 底烧词) =="
mkvert "$RAW/ainitaizhen_bili_BV1tE42157k6.mp4" 167.2 44 1440:565:0:0 "$C/vert_p5_aini.mp4"

echo "== #4 不下雨 (Universal coupled, crop 底烧词) =="
mkvert "$RAW/buxiayu_univ_vwFgOYv4cCA.webm" 33.98 49 640:368:0:8 "$C/vert_p4_buxiayu.mp4"

echo "== #3 手语 (VEVO coupled, 全宽干净) =="
mkvert "$RAW/shouyu_vevo_fnXqE3QPgmY.webm" 179.97 46 854:480:0:0 "$C/vert_p3_shouyu.mp4"

echo "== #1 情愿一个人 (冬季 decoupled footage, 全宽干净) =="
mkvert "$RAW/dongji_studio_7FmPOAvHS7Y.webm" 216 50 640:480:0:0 "$C/vert_p1_qingyuan.mp4" "0.02:1.04"

echo "== #2 第二道彩虹 (VEVO B&W 蒙太奇: 她干净段拼接) =="
# 她干净 B&W 段: 14-28(远/黑裙) 32-46(黑裙特写) 64-77(皮衣电话特写)。避开男演员(@48起)/戏服/工坊。
mkvert "$RAW/caihong_vevo_KBN0XByocJI.webm" 14 14 854:480:0:0 "$C/_m2a.mp4"
mkvert "$RAW/caihong_vevo_KBN0XByocJI.webm" 32 14 854:480:0:0 "$C/_m2b.mp4"
mkvert "$RAW/caihong_vevo_KBN0XByocJI.webm" 64 13 854:480:0:0 "$C/_m2c.mp4"
printf "file '_m2a.mp4'\nfile '_m2b.mp4'\nfile '_m2c.mp4'\n" > "$C/_m2list.txt"
ffmpeg -v error -f concat -safe 0 -i "$C/_m2list.txt" -c:v libx264 -preset veryfast -r 30 -g 30 -keyint_min 30 -an "$C/vert_p2_caihong.mp4" -y
echo "  vert: $C/vert_p2_caihong.mp4 ($(ffprobe -v error -show_entries format=duration -of csv=p=0 $C/vert_p2_caihong.mp4)s)"
rm -f "$C/_m2a.mp4" "$C/_m2b.mp4" "$C/_m2c.mp4" "$C/_m2list.txt"

echo "== intro 底片 (不下雨 金色, 多被封面遮) =="
mkvert "$RAW/buxiayu_univ_vwFgOYv4cCA.webm" 62 20 640:368:0:8 "$C/vert_intro.mp4"

echo "== outro 底片 (冬季 暖调反思) =="
mkvert "$RAW/dongji_studio_7FmPOAvHS7Y.webm" 38 34 640:480:0:0 "$C/vert_outro.mp4" "0.02:1.04"

echo "== cover_hero.png (不下雨 @70 金色特写, scale-cover 居中) =="
ffmpeg -v error -ss 70 -i "$RAW/buxiayu_univ_vwFgOYv4cCA.webm" -frames:v 1 \
  -vf "crop=640:368:0:8,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,eq=brightness=0.01:saturation=1.06" cover_hero.png -y
echo "  cover_hero.png done"
echo "ALL CLIPS DONE"