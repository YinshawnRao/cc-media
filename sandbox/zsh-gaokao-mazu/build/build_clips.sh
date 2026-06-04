#!/usr/bin/env bash
# 4 首副歌 → 1080×1920 (各自 crop 处理烧字/水印)。长度=SHOW+2 覆盖 TAIL 避免段落黑档。
set -euo pipefail
cd /Users/yinshawnrao/explorer/cc-media/sandbox/zsh-gaokao-mazu
enc=(-c:v libx264 -preset veryfast -r 30 -g 30 -keyint_min 30 -pix_fmt yuv420p -an)
LB () { # in start dur crop out  —— letterbox 保原比例
  ffmpeg -v error -i "$1" -ss "$2" -t "$3" -filter_complex \
   "[0:v]crop=$4,split=2[bg][fg];[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=28,eq=brightness=-0.30:saturation=1.05[bgb];[fg]scale=1080:-2[fgs];[bgb][fgs]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]" \
   -map "[v]" "${enc[@]}" "$5" -y
}
# s1 破茧 动画MV letterbox (裁上黑边 + 底部烧词「武魂…」y880 + 斗罗大陆logo y850 → 内容带收到 y145-845)
LB raw/s1_pojian_mv.mp4 52 29 "1920:700:0:145" clips_seg/song_s1.mp4
# s3 淋雨 官方MV letterbox 全幅
LB raw/s3_linyu_yt.mkv 58 29 "1920:1080:0:0" clips_seg/song_s3.mp4
# s2 篇章 竖屏直拍 裁顶水印
ffmpeg -v error -i raw/s2_pianzhang.mp4 -ss 68 -t 30 -vf "crop=1080:1812:0:100,scale=1080:1920,setsar=1,format=yuv420p" "${enc[@]}" clips_seg/song_s2.mp4 -y
# s4 隐形 官方HD MV(4:3) 居中裁切 裁底烧词
ffmpeg -v error -i raw/s4_yinxing_hd.mkv -ss 80 -t 32 -vf "crop=560:1000:440:18,scale=1080:1920,setsar=1,format=yuv420p" "${enc[@]}" clips_seg/song_s4.mp4 -y
for n in 1 2 3 4; do echo "song_s$n: $(ffprobe -v error -show_entries format=duration -of csv=p=0 clips_seg/song_s$n.mp4)s"; done
