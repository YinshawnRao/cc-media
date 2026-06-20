#!/usr/bin/env bash
# 陈慧琳最难5首 — 切片 + 竖屏化。
# 每段切片起点 = 副歌窗起点 − preroll(=voice_dur+2.1s)，让副歌落在展示段；clip 长 60s（> 整段时长，防黑屏）。
# 输出端 seek（-i src -ss S）抽干净音轨（避免 webm 从头重剪丢尾部音频）。
set -euo pipefail
ROOT="/Users/yinshawnrao/explorer/cc-media/sandbox/chenhuilin-hardest-top5"
VFILL="/Users/yinshawnrao/explorer/cc-media/tools/video/vfill.sh"
cd "$ROOT"
mkdir -p clips raw/seg
LEN=60

# key | source | clip_start | crop(W:H:X:Y)
clip () {
  local key="$1" src="$2" start="$3" crop="$4"
  echo "=== $key  start=$start  crop=$crop ==="
  ffmpeg -v error -i "$src" -ss "$start" -t "$LEN" \
    -c:v libx264 -preset veryfast -crf 18 -r 30 -g 30 -keyint_min 30 \
    -c:a aac -b:a 192k -ac 2 -ar 48000 "raw/seg/${key}.mp4" -y
  bash "$VFILL" "raw/seg/${key}.mp4" "clips/vert_${key}.mp4" "$crop"
}

clip huahua   raw/huahua_weaze.mp4 78.0  "1440:1080:240:0"
clip shiyi    raw/shiyi_637.webm   56.65 "960:505:0:45"
clip buru     raw/buru_bi.mp4      64.47 "1920:840:0:90"
clip darizi   raw/darizi_yt.webm   96.80 "640:480:0:0"
clip shuiyuan raw/shuiyuan_yt.webm 96.20 "640:385:0:0"

echo "=== clips done ==="
for f in clips/vert_*.mp4; do
  printf "%s  " "$f"
  ffprobe -v error -show_entries format=duration -of csv=p=0 "$f"
done
