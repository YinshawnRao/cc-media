#!/usr/bin/env bash
cd /Users/yinshawnrao/explorer/cc-media/sandbox/wuyuetian-graduation
CK="../www.youtube.com_cookies.txt"
dl () {
  local key="$1" id="$2"
  echo "=== downloading $key ($id) ==="
  yt-dlp "https://www.youtube.com/watch?v=$id" --cookies "$CK" --no-playlist --no-progress --quiet --no-warnings \
    -f "bv*[height<=1080][vcodec^=avc]+ba/b[height<=1080]" \
    -o "raw/${key}_full.%(ext)s" 2>&1 | tail -1
  local f=$(ls raw/${key}_full.* 2>/dev/null | head -1)
  echo "  -> $f  $(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x "$f" 2>/dev/null)  dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f" 2>/dev/null)"
}
dl sgj    hKPtVlSW2qA
dl ganbei qX2GsMj7154
dl hldwm  pd3eV-SG23E
dl zyjs   Jv3zvWZlXkk
echo "=== ALL DOWNLOADS DONE ==="
