#!/bin/bash
set -e
cd /Users/yinshawnrao/explorer/cc-media/sandbox/feilunhai-underrated-top5
COOK=/Users/yinshawnrao/explorer/cc-media/all_cookies.txt
dl () {
  KEY="$1"; ID="$2"
  echo "===== downloading $KEY ($ID) ====="
  yt-dlp "https://www.youtube.com/watch?v=$ID" --cookies "$COOK" --no-playlist \
    -f "bv*[height<=1080]+ba/b" --merge-output-format mp4 \
    -o "downloads/raw_${KEY}.%(ext)s" 2>&1 | tail -2
}
dl p4_xinliyoushu     SLtoCqTZtBM
dl p3_liuxialai       IG1X5xPzQe8
dl p2_xiaxue          9Qm8TYJynlc
dl p1_yigerenliulang  0p3I1hvTX6c
echo "=== ALL DONE ==="
ls -la downloads/
