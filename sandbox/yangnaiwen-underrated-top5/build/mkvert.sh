#!/usr/bin/env bash
# 竖屏填充 + 前景可调亮度（vfill.sh 只调背景，暗源前景需单独提亮）。
# 用法: mkvert.sh <in> <out.mp4> <crop=W:H:X:Y> [fg_bright=0.0] [fg_sat=1.06] [ss=] [t=]
set -euo pipefail
IN="$1"; OUT="$2"; CROP="$3"; FGB="${4:-0.0}"; FGS="${5:-1.06}"; SS="${6:-}"; T="${7:-}"
# output-seek (-ss/-t AFTER -i) for accurate cuts (coupled lip-sync / window precision)
SEEK=(); [ -n "$SS" ] && SEEK=(-ss "$SS"); DUR=(); [ -n "$T" ] && DUR=(-t "$T")
ffmpeg -v error -i "$IN" "${SEEK[@]}" "${DUR[@]}" -filter_complex \
"[0:v]crop=${CROP},split=2[bg][fg];\
[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=32,eq=brightness=-0.34:saturation=1.0[bgb];\
[fg]eq=brightness=${FGB}:saturation=${FGS},scale=1080:-2[fgs];\
[bgb][fgs]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]" \
-map "[v]" -an -c:v libx264 -preset veryfast -r 30 -g 30 -keyint_min 30 "$OUT" -y
echo "wrote $OUT ($(ffprobe -v error -show_entries stream=width,height,duration -of csv=p=0:s=x "$OUT" | head -1))"
