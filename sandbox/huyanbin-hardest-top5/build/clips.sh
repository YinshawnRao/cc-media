#!/usr/bin/env bash
# 胡彦斌最难5首 — 切片 + 竖屏化。
# clip_start 已按 CONVENTIONS「展示段硬规则 C」反推：
# 1) 先用 build/analyze_high_notes.py 找人声高音/高密度唱段候选；
# 2) 再让 full-music 展示窗落在人声覆盖率更高、且包含高点/难句的连续演唱区间。
set -euo pipefail
ROOT="/Users/yinshawnrao/explorer/cc-media/sandbox/huyanbin-hardest-top5"
VFILL="/Users/yinshawnrao/explorer/cc-media/tools/video/vfill.sh"
cd "$ROOT"
mkdir -p clips raw/seg
LEN=62

clip () {
  local key="$1" src="$2" start="$3" crop="$4"
  echo "=== $key  start=$start  crop=$crop ==="
  ffmpeg -v error -i "$src" -ss "$start" -t "$LEN" \
    -c:v libx264 -preset veryfast -crf 18 -r 30 -g 30 -keyint_min 30 \
    -c:a aac -b:a 192k -ac 2 -ar 48000 "raw/seg/${key}.mp4" -y
  bash "$VFILL" "raw/seg/${key}.mp4" "clips/vert_${key}.mp4" "$crop"
}

# Intro/outro use the #1 official MV source: cleaner than the 2026 stage cut, which exposes sponsor boards.
clip intro      raw/quannazou_mv_yt.mp4 177.8 "1920:940:0:0"
clip shiye      raw/shiye_live_yt.mp4 128.8 "1280:620:0:20"
clip juebieshi  raw/juebieshi_yt.mp4 185.5 "640:360:0:60"
clip hongyan    raw/hongyan_yt.mp4   100.1 "1920:760:0:160"
clip yueguang   raw/yueguang_bili_live.mp4 36.0 "1920:620:0:120"
clip quannazou  raw/quannazou_mv_yt.mp4 179.2 "1920:940:0:0"

echo "=== clips done ==="
for f in clips/vert_*.mp4; do
  printf "%s  " "$f"
  ffprobe -v error -show_entries format=duration -of csv=p=0 "$f"
done
