#!/usr/bin/env bash
set -uo pipefail
cd /Users/yinshawnrao/explorer/cc-media
CK=sandbox/www.youtube.com_cookies.txt
RAW=sandbox/fws-no-jay/raw
PAIRS="s2:z9drIRdLh88 s3:EQ5Ib7jNnnE s4:DkTmr1ZhnfQ s5:4n1XN7E-ZSY s6:AKjgg3I6HEQ s7:E7fCgKvMYAQ"
for pair in $PAIRS; do
  k="${pair%%:*}"; id="${pair##*:}"
  echo "===== downloading $k ($id) ====="
  rm -f $RAW/${k}_src.* 2>/dev/null
  yt-dlp "https://www.youtube.com/watch?v=$id" --cookies "$CK" --no-playlist \
    -f "bv*[height<=1080]+ba/b[height<=1080]" -o "$RAW/${k}_src.%(ext)s" 2>&1 | tail -2
  SF=$(ls $RAW/${k}_src.* 2>/dev/null | head -1)
  echo "re-encode $k <- $SF"
  ffmpeg -v error -i "$SF" -c:v libx264 -preset veryfast -crf 19 -r 30 -g 30 -keyint_min 30 -c:a aac -b:a 192k "$RAW/${k}_full.mp4" -y
  echo "$k done: $(ffprobe -v error -show_entries format=duration -show_entries stream=width,height -of csv=p=0:s=x "$RAW/${k}_full.mp4" 2>/dev/null | head -1)"
done
echo "===== ALL DOWNLOADS DONE ====="
