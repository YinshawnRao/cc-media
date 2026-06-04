#!/usr/bin/env bash
# 竖屏化 1080x1920。绝对路径，后台安全。
# 过火=竖屏满幅(delogo右上UP水印)；其余 letterbox 保原比例(裁角标/水印窄带)。
set -uo pipefail
ROOT=/Users/yinshawnrao/explorer/cc-media
PROJ=$ROOT/sandbox/zhangxinzhe-hardest
cd "$PROJ"
mkdir -p clips
VF="$ROOT/tools/video/vfill.sh"

echo "### 过火 1080x1920 沈阳直拍：delogo 右上 UP 水印，保满竖屏"
ffmpeg -v error -i raw/guohuo.mp4 \
  -vf "delogo=x=688:y=4:w=392:h=64,format=yuv420p" \
  -c:v libx264 -preset veryfast -r 30 -g 30 -keyint_min 30 -c:a aac -b:a 192k clips/vert_guohuo.mp4 -y
echo "  vert_guohuo: $(ffprobe -v error -show_entries stream=width,height -of csv=p=0:s=x clips/vert_guohuo.mp4 | head -1)"

echo "### 爱如潮水 1474x1080 演唱会：letterbox 全幅(干净)"
bash "$VF" raw/airuchaoshui.mp4 clips/vert_airuchaoshui.mp4 "1474:1080:0:0"

echo "### 太想爱你 1620x1080 蒲公英Live：letterbox 全幅(干净)"
bash "$VF" raw/taixiangaini.mp4 clips/vert_taixiangaini.mp4 "1620:1080:0:0"

echo "### 宽容 1440x1080 奥克兰：letterbox，裁底部 mike6liu 水印"
bash "$VF" raw/kuanrong.mp4 clips/vert_kuanrong.mp4 "1440:1005:0:0"

echo "### 信仰 1920x1080 CCTV央视频：居中4:3裁切(去顶logo/底字幕/右下赞助)，letterbox"
bash "$VF" raw/xinyang.mp4 clips/vert_xinyang.mp4 "1150:863:385:52"

echo "=== VFILL DONE ==="
for s in guohuo airuchaoshui taixiangaini kuanrong xinyang; do
  ffprobe -v error -show_entries stream=width,height -select_streams v:0 -of csv=p=0:s=x "clips/vert_$s.mp4" | sed "s|^|$s |"
done
