#!/usr/bin/env bash
# 周杰伦毕业季 footage prep: cut window (output-seek, accurate) -> grade(color arc) -> vfill letterbox.
# 色温弧: 暖白晴空(释然) -> 暖金sepia(回望) -> 暮色暖橙(告别) -> 冷蓝夜(怅惘) -> 金亮乡间(出发)
# crop 全宽横带去烧词/水印, 一律 letterbox 保原比例(不竖裁放大)。
set -uo pipefail
cd /Users/yinshawnrao/explorer/cc-media/sandbox/zhoujielun-graduation
VF=../../tools/video/vfill.sh

prep () {
  local key=$1 src=$2 win=$3 len=$4 crop=$5 grade=$6 br=$7
  echo "=== $key: cut+grade (win=$win len=$len) ==="
  ffmpeg -v error -i "$src" -ss "$win" -t "$len" -vf "$grade" \
    -c:v libx264 -preset veryfast -crf 18 -g 30 -keyint_min 30 -c:a aac -b:a 192k raw/${key}_pre.mp4 -y
  echo "=== $key: vfill letterbox ==="
  bash "$VF" raw/${key}_pre.mp4 clips/vert_${key}.mp4 "$crop" "$br" 1.0
}

# 1 晴天 (释然/暖白晴空) — B站4K修复1440x1080(4:3), 底部繁体歌词裁掉, swell落周杰伦仰头特写(源~180)
prep qingtian  raw/qingtian_4k.mp4  6   59.5 "1440:920:0:0" \
  "eq=brightness=0.04:saturation=1.05:contrast=1.03,colorbalance=rm=0.05:rh=0.03:gm=0.01:bm=-0.05:bh=-0.03" -0.12
# 2 蒲公英的约定 (回望/暖金sepia) — 官方MV(演唱会版,透明钢琴)480p, 底部歌词裁掉, 重去色+暖调做怀旧
prep pugongying raw/pugongying_yt.webm 90 57.5 "640:412:0:0" \
  "eq=brightness=0.03:saturation=0.70:contrast=1.05,colorbalance=rm=0.12:rh=0.06:gm=0.02:bm=-0.14:bh=-0.08" -0.18
# 3 轨迹 (告别/暮色暖橙) — 2004无与伦比4K Live(1920x1080,本人弹唱特写干净), 暖化暮色melancholy
prep guiji     raw/guiji_live.mp4   4   61.5 "1920:1080:0:0" \
  "eq=brightness=0.0:saturation=0.84:contrast=1.05,colorbalance=rm=0.09:rh=0.05:gm=0.01:bm=-0.07:bh=-0.04" -0.20
# 4 最长的电影 (怅惘/冷蓝夜) — 2007世巡Live 720p, 顶部FanClub+土豆水印裁掉(crop顶85), 冷蓝夜调
prep zuichang  raw/zuichang_live_yt.webm 114 59.5 "1280:600:0:115" \
  "eq=brightness=-0.02:saturation=0.82:contrast=1.05,colorbalance=rs=-0.05:rm=-0.06:gm=0.0:bm=0.12:bh=0.10:bs=0.06" -0.24
# 5 稻香 (出发/金亮乡间) — 官方MV 1920x1080, 底部繁体歌词裁掉, 提亮暖金, swell落乡间黄昏(源~165)
prep daoxiang  raw/daoxiang_yt.mkv  122 64.0 "1920:935:0:0" \
  "eq=brightness=0.05:saturation=1.08:contrast=1.04,colorbalance=rm=0.08:rh=0.05:gm=0.01:bm=-0.08:bh=-0.04" -0.10

echo "=== BEDS (intro=晴天 / outro=稻香) ==="
ffmpeg -v error -i raw/qingtian_4k.mp4 -ss 8 -t 32 -vn \
  -af "aresample=48000,loudnorm=I=-15:TP=-1.5:LRA=11" -ac 2 audio/qingtian_bed.wav -y
ffmpeg -v error -i raw/daoxiang_yt.mkv -ss 150 -t 34 -vn \
  -af "aresample=48000,loudnorm=I=-15:TP=-1.5:LRA=11" -ac 2 audio/daoxiang_bed.wav -y

echo "=== PREP ALL DONE ==="
for k in qingtian pugongying guiji zuichang daoxiang; do
  printf "%-11s " $k; ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x clips/vert_${k}.mp4
  printf "  dur="; ffprobe -v error -show_entries format=duration -of csv=p=0 clips/vert_${k}.mp4
done