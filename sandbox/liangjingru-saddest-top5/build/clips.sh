#!/usr/bin/env bash
# Cut each chorus segment (output-side seek = accurate) and letterbox/zoom to 1080x1920.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p clips

# key | seg file | start(s) | len(s) | crop(W:H:X:Y)
CONFIG=(
  "cover|raw/seg_kexi.mp4|12|26|1474:812:0:0"
  "huiguoqu|raw/seg_huiguoqu.mp4|0|60|520:720:290:108"
  "chongbai|raw/seg_chongbai.mp4|0|58|1920:975:0:105"
  "manleng|raw/seg_manleng.mp4|0|60|2520:2160:660:0"
  "kexi|raw/seg_kexi.mp4|0|62|1474:812:0:0"
  "huxi|raw/seg_huxi.mp4|0|64|1474:812:0:0"
)

for row in "${CONFIG[@]}"; do
  IFS='|' read -r key seg S L CROP <<< "$row"
  out="clips/vert_${key}.mp4"
  echo ">> ${key}: ${seg} ss=${S} t=${L} crop=${CROP}"
  ffmpeg -v error -i "$seg" -ss "$S" -t "$L" -filter_complex \
    "[0:v]crop=${CROP},split=2[bg][fg];\
[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=30,eq=brightness=-0.30:saturation=1.05[bgb];\
[fg]scale=1080:-2[fgs];\
[bgb][fgs]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]" \
    -map "[v]" -map 0:a -c:v libx264 -preset veryfast -r 30 -g 30 -keyint_min 30 \
    -c:a aac -b:a 192k "$out" -y
  echo "   wrote $out ($(ffprobe -v error -show_entries format=duration -of csv=p=0 "$out")s, $(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x "$out"))"
done
echo "ALL CLIPS DONE"
