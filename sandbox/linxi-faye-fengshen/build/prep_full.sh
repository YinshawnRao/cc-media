#!/usr/bin/env bash
# 全片素材预处理：9 首展示段 letterbox（原生 crop → 1080 宽，保原比例）。
# 《人间》(s10) 已在样片 prep_clips.sh 产出 clips_seg/renjian_show.mp4。
set -e
cd "$(dirname "$0")/.."
CS=hf_full/clips_seg
mkdir -p "$CS"
ENC=(-c:v libx264 -preset veryfast -r 30 -g 30 -keyint_min 30 -pix_fmt yuv420p -an)

lb () {  # <key> <cropspec>
  ffmpeg -v error -i "raw/$1_show.mp4" -vf "crop=$2,scale=1080:-2,setsar=1,format=yuv420p" "${ENC[@]}" "$CS/$1_show.mp4" -y
  echo "$1_show.mp4 -> $(ffprobe -v error -show_entries format=duration:stream=width,height -of csv=p=0 "$CS/$1_show.mp4" | tr '\n' ' ')"
}
lb hongdou 1440:900:0:0
lb yueding 640:285:0:0
lb anyong  1440:660:0:0
lb liunian 1406:980:256:100
lb youchai 1440:1080:0:0
lb qingshu 1920:970:0:0
lb bainian 1440:880:0:0
lb kaidao  1418:870:246:0
lb bianhua 1920:720:0:175
# 《人间》复用样片 letterbox 展示段
cp hf/clips_seg/renjian_show.mp4 "$CS/s10_show.mp4"
echo "s10_show.mp4 (人间, reuse) -> $(ffprobe -v error -show_entries format=duration:stream=width,height -of csv=p=0 "$CS/s10_show.mp4" | tr '\n' ' ')"
