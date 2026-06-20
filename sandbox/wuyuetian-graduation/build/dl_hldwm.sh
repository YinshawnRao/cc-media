#!/usr/bin/env bash
cd /Users/yinshawnrao/explorer/cc-media/sandbox/wuyuetian-graduation
yt-dlp "https://www.youtube.com/watch?v=pd3eV-SG23E" --cookies "../www.youtube.com_cookies.txt" \
  --no-playlist --no-progress --quiet --no-warnings --retries 10 --fragment-retries 20 \
  -f "bv*[height<=1080][vcodec^=avc]+ba/b[height<=1080]" -o "raw/hldwm_full.%(ext)s" 2>&1 | tail -1
f=$(ls raw/hldwm_full.* | head -1)
n=$(ffmpeg -v error -i "$f" -f null - 2>&1 | grep -ic "nal\|error\|corrupt")
echo "hldwm re-dl: $f dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f") errors=$n"
