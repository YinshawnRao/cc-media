#!/usr/bin/env bash
# 彩蛋《听你·听我》蒙太奇：张雨生资料 + 阿妹录音棚 + 张雨生资料慢。纪念向，避开装饰空镜。
set -euo pipefail
ROOT=/Users/yinshawnrao/explorer/cc-media
P=$ROOT/sandbox/zys-amei-bole; VFILL=$ROOT/tools/video/vfill.sh
cd "$P"; mkdir -p clips tmp qa
cut(){ ffmpeg -v error -i "$1" -ss "$2" -t "$3" -c:v libx264 -preset veryfast -r 30 -c:a aac "$4" -y; }
cut raw/egg_yt.webm 66 12  tmp/e_zys.mp4    # 张雨生 资料画面
cut raw/egg_yt.webm 156 12 tmp/e_amei.mp4   # 阿妹 录音棚演唱
bash "$VFILL" tmp/e_zys.mp4  clips/ve_zys.mp4  "712:352:0:34" -0.36 1.02
bash "$VFILL" tmp/e_amei.mp4 clips/ve_amei.mp4 "712:372:0:8"  -0.34 1.04
reenc(){ ffmpeg -v error -i "$1" ${3:-} -an -c:v libx264 -preset veryfast -r 30 -g 30 -keyint_min 30 -pix_fmt yuv420p "$2" -y; }
reenc clips/ve_zys.mp4  clips/ve_zys_v.mp4
reenc clips/ve_amei.mp4 clips/ve_amei_v.mp4
reenc clips/ve_zys.mp4  clips/ve_zys_slow.mp4 "-filter:v setpts=1.667*PTS"
printf "file 've_zys_v.mp4'\nfile 've_amei_v.mp4'\nfile 've_zys_slow.mp4'\nfile 've_amei_v.mp4'\n" > clips/egglist.txt
ffmpeg -v error -f concat -safe 0 -i clips/egglist.txt -an -c:v libx264 -preset veryfast -r 30 -g 30 -keyint_min 30 -pix_fmt yuv420p clips/vert_egg.mp4 -y
echo -n "vert_egg dur: "; ffprobe -v error -show_entries format=duration -of csv=p=0 clips/vert_egg.mp4
ffmpeg -v error -i clips/vert_egg.mp4 -ss 4 -frames:v 1 qa/egg_zys.png -y
ffmpeg -v error -i clips/vert_egg.mp4 -ss 16 -frames:v 1 qa/egg_amei.png -y
echo "PREP EGG DONE"