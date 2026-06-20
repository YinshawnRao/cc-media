#!/usr/bin/env bash
cd /Users/yinshawnrao/explorer/cc-media/sandbox/wuyuetian-graduation
CK="../www.youtube.com_cookies.txt"
dl () {
  echo "=== $1 ($2) ==="
  yt-dlp "https://www.youtube.com/watch?v=$2" --cookies "$CK" --no-playlist --no-progress --quiet --no-warnings \
    -f "bv*[height<=1080][vcodec^=avc]+ba/b[height<=1080]" -o "raw/$1_full.%(ext)s" 2>&1 | tail -1
  local f=$(ls raw/$1_full.* 2>/dev/null | head -1)
  echo "  -> $f dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f" 2>/dev/null)"
}
dl sgj    hKPtVlSW2qA
dl ganbei qX2GsMj7154
echo "=== FIX DOWNLOADS DONE ==="
