#!/usr/bin/env bash
# 蔡依林毕业季 footage prep: cut window (output-seek) -> grade (color arc) -> vfill letterbox.
# 调色弧: 暖白柔光 -> sepia暖怀旧(演唱会重洗) -> 暖橙金(变身) -> 冷蓝夜(叙事) -> 金亮(燃finale)
set -uo pipefail
cd /Users/yinshawnrao/explorer/cc-media/sandbox/caiyilin-graduation
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
# 1 柠檬草的味道 (释然 / 暖白柔光) — 官方4K MV 无烧词, swell落暖白大特写(源~187)
prep lemon    176 58 "1920:1080:0:0" "eq=brightness=0.04:saturation=1.04:contrast=1.02,colorbalance=rm=0.06:rh=0.03:gm=0.01:bm=-0.07:bh=-0.03" -0.12
# 2 倒带 (回望 / sepia重洗) — 仅官方Live演唱会(无可用剧情MV), 重度去色+暖调压住舞台彩光做怀旧, swell落Jolin闭眼深情特写(源~82)
prep daodai   59  59 "1920:1080:0:0" "eq=brightness=0.02:saturation=0.60:contrast=1.06,colorbalance=rm=0.14:rh=0.08:gm=0.02:bm=-0.18:bh=-0.10" -0.18
# 3 看我72变 (告别 / 暖橙金) — 官方MV 底部烧词裁掉, swell落白帽/牛仔帽举手标志特写群(源162-180)
prep kanwo    140 60 "1456:905:0:0"  "eq=brightness=0.02:saturation=1.02:contrast=1.04,colorbalance=rm=0.08:rh=0.04:gm=0.01:bm=-0.10:bh=-0.05" -0.16
# 4 不一样又怎样 (怅惘 / 冷蓝夜) — 华纳官方MV(叙事片) 2.35:1裁掉黑边+底部字幕, swell落Jolin+林心如婚纱拥吻(源~208,双人letterbox不放大)
prep buyiyang 172 57 "1920:806:0:152" "eq=brightness=-0.02:saturation=0.80:contrast=1.05,colorbalance=rs=-0.05:rm=-0.07:bm=0.12:bh=0.10:bs=0.07" -0.22
# 5 玫瑰少年 (出发 / 金亮燃) — 官方Dance Video, 群舞燃finale(源~196起滚演职员字幕须避开), swell落群舞→Jolin黄衣居中展臂(源180)
prep meigui   123 60 "1920:1080:0:0" "eq=brightness=0.05:saturation=1.06:contrast=1.04,colorbalance=rm=0.08:rh=0.05:gm=0.01:bm=-0.09:bh=-0.04" -0.10
echo "=== PREP ALL DONE ==="
for k in lemon daodai kanwo buyiyang meigui; do printf "%-9s " $k; ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x clips/vert_${k}.mp4; ffprobe -v error -show_entries format=duration -of csv=p=0 clips/vert_${k}.mp4; done
