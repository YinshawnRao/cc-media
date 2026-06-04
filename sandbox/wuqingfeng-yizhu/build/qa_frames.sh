#!/usr/bin/env bash
# QA 抽帧：给定成片 mp4，抽封面/intro/各章转场卡+展示/outro，拼两张 contact sheet。
set -euo pipefail
cd /Users/yinshawnrao/explorer/cc-media/sandbox/wuqingfeng-yizhu
MP4="${1:-renders/full_raw.mp4}"
mkdir -p qa_frames
shot(){ ffmpeg -nostdin -v error -i "$MP4" -ss "$2" -frames:v 1 "qa_frames/$1.png" -y 2>/dev/null; }
# 揭晓卡（VO 期）+ 封面/intro/outro
shot cover 1.0
shot intro 15.0
shot p5_card 38.0
shot p4_card 80.0
shot p3_card 120.0
shot p2_card 162.0
shot p1_card 202.0
shot outro 236.0
# 展示段（footage）
shot p5_show 55.0
shot p4_show 97.0
shot p3_show 138.0
shot p2_show 178.0
shot p1_show 218.0
# sheet A: 封面/intro/转场卡/outro (8)
ffmpeg -nostdin -v error \
 -i qa_frames/cover.png -i qa_frames/intro.png -i qa_frames/p5_card.png -i qa_frames/p4_card.png \
 -i qa_frames/p3_card.png -i qa_frames/p2_card.png -i qa_frames/p1_card.png -i qa_frames/outro.png \
 -filter_complex "[0]scale=300:533[a];[1]scale=300:533[b];[2]scale=300:533[c];[3]scale=300:533[d];[4]scale=300:533[e];[5]scale=300:533[f];[6]scale=300:533[g];[7]scale=300:533[h];[a][b][c][d]hstack=4[r1];[e][f][g][h]hstack=4[r2];[r1][r2]vstack" -frames:v 1 -update 1 qa_frames/SHEET_cards.png -y 2>/dev/null
# sheet B: 5 展示段
ffmpeg -nostdin -v error \
 -i qa_frames/p5_show.png -i qa_frames/p4_show.png -i qa_frames/p3_show.png -i qa_frames/p2_show.png -i qa_frames/p1_show.png \
 -filter_complex "[0]scale=360:640[a];[1]scale=360:640[b];[2]scale=360:640[c];[3]scale=360:640[d];[4]scale=360:640[e];[a][b][c][d][e]hstack=5" -frames:v 1 -update 1 qa_frames/SHEET_shows.png -y 2>/dev/null
echo "QA sheets: qa_frames/SHEET_cards.png  qa_frames/SHEET_shows.png"