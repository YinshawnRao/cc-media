#!/usr/bin/env bash
# 切 showcase 段(输出端 seek 精确) + 前景调色 + 竖屏化(vfill 裁烧字/水印/黑边)。
# 产物: clips_seg/<key>.mp4 (1080x1920 footage), audio/<key>_music.wav (pcm 展示段音乐)。
# crop 满足 H/W>=1.78 → fg 填满 1920 高(不露模糊边)。start 必须 == full_build.py 的 W(口型同步)。
set -euo pipefail
cd /Users/yinshawnrao/explorer/cc-media/sandbox/wuqingfeng-for-others
ROOT=/Users/yinshawnrao/explorer/cc-media
VFILL="$ROOT/tools/video/vfill.sh"
mkdir -p clips_seg audio tmp

# key|raw|start(=W)|len|crop W:H:X:Y|bg_br|bg_sat|fg_eq(空=不调)
# 倒数 #5->#1。crop 排除烧死歌词/水印/黑边。
ROWS=(
  "guaimei|raw/guaimei_yt.mp4|245.0|16.0|560:1040:560:0|-0.20|1.02|"
  "nianlun|raw/nianlun_yt.mp4|66.0|16.0|560:1040:260:0|-0.18|1.04|eq=brightness=0.04:contrast=1.05:saturation=1.06"
  "diaole|raw/diaole_bili.mp4|163.0|16.0|560:1040:1240:0|-0.18|1.04|eq=contrast=1.06:saturation=1.06"
  "daiwozou|raw/daiwozou_live.mp4|99.0|16.0|560:1040:680:0|-0.18|1.04|eq=brightness=0.06:contrast=1.05:saturation=1.10"
  "youxing|raw/youxing_yt.mp4|145.0|16.0|472:840:800:0|-0.20|1.02|eq=contrast=1.04"
)
for row in "${ROWS[@]}"; do
  IFS='|' read -r key raw start len crop br sat fgeq <<< "$row"
  echo "=== $key  win=${start}+${len}s crop=$crop fg_eq=${fgeq:-none} ==="
  VF="-an"
  if [ -n "$fgeq" ]; then VF="-vf $fgeq -an"; fi
  ffmpeg -nostdin -v error -i "$raw" -ss "$start" -t "$len" $VF \
    -c:v libx264 -preset veryfast -r 30 -g 30 -keyint_min 30 -pix_fmt yuv420p \
    "tmp/${key}_seg.mp4" -y
  ffmpeg -nostdin -v error -f lavfi -t "$len" -i anullsrc=r=48000:cl=stereo \
    -i "tmp/${key}_seg.mp4" -map 1:v -map 0:a -c:v copy -c:a aac -shortest \
    "tmp/${key}_segA.mp4" -y
  bash "$VFILL" "tmp/${key}_segA.mp4" "clips_seg/${key}.mp4" "$crop" "$br" "$sat"
  ffmpeg -nostdin -v error -i "$raw" -ss "$start" -t "$len" -vn -ac 2 -ar 48000 \
    -c:a pcm_s16le "audio/${key}_music.wav" -y
done
echo "ALL CLIPS DONE"
