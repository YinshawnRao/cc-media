#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p raw

COOKIE="../../sandbox/www.youtube.com_cookies.txt"
FMT="bv*[height<=1080]+ba/b[height<=1080]"

yt-dlp --cookies "$COOKIE" --no-playlist -f "$FMT" --merge-output-format mp4 \
  -o "raw/juli.%(ext)s" "https://www.youtube.com/watch?v=vGIgU9Xaawg"

yt-dlp --cookies "$COOKIE" --no-playlist -f "$FMT" --merge-output-format mp4 \
  -o "raw/taicongming.%(ext)s" "https://www.youtube.com/watch?v=33rdx577PxY"

yt-dlp --cookies "$COOKIE" --no-playlist -f "$FMT" --merge-output-format mp4 \
  -o "raw/yigui.%(ext)s" "https://www.youtube.com/watch?v=BPNXyVzJjtw"

yt-dlp --cookies "$COOKIE" --no-playlist -f "$FMT" --merge-output-format mp4 \
  -o "raw/yigui_live.%(ext)s" "https://www.youtube.com/watch?v=2MTCYtab-RY"

yt-dlp --cookies "$COOKIE" --no-playlist -f "$FMT" --merge-output-format mp4 \
  -o "raw/wanmei80.%(ext)s" "https://www.youtube.com/watch?v=h3Rdw_NOQ3s"

yt-dlp --cookies "$COOKIE" --no-playlist -f "$FMT" --merge-output-format mp4 \
  -o "raw/fuxiu.%(ext)s" "https://www.youtube.com/watch?v=Pw9jk8eAg54"
