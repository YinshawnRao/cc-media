#!/usr/bin/env bash
# 全片素材：从华纳官方4K串烧 8AWbq0XDbfE 切 No.5-No.2 各 ~98s(含verse+chorus)。顺序执行。
set -uo pipefail
cd /Users/yinshawnrao/explorer/cc-media
YT=sandbox/www.youtube.com_cookies.txt
RAW=sandbox/guocaijie-sweet/raw
U="https://www.youtube.com/watch?v=8AWbq0XDbfE"
F='bv*[height<=1080]+ba/b[height<=1080]'

dl(){ # section out
  echo "===== $2  ($1) ====="
  yt-dlp "$U" --cookies "$YT" --no-playlist --download-sections "$1" -f "$F" \
    -o "$RAW/$2.%(ext)s" 2>&1 | tail -3
  sleep 3
}
dl "*00:25:31-00:27:09" "s5_yueliang"     # 又圆了的月亮
dl "*01:02:37-01:04:15" "s4_kuaiyidian"   # 快一点
dl "*01:19:55-01:21:33" "s3_katong"       # 卡通人生
dl "*01:05:58-01:07:36" "s2_aiyixiang"    # 爱异想

echo "===== downloaded ====="
ls -la "$RAW"/s5_* "$RAW"/s4_* "$RAW"/s3_* "$RAW"/s2_* 2>/dev/null
