#!/bin/bash
# 把 raw/ 各源做成 clips/vert_sX.mp4（1080×1920 竖屏，模糊背景填充，底部歌词已 crop）。
set -e
ROOT=/Users/yinshawnrao/explorer/cc-media
cd "$ROOT"
VF="$ROOT/tools/video/vfill.sh"
RAW="sandbox/4d3x-kuaige-pk/raw"
OUT="sandbox/4d3x-kuaige-pk/clips"
mkdir -p "$OUT"

# s1 蔡依林《舞娘》— YT 480p 官方版，有底部歌词烧字 + letterbox 黑边 → 二阶段裁
# 原片 712×480，content 区约 y=30-415（black bars），lyrics 约 y=420-475
bash "$VF" "$RAW/s1_caiyilin_wuniang_v2.mp4" "$OUT/vert_s1.mp4" "712:360:0:50" -0.20 1.08

# s2 萧亚轩《爱的主打歌》— YT 4K 官方，画面干净
bash "$VF" "$RAW/s2_xiaoyaxuan_zhudage.mp4" "$OUT/vert_s2.mp4" "864:1080:528:0" -0.20 1.10

# s3 孙燕姿《超快感》— YT 480p 官方版，底部歌词
bash "$VF" "$RAW/s3_sunyanzi_chaokuaigan_v2.mp4" "$OUT/vert_s3.mp4" "712:360:0:50" -0.20 1.12

# s4 梁静茹《燕尾蝶》— B站修复 1080p，底部歌词
bash "$VF" "$RAW/s4_liangjingru_yanweidie.mp4" "$OUT/vert_s4.mp4" "864:920:528:60" -0.18 1.08

# s5 王心凌《Honey》— YT 1080p avex 官方，底部 .com 网址
bash "$VF" "$RAW/s5_wangxinling_honey.mp4" "$OUT/vert_s5.mp4" "864:920:528:60" -0.16 1.10

# s6 张韶涵《That Girl》— YT 1080p 官方，底部 like no one else 烧字
bash "$VF" "$RAW/s6_zhangshaohan_thatgirl.mp4" "$OUT/vert_s6.mp4" "864:920:528:60" -0.20 1.08

echo "== vfill 6/7 done. s7 待新源 =="
ls -la "$OUT"
