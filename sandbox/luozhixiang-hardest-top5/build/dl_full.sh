#!/usr/bin/env bash
set -uo pipefail
cd /Users/yinshawnrao/explorer/cc-media/sandbox/luozhixiang-hardest-top5
COOK=/Users/yinshawnrao/explorer/cc-media/all_cookies.txt
PC=web_safari
PAIRS="jingwumen:3WAgjt-cDQg wujixian:XOUImj1TlHY duyiwuer:1SDy8W6FoV8 pinshenme:2iNsT9dXDrw bujuming:HfO2yMfLsw0"
for p in $PAIRS; do
  k=${p%%:*}; id=${p##*:}
  echo "==== $k $id ===="
  yt-dlp --cookies "$COOK" "https://www.youtube.com/watch?v=$id" \
    --extractor-args "youtube:player_client=$PC" \
    -f "bv*[height<=1080]+ba/b" --no-playlist --merge-output-format mp4 \
    -o "downloads/$k.%(ext)s" 2>&1 | tail -2
  ffprobe -v error -select_streams v -show_entries stream=width,height -of csv=p=0 "downloads/$k.mp4" 2>/dev/null && echo "  -> $k OK"
done
echo "ALL DONE"
