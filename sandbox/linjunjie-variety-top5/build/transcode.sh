#!/usr/bin/env bash
# 转 h264 密集关键帧(footage 用) + 抽全长干净 wav(音频用，输出端全解码避免 opus 截断)。
set -e
cd /Users/yinshawnrao/explorer/cc-media/sandbox/linjunjie-variety-top5
mkdir -p raw_h264
vtc(){ ffmpeg -v error -i "$1" -an -c:v libx264 -preset veryfast -crf 18 -r 30 -g 30 -keyint_min 30 -pix_fmt yuv420p "$2" -y && echo "V_OK $(basename "$2")"; }
atc(){ ffmpeg -v error -i "$1" -vn -ac 2 -ar 48000 -c:a pcm_s16le "$2" -y && echo "A_OK $(basename "$2")"; }
vtc raw/s1_shule_bi.mp4       raw_h264/s1.mp4    ; atc raw/s1_shule_bi.mp4       raw/s1.wav
vtc raw/s2_huainian_yt.mp4    raw_h264/s2.mp4    ; atc raw/s2_huainian_yt.mp4    raw/s2.wav
vtc raw/s3_mimi_bi.mp4        raw_h264/s3.mp4    ; atc raw/s3_mimi_bi.mp4        raw/s3.wav
vtc raw/s4_mobanche_yt.mp4    raw_h264/s4.mp4    ; atc raw/s4_mobanche_yt.mp4    raw/s4.wav
vtc raw/s5_womendeai_bi.mp4   raw_h264/s5_bi.mp4 ; atc raw/s5_womendeai_bi.mp4   raw/s5_bi.wav
vtc raw/s5_womendeai_yt.mp4   raw_h264/s5_yt.mp4 ; atc raw/s5_womendeai_yt.mp4   raw/s5_yt.wav
echo TRANSCODE_ALL_DONE
