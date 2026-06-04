#!/usr/bin/env bash
# 竖屏化(letterbox 保原比例) + 角标 delogo。绝对路径，后台安全。
set -uo pipefail
ROOT=/Users/yinshawnrao/explorer/cc-media
PROJ=$ROOT/sandbox/wangfeng-hardest
cd "$PROJ"
mkdir -p clips
VF="$ROOT/tools/video/vfill.sh"

# crop = 全宽横带(letterbox)，裁掉底部烧死歌词/顶部台标。源宽:裁后高:0:Y
echo "### 光明 1920x1080 鸟巢，裁底部歌词带"
bash "$VF" raw/guangming.mp4   clips/vert_guangming.mp4   "1920:890:0:0"
echo "### 等待 1920x1080 歌手2018，裁顶台标+底奖徽"
bash "$VF" raw/dengdai.webm    clips/vert_dengdai.mp4     "1920:550:0:155"
echo "### 存在 1280x720 官方MV，裁底歌词(右上红星稍后 delogo)"
bash "$VF" raw/cunzai.webm     clips/vert_cunzai.mp4      "1280:600:0:0"
echo "### 勇敢的心 1920x1080 蓝光，裁底歌词(右上QQ稍后 delogo)"
bash "$VF" raw/yonggan.mp4     clips/vert_yonggan.mp4     "1920:885:0:0"
echo "### 一起摇摆 3840x2160 4K，裁底卡拉OK词"
bash "$VF" raw/yiqiyaobai.mp4  clips/vert_yiqiyaobai.mp4  "3840:1820:0:0"

echo "=== VFILL DONE ==="
for s in guangming dengdai cunzai yonggan yiqiyaobai; do
  ffprobe -v error -show_entries stream=width,height -select_streams v:0 -of csv=p=0:s=x "clips/vert_$s.mp4" | sed "s|^|$s |"
done
