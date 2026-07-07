#!/usr/bin/env bash
# 生成各首竖屏 letterbox footage（output-seek 精确切窗 + crop 裁烧词/水印 + 模糊背景填充 + 分级调色）。
# 双人组合 → 全宽 letterbox 保原比例（大漠 SD 源带左侧竖排双列水印，例外用中心裁剪去左边）。
# intro 与 p5 取 symphony 同源连续窗（封面→#5 丝滑）；p2 复用 symphony 另一窗 + 冷调（史诗）。
# ⚠️ crop 值为抽帧实测后的最终值（见 SOURCES.md）：
#   symphony 1920:655:0:95 = 裁顶 UP水印(y40-85) + 底烧字幕/burned 凤凰传奇新年交响演唱会 lower-third(y755-850)
#   天籁 1280:450:0:55 = 裁顶黑边 + 底蓝水印(y510-575)+卡拉OK(y600+)
#   康定 1920:750:0:90 = 裁底卡拉OK(y840-960)
#   大漠 552:298:88:0 = 中心裁去左竖排双列水印(PHOENIX LEGEND/Vol.1 2005 x15-80)+底烧词(y300+)
set -euo pipefail
cd "$(dirname "$0")/.."
SYM=raw/probe_zhongguo_4k.mp4      # 4K交响 1920x960 (中国味道现场, 双人同台)
TIANLAI=raw/coll_tianlai.mp4       # 草原官方 MV 1280x720
KANGDING=raw/probe_kangding_mv.mp4 # 西藏实拍 DVD 官方 MV 1920x1080
DAMO=raw/probe_damo2005.webm       # 沙漠武士官方 MV 640x360

# clip <src> <out> <ss> <len> <crop> <fg_filter> <bg_br> <bg_sat>
clip() {
  local src="$1" out="$2" ss="$3" len="$4" crop="$5" fg="$6" bbr="$7" bsat="$8"
  ffmpeg -v error -i "$src" -ss "$ss" -t "$len" -filter_complex \
    "[0:v]crop=${crop},split=2[bg][fg];\
[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=30,eq=brightness=${bbr}:saturation=${bsat}[bgb];\
[fg]${fg},scale=1080:-2[fgs];\
[bgb][fgs]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]" \
    -map "[v]" -an -c:v libx264 -preset veryfast -r 30 -g 30 -keyint_min 30 "$out" -y
  echo "wrote $out ($(ffprobe -v error -show_entries stream=width,height,duration -of csv=p=0:s=x "$out"))"
}

WARM="eq=saturation=1.07:brightness=0.05,colorbalance=rm=0.03:gm=0.01"
COOL="eq=saturation=0.80:contrast=1.05,colorbalance=bm=0.05:bh=0.05:rs=-0.03"
DG="eq=saturation=1.05:brightness=0.02"

# 封面+#5 中国味道（symphony 同源连续窗 T0=48 双人同台, 暖festive）
clip "$SYM"      clips/vert_intro.mp4       48.0  18.5  1920:655:0:95  "$WARM" -0.28 1.10
clip "$SYM"      clips/vert_p5_zhongguo.mp4 65.35 48.2  1920:655:0:95  "$WARM" -0.28 1.10
# #2 传奇（symphony 另一窗 + 冷调史诗）
clip "$SYM"      clips/vert_p2_chuanqi.mp4  113.5 55.0  1920:655:0:95  "$COOL" -0.34 0.85
# #4 天籁传奇（草原 MV，裁底蓝水印+烧词）
clip "$TIANLAI"  clips/vert_p4_tianlai.mp4  27.0  46.0  1280:450:0:55  "eq=saturation=1.04" -0.32 1.06
# #3 康定情缘（DVD MV，裁底卡拉OK）
clip "$KANGDING" clips/vert_p3_kangding.mp4 18.0  51.0  1920:750:0:90  "eq=saturation=1.0" -0.32 1.06
# #1 大漠情人（沙漠武士 MV，中心裁去左竖排双列水印+底烧词）
clip "$DAMO"     clips/vert_p1_damo.mp4     26.0  50.0  552:298:88:0   "$DG" -0.30 1.05
# outro（大漠 desert 收尾，bookend 在 #1）
clip "$DAMO"     clips/vert_outro.mp4       120.0 32.0  552:298:88:0   "$DG" -0.30 1.05
echo "ALL CLIPS DONE"
