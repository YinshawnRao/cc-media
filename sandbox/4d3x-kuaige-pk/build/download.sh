#!/bin/bash
# 顺序下载 7 首歌的副歌切片到 raw/
# 每段约 50s，含完整副歌
set -e
cd /Users/yinshawnrao/explorer/cc-media

YTC="sandbox/www.youtube.com_cookies.txt"
BLC="sandbox/www.bilibili.com_cookies.txt"
OUT="sandbox/4d3x-kuaige-pk/raw"
mkdir -p "$OUT"

# 通用格式：B站<=1080p避免AV1单声道；YT<=1080p即可
BFMT='bv*[height<=1080]+ba/b[height<=1080]'
YFMT='bv*[height<=1080]+ba/b[height<=1080]'

# s1 蔡依林《舞娘》— B站 BV1Y34y12734 — 1:15-2:05
echo "== s1 蔡依林《舞娘》=="
yt-dlp --cookies "$BLC" --download-sections "*00:01:15-00:02:05" \
  -f "$BFMT" --no-playlist --merge-output-format mp4 \
  -o "$OUT/s1_caiyilin_wuniang.%(ext)s" \
  "https://www.bilibili.com/video/BV1Y34y12734"

# s2 萧亚轩《爱的主打歌》— YT tgxolGZ_NQY — 0:40-1:30
echo "== s2 萧亚轩《爱的主打歌》=="
yt-dlp --cookies "$YTC" --download-sections "*00:00:40-00:01:30" \
  -f "$YFMT" --no-playlist --merge-output-format mp4 \
  -o "$OUT/s2_xiaoyaxuan_zhudage.%(ext)s" \
  "https://www.youtube.com/watch?v=tgxolGZ_NQY"

# s3 孙燕姿《超快感》— B站 BV1uU95BsEPb — 1:00-1:50
echo "== s3 孙燕姿《超快感》=="
yt-dlp --cookies "$BLC" --download-sections "*00:01:00-00:01:50" \
  -f "$BFMT" --no-playlist --merge-output-format mp4 \
  -o "$OUT/s3_sunyanzi_chaokuaigan.%(ext)s" \
  "https://www.bilibili.com/video/BV1uU95BsEPb"

# s4 梁静茹《燕尾蝶》— B站 BV1j7411C7gK — 2:30-3:20
echo "== s4 梁静茹《燕尾蝶》=="
yt-dlp --cookies "$BLC" --download-sections "*00:02:30-00:03:20" \
  -f "$BFMT" --no-playlist --merge-output-format mp4 \
  -o "$OUT/s4_liangjingru_yanweidie.%(ext)s" \
  "https://www.bilibili.com/video/BV1j7411C7gK"

# s5 王心凌《Honey》— YT COmOMjwnK8U — 2:35-3:25
echo "== s5 王心凌《Honey》=="
yt-dlp --cookies "$YTC" --download-sections "*00:02:35-00:03:25" \
  -f "$YFMT" --no-playlist --merge-output-format mp4 \
  -o "$OUT/s5_wangxinling_honey.%(ext)s" \
  "https://www.youtube.com/watch?v=COmOMjwnK8U"

# s6 张韶涵《That Girl》— YT 6htyfxPkYDU — 0:55-1:45
echo "== s6 张韶涵《That Girl》=="
yt-dlp --cookies "$YTC" --download-sections "*00:00:55-00:01:45" \
  -f "$YFMT" --no-playlist --merge-output-format mp4 \
  -o "$OUT/s6_zhangshaohan_thatgirl.%(ext)s" \
  "https://www.youtube.com/watch?v=6htyfxPkYDU"

# s7 杨丞琳《新流感》— YT dQOOTrRfV24 — 1:50-2:40 (1080×1080方画幅)
echo "== s7 杨丞琳《新流感》=="
yt-dlp --cookies "$YTC" --download-sections "*00:01:50-00:02:40" \
  -f "$YFMT" --no-playlist --merge-output-format mp4 \
  -o "$OUT/s7_yangchenglin_xinliugan.%(ext)s" \
  "https://www.youtube.com/watch?v=dQOOTrRfV24"

echo "== ALL DOWNLOADS DONE =="
ls -la "$OUT/"
