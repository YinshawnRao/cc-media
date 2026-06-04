#!/usr/bin/env bash
# 顺序下载 5 首最终切片（绝对路径，后台安全）。每首 = chorus_start-24s 起、约56s，
# 副歌段落在 SHOW 尾段（build 里再精切 clips_seg 对齐口型）。
set -uo pipefail
ROOT=/Users/yinshawnrao/explorer/cc-media
PROJ=$ROOT/sandbox/wangfeng-hardest
YCK=$ROOT/sandbox/www.youtube.com_cookies.txt
BCK=$ROOT/sandbox/www.bilibili.com_cookies.txt
RAW=$PROJ/raw
mkdir -p "$RAW"
cd "$RAW"

dl() { # name url cookie sections fmt
  echo "=== $1  $4 ==="
  yt-dlp "$2" --cookies "$3" --download-sections "*$4" --no-playlist \
    -f "$5" --force-keyframes-at-cuts \
    -o "$RAW/$1.%(ext)s" 2>&1 | tail -4
  ls -la "$RAW/$1."* 2>/dev/null
}

# 1 光明  B站 2014鸟巢 1080p60 立体声  chorus 03:08
dl guangming   "https://www.bilibili.com/video/BV1Rg41137BU" "$BCK" "00:02:44-00:03:40" "bv*[height<=1080]+ba/b[height<=1080]"
# 2 等待  YT 歌手2018 1080p25 立体声  chorus 03:38
dl dengdai     "https://www.youtube.com/watch?v=3a2Tudvgnnc" "$YCK" "00:03:14-00:04:10" "bv*[height<=1080]+ba/b[height<=1080]"
# 3 存在  YT 风华秋实官方MV 720p 立体声  chorus ~03:40 (避开 04:08 过曝)
dl cunzai      "https://www.youtube.com/watch?v=Ri89KOr1Z2I" "$YCK" "00:03:14-00:04:10" "bv*+ba/b"
# 4 勇敢的心 B站 蓝光修复 1080p 立体声  chorus 02:00
dl yonggan     "https://www.bilibili.com/video/BV1oC4y1b7SC" "$BCK" "00:01:36-00:02:32" "bv*[height<=1080]+ba/b[height<=1080]"
# 5 一起摇摆 B站 4K60 立体声(remaster)  chorus 03:03
dl yiqiyaobai  "https://www.bilibili.com/video/BV1Ys4y1D7md" "$BCK" "00:02:39-00:03:35" "bv*+ba/b"

echo "=== DOWNLOAD DONE ==="
for s in guangming dengdai cunzai yonggan yiqiyaobai; do
  f=$(ls "$RAW/$s".* 2>/dev/null | head -1)
  if [ -n "$f" ]; then
    ffprobe -v error -select_streams v:0 -show_entries stream=width,height,codec_name,avg_frame_rate -of csv=p=0 "$f" | sed "s|^|$s VID: |"
    ffprobe -v error -select_streams a:0 -show_entries stream=channels,codec_name -of csv=p=0 "$f" | sed "s|^|$s AUD: |"
    ffprobe -v error -show_entries format=duration -of csv=p=0 "$f" | sed "s|^|$s DUR: |"
  else echo "$s MISSING"; fi
done
