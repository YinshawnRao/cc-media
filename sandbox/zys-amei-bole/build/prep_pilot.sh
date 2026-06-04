#!/usr/bin/env bash
# 样片素材 v3：OUTPUT-side seek。s8 = ~59s 蒙太奇，师徒B&W为主 + 姊妹绿幕正脸 + 雨生资料。
set -euo pipefail
ROOT=/Users/yinshawnrao/explorer/cc-media
P=$ROOT/sandbox/zys-amei-bole
VFILL=$ROOT/tools/video/vfill.sh
cd "$P"
mkdir -p clips hf/clips_seg hf/cover_assets qa tmp
cut(){ ffmpeg -v error -i "$1" -ss "$2" -t "$3" -c:v libx264 -preset veryfast -r 30 -c:a aac "$4" -y; }

cut raw/s8_yt.webm 205 6   tmp/duo.mp4      # 录音棚师徒二人(B&W,干净;205-211不含橙色剧情尾)
cut raw/s6_yt.webm 154 7   tmp/jm.mp4       # 姊妹 绿幕 A-Mei 正脸近景
cut raw/egg_yt.webm 66 8   tmp/zys.mp4      # 张雨生 资料画面

bash "$VFILL" tmp/duo.mp4 clips/vduo.mp4 "712:400:0:40"   -0.40 1.02
bash "$VFILL" tmp/jm.mp4  clips/vjm.mp4  "1600:920:0:30"  -0.36 1.06
bash "$VFILL" tmp/zys.mp4 clips/vzys.mp4 "712:352:0:34"   -0.40 1.04

reenc(){ ffmpeg -v error -i "$1" ${3:-} -an -c:v libx264 -preset veryfast -r 30 -g 30 -keyint_min 30 -pix_fmt yuv420p "$2" -y; }
reenc clips/vduo.mp4 clips/vduo6.mp4 ""
reenc clips/vduo.mp4 clips/vduo_slow.mp4 "-filter:v setpts=1.667*PTS"
reenc clips/vjm.mp4  clips/vjm_v.mp4
reenc clips/vzys.mp4 clips/vzys_v.mp4

# 62s 蒙太奇(全干净)：duo→姊妹→雨生→duo慢→姊妹→雨生→duo→duo慢
printf "file 'vduo6.mp4'\nfile 'vjm_v.mp4'\nfile 'vzys_v.mp4'\nfile 'vduo_slow.mp4'\nfile 'vjm_v.mp4'\nfile 'vzys_v.mp4'\nfile 'vduo6.mp4'\nfile 'vduo_slow.mp4'\n" > clips/s8list.txt
ffmpeg -v error -f concat -safe 0 -i clips/s8list.txt -an -c:v libx264 -preset veryfast -r 30 -g 30 -keyint_min 30 -pix_fmt yuv420p clips/vert_s8.mp4 -y
cp clips/vert_s8.mp4 hf/clips_seg/s8.mp4

# 封面资产（output-side seek 精确取师徒镜）
ffmpeg -v error -i raw/s8_yt.webm -ss 208 -frames:v 1 tmp/duo_full.png -y
ffmpeg -v error -i raw/s6_yt.webm -ss 156 -frames:v 1 tmp/amei_full.png -y
ffmpeg -v error -i tmp/amei_full.png -vf "crop=660:760:560:120" hf/cover_assets/amei.jpg -y
ffmpeg -v error -i tmp/duo_full.png -vf "crop=300:420:36:40,eq=brightness=-0.04:saturation=0" hf/cover_assets/zys.jpg -y
ffmpeg -v error -i tmp/duo_full.png -vf "crop=712:400:0:40,eq=saturation=0" hf/cover_assets/studio.jpg -y

echo -n "vert_s8 dur: "; ffprobe -v error -show_entries format=duration -of csv=p=0 clips/vert_s8.mp4
ffmpeg -v error -i hf/clips_seg/s8.mp4 -ss 10 -frames:v 1 qa/v3_s8_10.png -y
ffmpeg -v error -i hf/clips_seg/s8.mp4 -ss 38 -frames:v 1 qa/v3_s8_38.png -y
echo "PREP v3 DONE"