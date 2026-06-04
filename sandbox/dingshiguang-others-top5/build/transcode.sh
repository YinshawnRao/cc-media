#!/usr/bin/env bash
cd /Users/yinshawnrao/explorer/cc-media/sandbox/dingshiguang-others-top5
mkdir -p raw_h264
tc(){ ffmpeg -v error -i "$1" -an -c:v libx264 -preset veryfast -crf 18 -r 30 -g 30 -keyint_min 30 -pix_fmt yuv420p "$2" -y && echo "OK $(basename $2)"; }
tc raw/probe/s1_xinsuan_bi_redbull.mp4 raw_h264/s1_xinsuan_redbull.mp4
tc raw/probe/s2_catherine_bi.mp4       raw_h264/s2_catherine.mp4
tc raw/probe/s4_lvgu_yt_lunar.mkv      raw_h264/s4_lvgu.mp4
tc raw/probe/s5_fengci_yt_mv.webm      raw_h264/s5_fengci.mp4
tc "$(find raw/probe -name 's3_2g4e_hq*'|head -1)" raw_h264/s3_ailaiguo.mp4
echo TRANSCODE_ALL_DONE
