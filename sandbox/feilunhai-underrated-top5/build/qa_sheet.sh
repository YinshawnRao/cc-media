#!/usr/bin/env bash
# Extract QA contact sheets from the final muxed video.
set -euo pipefail
cd /Users/yinshawnrao/explorer/cc-media/sandbox/feilunhai-underrated-top5
V=renders/feilunhai-underrated-top5.mp4
mkdir -p qa/final
grab(){ ffmpeg -v error -ss "$2" -i "$V" -frames:v 1 -vf scale=300:-1 "qa/final/$1.png" -y; }

# cover / hook / bridge / cards / showcases / outro / cta
grab a_cover 2
grab a_hook 9
grab a_bridge 17
grab b_p5_card 27
grab b_p5_show 60
grab c_p4_card 82
grab c_p4_show 110
grab d_p3_card 138
grab d_p3_show 165
grab e_p2_card 188
grab e_p2_show 215
grab f_p1_card 240
grab f_p1_show 270
grab g_outro 300
grab g_cta 309

cd qa/final
ffmpeg -v error -i a_cover.png -i a_hook.png -i a_bridge.png -i b_p5_card.png -i b_p5_show.png \
  -filter_complex hstack=inputs=5 row1.png -y
ffmpeg -v error -i c_p4_card.png -i c_p4_show.png -i d_p3_card.png -i d_p3_show.png -i e_p2_card.png \
  -filter_complex hstack=inputs=5 row2.png -y
ffmpeg -v error -i e_p2_show.png -i f_p1_card.png -i f_p1_show.png -i g_outro.png -i g_cta.png \
  -filter_complex hstack=inputs=5 row3.png -y
ffmpeg -v error -i row1.png -i row2.png -i row3.png -filter_complex vstack=inputs=3 SHEET.png -y
echo "wrote qa/final/SHEET.png"
