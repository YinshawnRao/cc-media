#!/usr/bin/env bash
# 孙燕姿毕业季 footage prep: cut window (output-seek) -> grade (color arc) -> vfill letterbox.
# 调色弧: 暖白柔光 -> sepia暖怀旧 -> 暖橙黄昏 -> 冷蓝夜 -> 金亮逆光
set -uo pipefail
cd /Users/yinshawnrao/explorer/cc-media/sandbox/sunyanzi-graduation
VF=../../tools/video/vfill.sh
prep () {
  local key=$1 win=$2 len=$3 crop=$4 grade=$5 br=$6
  echo "=== $key: cut(win=$win len=$len) ==="
  ffmpeg -v error -i raw/${key}_full.mp4 -ss $win -t $len -c:v libx264 -preset veryfast -crf 18 -g 30 -keyint_min 30 -c:a aac -b:a 192k raw/${key}_win.mp4 -y
  echo "=== $key: grade ==="
  ffmpeg -v error -i raw/${key}_win.mp4 -vf "$grade" -c:v libx264 -preset veryfast -crf 18 -c:a copy raw/${key}_graded.mp4 -y
  echo "=== $key: vfill ==="
  bash "$VF" raw/${key}_graded.mp4 clips/vert_${key}.mp4 "$crop" "$br" 1.0
}
# 1 当冬夜渐暖 (释然 / 暖白柔光) — 簽會 live, crop bottom-center 烧词
prep dongye   44  57 "1920:930:0:0"  "eq=brightness=0.04:saturation=1.03:contrast=1.02,colorbalance=rm=0.06:rh=0.03:gm=0.01:bm=-0.07:bh=-0.03" -0.12
# 2 我怀念的 (回望 / sepia暖怀旧) — 4K MV, crop bottom 烧词
prep huainian 122 58 "2560:1210:0:0" "eq=brightness=0.03:saturation=0.80:contrast=1.05,colorbalance=rm=0.11:rh=0.05:gm=0.03:bm=-0.13:bh=-0.06" -0.18
# 3 遇见 (告别 / 暖橙黄昏) — 4K MV 无烧词, swell 落绿野行走signature(源~105.5)→大特写
prep yujian   83 60 "2560:1440:0:0" "eq=brightness=0.02:saturation=1.04:contrast=1.04,colorbalance=rm=0.08:rh=0.04:gm=0.01:bm=-0.10:bh=-0.05" -0.16
# 4 天黑黑 (怅惘 / 冷蓝夜) — 4K MV 无持续烧词, swell 落成年芦苇地独唱(源~70)
prep tianheihei 46 59 "2560:1440:0:0" "eq=brightness=-0.02:saturation=0.78:contrast=1.06,colorbalance=rs=-0.06:rm=-0.08:bm=0.12:bh=0.10:bs=0.08" -0.22
# 5 逆光 (出发 / 金亮逆光) — 4K MV 无烧词, swell 落最终副歌嘶吼特写(源~228,响)→举臂金字塔finale(源264)
prep niguang  204 68 "2560:1440:0:0" "eq=brightness=0.04:saturation=1.08:contrast=1.02,colorbalance=rm=0.07:rh=0.05:gm=0.02:bm=-0.08:bh=-0.04" -0.10
echo "=== PREP ALL DONE ==="
for k in dongye huainian yujian tianheihei niguang; do printf "%-11s " $k; ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x clips/vert_${k}.mp4; ffprobe -v error -show_entries format=duration -of csv=p=0 clips/vert_${k}.mp4; done
