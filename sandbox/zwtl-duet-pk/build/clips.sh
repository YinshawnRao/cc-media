#!/usr/bin/env bash
# v2：每首一段【连续】副歌片段(~27-32s) + 【信箱式letterbox】保持MV原比例、不放大画面(全宽呈现,人物不被裁半)。
# 只裁掉烧死歌词/水印的横向窄带(全宽保留)；fg 下采样到1080宽居中, 模糊背景填上下黑边。
# footage 窗 == full_build 的 W → footage 与音乐同源同窗, 口型精确同步。
set -euo pipefail
cd /Users/yinshawnrao/explorer/cc-media/sandbox/zwtl-duet-pk
ROOT=/Users/yinshawnrao/explorer/cc-media
VFILL="$ROOT/tools/video/vfill.sh"
mkdir -p clips_seg tmp

# key | raw | W(start,与full_build一致) | DUR(=SHOW_TARGET+余量) | crop(全宽,裁烧词/水印带) | bg_br | bg_sat | fg_eq
ROWS=(
  "today|raw/tao_jolin_mv.mp4|26|32.4|1280:640:0:0|-0.26|1.05|eq=brightness=0.03:contrast=1.04:saturation=1.08"
  "coral|raw/jay_lara.mp4|25|28.4|1920:956:0:0|-0.28|1.04|eq=brightness=0.10:contrast=1.05:saturation=1.05"
  "dimples|raw/jj_asa_mv.mp4|24|27.4|1440:846:0:104|-0.24|1.05|eq=brightness=0.02:contrast=1.03:saturation=1.07"
  "heaven|raw/lh_zlj_live.mkv|98|28.4|1920:716:0:0|-0.26|1.04|eq=brightness=0.05:contrast=1.04:saturation=1.03"
)
for row in "${ROWS[@]}"; do
  IFS='|' read -r key raw W DUR crop br sat fgeq <<< "$row"
  echo "=== $key  win=${W}+${DUR}s  crop=$crop ==="
  # 连续切(输出端seek精确) + 前景调色, 密集关键帧
  ffmpeg -nostdin -v error -i "$raw" -ss "$W" -t "$DUR" -vf "$fgeq" -an \
    -c:v libx264 -preset veryfast -r 30 -g 30 -keyint_min 30 -pix_fmt yuv420p "tmp/${key}_seg.mp4" -y
  ffmpeg -nostdin -v error -f lavfi -t "$DUR" -i anullsrc=r=48000:cl=stereo \
    -i "tmp/${key}_seg.mp4" -map 1:v -map 0:a -c:v copy -c:a aac -shortest "tmp/${key}_segA.mp4" -y
  bash "$VFILL" "tmp/${key}_segA.mp4" "clips_seg/${key}.mp4" "$crop" "$br" "$sat"
done
echo "ALL CLIPS DONE"
