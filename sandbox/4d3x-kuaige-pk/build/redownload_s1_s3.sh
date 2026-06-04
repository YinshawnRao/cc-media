#!/bin/bash
# 替换 s1 蔡依林 和 s3 孙燕姿 为 YT 480p 官方版（牺牲清晰度换取无烧字/无水印）
set -e
cd /Users/yinshawnrao/explorer/cc-media

YTC="sandbox/www.youtube.com_cookies.txt"
OUT="sandbox/4d3x-kuaige-pk/raw"

# s1 蔡依林《舞娘》— YT 0EN3MnGEBXk (Jolin 官方频道，480p，无烧字水印)
# MV 时长 3:42。副歌 typical: 1:00-1:30 (chorus1), 2:20-2:50 (chorus2/3)
echo "== s1 蔡依林《舞娘》(YT 480p 官方) =="
yt-dlp --cookies "$YTC" --download-sections "*00:01:00-00:01:50" \
  -f "bv*+ba/b" --no-playlist --merge-output-format mp4 \
  -o "$OUT/s1_caiyilin_wuniang_v2.%(ext)s" \
  "https://www.youtube.com/watch?v=0EN3MnGEBXk"

# s3 孙燕姿《超快感》— YT k_C-i4rbUpk (Timeless Music 官方，480p，无歌词版)
echo "== s3 孙燕姿《超快感》(YT 480p 官方) =="
yt-dlp --cookies "$YTC" --download-sections "*00:01:00-00:01:50" \
  -f "bv*+ba/b" --no-playlist --merge-output-format mp4 \
  -o "$OUT/s3_sunyanzi_chaokuaigan_v2.%(ext)s" \
  "https://www.youtube.com/watch?v=k_C-i4rbUpk"

echo "== Done =="
ls -la "$OUT/"*v2*
