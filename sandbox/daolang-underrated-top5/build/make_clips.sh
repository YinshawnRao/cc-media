#!/usr/bin/env bash
set -euo pipefail
P=/Users/yinshawnrao/explorer/cc-media/sandbox/daolang-underrated-top5
V=/Users/yinshawnrao/explorer/cc-media/tools/video/vfill.sh
cd "$P"
# 知交 songs: delogo sponsor wm + letterbox in one pass
delogo_letterbox(){ # src out crop
  ffmpeg -v error -i "$1" -filter_complex \
"[0:v]delogo=x=1422:y=182:w=410:h=175,crop=$3,split=2[bg][fg];\
[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=30,eq=brightness=-0.30:saturation=1.06[bgb];\
[fg]scale=1080:-2[fgs];\
[bgb][fgs]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]" \
    -map "[v]" -map 0:a -c:v libx264 -preset veryfast -r 30 -g 30 -keyint_min 30 -c:a aac -b:a 192k "$2" -y
  echo "wrote $2"
}
delogo_letterbox raw/kashi_online.mp4    clips/vert_kashi.mp4     "1920:940:0:0"
delogo_letterbox raw/fengxiang_online.mp4 clips/vert_fengxiang.mp4 "1920:940:0:0"
bash "$V" raw/guazhou_mv.mp4     clips/vert_guazhou.mp4 "1920:850:0:0"
bash "$V" raw/erdao_xinjiang.mp4 clips/vert_erdao.mp4   "1920:875:0:0"
bash "$V" raw/deling_wlmq.mp4    clips/vert_deling.mp4  "1920:960:0:120"
echo "ALL CLIPS DONE"
