#!/usr/bin/env bash
# 竖屏填充：把任意素材片段做成 1080x1920，中心竖向裁切放大贴宽 + 模糊背景填满边距。
# 顺带可裁掉边角台标/底部歌词字幕。重编码 H.264 + 密集关键帧（避免 HyperFrames seek 卡顿）。
#
# 用法: vfill.sh <输入> <输出.mp4> <crop=W:H:X:Y> [brightness=-0.32] [sat=1.06]
#   crop 选 4:5 左右中心竖向裁切。例:
#     16:9 HD(1920x1080) 居中:        864:1080:528:0
#     16:9 暗调/Live(保留更多宽度):   1280:900:320:120
#     4:3 标清(640x480,裁底部水印):   384:400:128:0
set -euo pipefail
IN="$1"; OUT="$2"; CROP="$3"; BR="${4:--0.32}"; SAT="${5:-1.06}"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
BUDGET_RUNNER="$SCRIPT_DIR/resource_budget.py"
THREAD_TOKEN="__CC_MEDIA_THREADS__"

python3 "$BUDGET_RUNNER" ffmpeg -- ffmpeg -v error \
  -filter_threads "$THREAD_TOKEN" -filter_complex_threads "$THREAD_TOKEN" \
  -threads "$THREAD_TOKEN" -i "$IN" -filter_complex \
"[0:v]crop=${CROP},split=2[bg][fg];\
[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=30,eq=brightness=${BR}:saturation=${SAT}[bgb];\
[fg]scale=1080:-2[fgs];\
[bgb][fgs]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]" \
-map "[v]" -map 0:a -c:v libx264 -threads "$THREAD_TOKEN" \
  -preset veryfast -r 30 -g 30 -keyint_min 30 -c:a aac -b:a 192k "$OUT" -y
echo "wrote $OUT ($(ffprobe -v error -show_entries stream=width,height -of csv=p=0:s=x "$OUT" | head -1))"
