#!/bin/bash
# 渲染完后：mux master.wav 覆盖音轨，得到成片，并抽多帧 QA contact sheet。
set -e
cd /Users/yinshawnrao/explorer/cc-media/sandbox/4d3x-kuaige-pk/hf
SLUG="4d3x-kuaige-pk"

# mux: 替换 HF 内部归一化压平后的音轨，用预混 master.wav
ffmpeg -v error -i renders/full_raw.mp4 -i master.wav \
  -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest \
  "renders/${SLUG}.mp4" -y

echo "== final mp4 =="
ls -la "renders/${SLUG}.mp4"
ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate,duration,channels,sample_rate \
  -of default=nw=1 "renders/${SLUG}.mp4"

# QA: 抽 12 帧 (每 ~32s 一帧 覆盖全片 6:30) 拼 contact sheet
QA=../qa_frames/final
mkdir -p "$QA"
for i in 1 2 3 4 5 6 7 8 9 10 11 12; do
  t=$(echo "scale=2; $i * 32" | bc)
  ffmpeg -v error -ss "$t" -i "renders/${SLUG}.mp4" -frames:v 1 \
    "$QA/f$(printf %02d $i)_t${t}s.jpg" -y
done

# 拼 3×4 contact sheet
ffmpeg -v error \
  -i "$QA/f01_t32.00s.jpg" -i "$QA/f02_t64.00s.jpg" -i "$QA/f03_t96.00s.jpg" -i "$QA/f04_t128.00s.jpg" \
  -i "$QA/f05_t160.00s.jpg" -i "$QA/f06_t192.00s.jpg" -i "$QA/f07_t224.00s.jpg" -i "$QA/f08_t256.00s.jpg" \
  -i "$QA/f09_t288.00s.jpg" -i "$QA/f10_t320.00s.jpg" -i "$QA/f11_t352.00s.jpg" -i "$QA/f12_t384.00s.jpg" \
  -filter_complex "[0][1][2][3]hstack=4[r1];[4][5][6][7]hstack=4[r2];[8][9][10][11]hstack=4[r3];[r1][r2][r3]vstack=3,scale=2160:-1[out]" \
  -map "[out]" "$QA/contact.jpg" -y
echo "== contact sheet =="
ls -la "$QA/contact.jpg"

# 音频检查
echo ""
echo "== silencedetect (>1s @ -35dB) =="
ffmpeg -i "renders/${SLUG}.mp4" -af silencedetect=n=-35dB:d=1 -f null - 2>&1 | grep silence_duration | head -5

echo ""
echo "== volumedetect (整片) =="
ffmpeg -i "renders/${SLUG}.mp4" -af volumedetect -f null - 2>&1 | grep -E "(mean_volume|max_volume)"

# 抽测：旁白段（t=10s 介于 intro 中）vs 副歌展示段（t=55s 在 s1 chorus 期）的音量对比
echo ""
echo "== 旁白段 (t=10 期 4s) vs 副歌展示段 (t=55 期 4s) =="
ffmpeg -ss 10 -t 4 -i "renders/${SLUG}.mp4" -af volumedetect -f null - 2>&1 | grep mean_volume
ffmpeg -ss 55 -t 4 -i "renders/${SLUG}.mp4" -af volumedetect -f null - 2>&1 | grep mean_volume

echo ""
echo "== DONE. 成片: renders/${SLUG}.mp4 =="
