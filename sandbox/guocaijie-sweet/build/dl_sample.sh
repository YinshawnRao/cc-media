#!/usr/bin/env bash
# 样片素材下载（顺序执行，不并行）。产物写 raw/。
set -uo pipefail
cd /Users/yinshawnrao/explorer/cc-media
YT=sandbox/www.youtube.com_cookies.txt
RAW=sandbox/guocaijie-sweet/raw
mkdir -p "$RAW"

echo "===== 1/4 Little Sunshine 干净音轨 (官方Lyric Video, eVmlqqKHWHA) ====="
yt-dlp "https://www.youtube.com/watch?v=eVmlqqKHWHA" --cookies "$YT" --no-playlist \
  -x --audio-format wav -o "$RAW/littlesunshine_audio.%(ext)s" 2>&1 | tail -4
sleep 3

echo "===== 2/4 给他 官方HD MV 1080p (甜镜: 封面右+开头甜+No.1蒙太奇, xfR8JNIpfMU) ====="
yt-dlp "https://www.youtube.com/watch?v=xfR8JNIpfMU" --cookies "$YT" --no-playlist \
  --download-sections "*00:00:00-00:02:50" \
  -f "bv*[height<=1080][vcodec^=avc]+ba/b[height<=1080]" \
  -o "$RAW/gei_ta_mv.%(ext)s" 2>&1 | tail -4
sleep 3

echo "===== 3/4 小时代 官方预告 720p (冷顾里: 封面左+开头冷, DlX1A80YklM) ====="
yt-dlp "https://www.youtube.com/watch?v=DlX1A80YklM" --cookies "$YT" --no-playlist \
  -f "bv*[height<=720][vcodec^=avc]+ba/b[height<=720]" \
  -o "$RAW/xsd_trailer.%(ext)s" 2>&1 | tail -4
sleep 3

echo "===== 4/4 隐形超人 官方MV 480p (2007出道甜镜变化, zpphrk9soGY) ====="
yt-dlp "https://www.youtube.com/watch?v=zpphrk9soGY" --cookies "$YT" --no-playlist \
  --download-sections "*00:00:10-00:02:20" \
  -f "bv*+ba/b" \
  -o "$RAW/yxcr_mv.%(ext)s" 2>&1 | tail -4

echo ""
echo "===== 下载产物 ====="
ls -la "$RAW"
