#!/usr/bin/env bash
# 杨千嬅最难5首 — 展示段 footage 预切 + 裁烧词/字幕/水印 + letterbox 竖屏。
# 两步：① 输出端 seek 精切窗(H264, 可 delogo 去UP水印) ② vfill letterbox(全宽保原比例)。
# 全宽 letterbox：crop 传「全宽横带 W:H:0:Y」→ fg 缩到 1080 宽居中，上下模糊填充，不放大不竖裁。
set -euo pipefail
cd /Users/yinshawnrao/explorer/cc-media/sandbox/yangqianhua-hardest
RAW=raw; TMP=clips/_tmp; OUT=clips; mkdir -p "$TMP"

# key | src | Wstart | LEN | CROP(crop去字幕) | DELOGO(去UP水印,none=无)
JOBS=(
  "vert_intro|xiaocheng_ts.webm|5|32|1920:720:0:0|none"
  "vert_xiaocheng|xiaocheng_live.mp4|59|56|1920:900:0:0|x=4:y=64:w=244:h=66"
  "vert_shuiping|shuiping_bili.mp4|124|52|1920:900:0:0|none"
  "vert_shaonv|shaonv_bili.mp4|90|52|1920:900:0:0|none"
  "vert_yehaizi|yehaizi_yy.webm|108|52|1280:608:0:0|none"
  "vert_jiaru|jiaru_solo.mp4|103|52|1920:900:0:0|none"
)
for j in "${JOBS[@]}"; do
  IFS='|' read -r key src W LEN CROP DELOGO <<< "$j"
  echo "=== $key  src=$src  W=$W LEN=$LEN crop=$CROP delogo=$DELOGO ==="
  PREVF=""
  [ "$DELOGO" != "none" ] && PREVF="delogo=${DELOGO},"
  # ① 输出端 seek 精切窗 (+可选 delogo)
  ffmpeg -v error -i "$RAW/$src" -ss "$W" -t "$LEN" \
    -vf "${PREVF}format=yuv420p" \
    -c:v libx264 -preset veryfast -crf 18 -r 30 -g 30 -keyint_min 30 \
    -c:a aac -b:a 192k -ac 2 -ar 48000 "$TMP/$key.mp4" -y
  # ② letterbox 竖屏（全宽，crop 去字幕带）
  ffmpeg -v error -i "$TMP/$key.mp4" -filter_complex \
    "[0:v]crop=${CROP},split=2[bg][fg];\
[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=30,eq=brightness=-0.30:saturation=1.06[bgb];\
[fg]scale=1080:-2[fgs];\
[bgb][fgs]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]" \
    -map "[v]" -map 0:a -c:v libx264 -preset veryfast -crf 19 -r 30 -g 30 -keyint_min 30 \
    -c:a aac -b:a 192k "$OUT/$key.mp4" -y
  echo "  -> $OUT/$key.mp4 $(ffprobe -v error -show_entries stream=width,height -of csv=p=0:s=x "$OUT/$key.mp4" | head -1) dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT/$key.mp4")"
done
rm -rf "$TMP"
echo "ALL CLIPS DONE"