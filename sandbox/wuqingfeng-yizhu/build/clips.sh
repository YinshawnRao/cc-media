#!/usr/bin/env bash
# 切 showcase 段(输出端 seek 精确切) + 可选前景调色 + 竖屏化(vfill 裁烧字/字幕/黑边)。
# 产物: clips_seg/<key>.mp4 (1080x1920 footage), audio/<key>_music.wav (pcm 展示段音乐)。
set -euo pipefail
cd /Users/yinshawnrao/explorer/cc-media/sandbox/wuqingfeng-yizhu
ROOT=/Users/yinshawnrao/explorer/cc-media
VFILL="$ROOT/tools/video/vfill.sh"
mkdir -p clips_seg audio tmp

# key|raw|start|len|crop W:H:X:Y|bg_br|bg_sat|fg_eq(空=不调)
# 倒数顺序 #5->#1。crop 已排除烧死歌词/字幕/黑边。
ROWS=(
  "shuimeiren|raw/shuimeiren_yt.mp4|201.0|16.0|472:840:724:0|-0.18|1.04|"
  "deng|raw/deng_bili.mp4|149.0|16.0|700:840:610:60|-0.05|1.06|eq=brightness=0.06:contrast=1.06:saturation=1.08"
  "yimengji|raw/yimengji_yt.mp4|380.0|17.0|506:900:707:0|-0.18|1.06|"
  "shangfeng|raw/shangfeng_yt.mp4|256.0|17.0|416:740:816:80|-0.14|1.08|eq=brightness=0.06:contrast=1.07:saturation=1.08"
  "xian|raw/xian_bili.mp4|203.0|13.0|608:1080:656:0|-0.22|1.04|eq=contrast=1.36:brightness=-0.08:saturation=1.13"
)
for row in "${ROWS[@]}"; do
  IFS='|' read -r key raw start len crop br sat fgeq <<< "$row"
  echo "=== $key  win=${start}+${len}s crop=$crop fg_eq=${fgeq:-none} ==="
  VF="-an"
  if [ -n "$fgeq" ]; then VF="-vf $fgeq -an"; fi
  # video-only segment, output-side seek (accurate), dense keyframes, optional fg eq
  ffmpeg -nostdin -v error -i "$raw" -ss "$start" -t "$len" $VF \
    -c:v libx264 -preset veryfast -r 30 -g 30 -keyint_min 30 -pix_fmt yuv420p \
    "tmp/${key}_seg.mp4" -y
  # vfill needs an audio track (-map 0:a): attach silent stereo track
  ffmpeg -nostdin -v error -f lavfi -t "$len" -i anullsrc=r=48000:cl=stereo \
    -i "tmp/${key}_seg.mp4" -map 1:v -map 0:a -c:v copy -c:a aac -shortest \
    "tmp/${key}_segA.mp4" -y
  bash "$VFILL" "tmp/${key}_segA.mp4" "clips_seg/${key}.mp4" "$crop" "$br" "$sat"
  # showcase music wav (pcm) from raw at same window
  ffmpeg -nostdin -v error -i "$raw" -ss "$start" -t "$len" -vn -ac 2 -ar 48000 \
    -c:a pcm_s16le "audio/${key}_music.wav" -y
done
echo "ALL CLIPS DONE"