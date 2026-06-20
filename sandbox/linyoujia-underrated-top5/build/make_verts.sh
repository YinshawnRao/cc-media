#!/bin/bash
# Cut window -> delogo watermark / crop burned lyrics -> letterbox 1080x1920 (keep原比例, no放大).
# All sources are pre-cut windows in raw/ (start at 0 unless offset given).
set -e
cd /Users/yinshawnrao/explorer/cc-media/sandbox/linyoujia-underrated-top5
mkdir -p clips

LB='scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=28,eq=brightness=-0.36:saturation=1.02'

vert () {
  src="$1"; out="$2"; start="$3"; len="$4"; pre="$5"; fgeq="$6"   # pre ends with comma if non-empty; fgeq optional fg eq
  fgchain="scale=1080:-2"
  [ -n "$fgeq" ] && fgchain="$fgeq,scale=1080:-2"
  ffmpeg -v error -ss "$start" -i "$src" -t "$len" -filter_complex \
    "[0:v]${pre}split=2[bg][fg];[bg]${LB}[bgb];[fg]${fgchain}[fgs];[bgb][fgs]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]" \
    -map "[v]" -an -c:v libx264 -preset veryfast -crf 19 -r 30 -g 30 -keyint_min 30 "clips/$out" -y
  echo "wrote clips/$out  $(ffprobe -v error -show_entries format=duration -of csv=p=0 clips/$out)s  $(ffprobe -v error -select_streams v -show_entries stream=width,height -of csv=p=0:s=x clips/$out)"
}

# watermark for 神遊/苏先生 uploaders sits at y~45-100, x~30-350 (NOT top edge) -> delogo correct box
WM="delogo=x=12:y=38:w=350:h=76"
# ---- showcase clips (offsets chosen so the SHOWCASE region lands on closeup clusters) ----
# 1 耳朵 : 改用神遊2012 4K 特写蒙太奇（感官世界 SD 烧字幕压在嘴/麦上不可裁，弃）: delogo
vert raw/erduo2_foot.mp4  vert_erduo.mp4   1  34 "$WM,"  ""
# 2 慢一点 (The Great Yoga, 1280x576) : 烧词带在 y390-510 -> 留 y0-385（脸完整）
vert raw/manyidian_win.mp4 vert_manyidian.mp4 0 34 "crop=1280:385:0:0,"  ""
# 3 拾荒 (神遊 4K, dark suit) : delogo ; offset 5 -> showcase 落在特写簇
vert raw/shihuang_foot.mp4 vert_shihuang.mp4 5 34 "$WM,"  ""
# 4 4号病房 (神遊, tan suit) : delogo ; offset 8 -> 避开宽景
vert raw/sihao_foot.mp4   vert_sihao.mp4   8 34 "$WM,"  ""
# 5 飞 (solo live, 1080p) : delogo + crop 双行烧词带 y840-950 -> 留 y0-835（脸完整）
vert raw/fei_foot.mp4     vert_fei.mp4     0 34 "$WM,crop=1920:835:0:0,"  ""
# cover (神遊 closeup) : delogo ; start on a closeup frame
vert raw/cover_foot.mp4   vert_cover.mp4   16.5 13 "$WM,"  ""
# outro backdrop (神遊 cover window full) : delogo
vert raw/cover_foot.mp4   vert_outro.mp4   0  37 "$WM,"  ""
echo ALL_VERTS_DONE
