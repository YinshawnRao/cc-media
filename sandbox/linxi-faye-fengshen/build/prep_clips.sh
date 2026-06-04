#!/usr/bin/env bash
# 样片素材预处理 → hf/clips_seg/*.mp4 + hf/cover_assets/faye.jpg
# 主体王菲 letterbox（裁顶 660 去卡拉OK歌词、保原比例、1080 宽）；氛围素材 full-bleed cover。
set -e
cd "$(dirname "$0")/.."
R=raw; CS=hf/clips_seg
mkdir -p "$CS" hf/cover_assets
LB="crop=1920:660:0:0,scale=1080:-2,setsar=1,format=yuv420p"
COVER="scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,format=yuv420p"
ENC=(-c:v libx264 -preset veryfast -r 30 -g 30 -keyint_min 30 -pix_fmt yuv420p -an)

# 《人间》MV: renjian.mp4 local = MV-48 （本机渲染器 ≥7 个 video 会超时 → 控制在 4 个，故各 clip 加长覆盖时间轴）
ffmpeg -v error -i "$R/renjian.mp4" -ss 22 -t 34 -vf "$LB" "${ENC[@]}" "$CS/renjian_show.mp4" -y   # MV70-104 副歌展示
ffmpeg -v error -i "$R/renjian.mp4" -ss 72 -t 18 -vf "$LB" "${ENC[@]}" "$CS/renjian_img.mp4" -y     # MV120-138 人间烟火意象(干净·无制作署名)
ffmpeg -v error -i "$R/renjian.mp4" -ss  2 -t 20 -vf "$LB" "${ENC[@]}" "$CS/faye_open.mp4" -y         # MV50-70 开头王菲慢镜
# 氛围 full-bleed
ffmpeg -v error -i "$R/stock_city.mp4"            -ss 2 -t 26 -vf "$COVER" "${ENC[@]}" "$CS/city.mp4" -y
# 封面王菲冷感主图（黑底低头特写，避开底部卡拉OK）
ffmpeg -v error -i "$R/renjian.mp4" -ss 20 -frames:v 1 -vf "crop=600:660:372:20" hf/cover_assets/faye.jpg -y

echo "=== outputs ==="
for f in "$CS"/*.mp4; do
  echo "$f -> $(ffprobe -v error -show_entries format=duration:stream=width,height -of csv=p=0 "$f" | tr '\n' ' ')"
done
ls -la hf/cover_assets/faye.jpg
