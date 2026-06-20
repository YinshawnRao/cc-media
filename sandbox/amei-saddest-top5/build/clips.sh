#!/usr/bin/env bash
# Build vertical 1080x1920 clips. Each clip covers the WHOLE segment (narration bed + show);
# output-seek S=6 inside each downloaded window so clip-time fsl == chorus start.
# mode lb  = letterbox 全宽保原比例 (crop = full-width band)
# mode zoom= 单主体竖向裁切放大贴宽 (crop = narrow vertical slab)
# optional delogo applied before crop (for residual watermarks).
set -uo pipefail
cd "$(dirname "$0")/.."
mkdir -p clips

# key | raw | S | L | crop(W:H:X:Y) | mode | brightness | sat | delogo(x:y:w:h or -)
CONFIG=(
  "cover|raw/renzhi_fix.mp4|41|17|3840:2160:0:0|lb|-0.30|1.02|-"
  "lianmingdaixing|raw/lmdx_official.webm|8.4|53.6|1920:946:0:0|lb|-0.32|1.05|-"
  "diaole|raw/diaole.mp4|9.9|48.12|3840:2160:0:0|lb|-0.34|1.05|-"
  "jianai|raw/jianai.mp4|4.75|45.25|712:382:0:0|lb|-0.30|1.08|-"
  "wohenwoaini|raw/wohenwoaini.mp4|6|54.6|2878:1850:0:150|lb|-0.32|1.06|-"
  "renzhi|raw/renzhi_fix.mp4|6|61.0|3840:2160:0:0|lb|-0.34|1.02|-"
)

for row in "${CONFIG[@]}"; do
  IFS='|' read -r key raw S L CROP mode BR SAT DELOGO <<< "$row"
  out="clips/vert_${key}.mp4"
  pre=""
  [ "$DELOGO" != "-" ] && pre="delogo=$DELOGO,"
  echo ">> ${key}: ${raw} S=${S} L=${L} crop=${CROP} mode=${mode} delogo=${DELOGO}"
  if [ "$mode" = "zoom" ]; then
    # fg fills frame (crop already ~9:16); bg = same crop scaled up + blur
    FILTER="[0:v]${pre}crop=${CROP},setsar=1,split=2[bg][fg];\
[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=28,eq=brightness=${BR}:saturation=${SAT}[bgb];\
[fg]scale=1080:-2[fgs];[bgb][fgs]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]"
  else
    # letterbox: fg = full-width crop scaled to 1080 wide; bg = same crop scaled up + blur
    FILTER="[0:v]${pre}crop=${CROP},setsar=1,split=2[bg][fg];\
[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=30,eq=brightness=${BR}:saturation=${SAT}[bgb];\
[fg]scale=1080:-2[fgs];[bgb][fgs]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]"
  fi
  ffmpeg -v error -ss "$S" -i "$raw" -t "$L" -filter_complex "$FILTER" \
    -map "[v]" -map "0:a" \
    -c:v libx264 -preset veryfast -crf 18 -r 30 -g 30 -keyint_min 30 -pix_fmt yuv420p \
    -c:a aac -b:a 192k -ac 2 -ar 48000 "$out" -y
  echo "   wrote $out ($(ffprobe -v error -show_entries format=duration -of csv=p=0 "$out")s, $(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x "$out"), ach=$(ffprobe -v error -select_streams a:0 -show_entries stream=channels -of csv=p=0 "$out"))"
done
echo "ALL CLIPS DONE"
