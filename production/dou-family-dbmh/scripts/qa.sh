#!/usr/bin/env bash
# 成片 QA：抽关键时刻帧 + 音频 silencedetect + volumedetect。
# 用法: bash scripts/qa.sh <final.mp4>
set -euo pipefail
IN="${1:?usage: qa.sh <mp4>}"
mkdir -p frames/qa

# 关键时刻抽帧（每段开头中段尾）
TIMES=(0 6 14 18 22 28 38 50 75 88 100 130 155 168 195 213 230 255 270 285 290 297)
for t in "${TIMES[@]}"; do
  ffmpeg -y -v error -i "$IN" -ss "$t" -frames:v 1 "frames/qa/qa_t${t}.jpg"
done

# 4列拼一张 contact sheet
ffmpeg -y -v error -pattern_type glob -i 'frames/qa/qa_t*.jpg' \
  -filter_complex "scale=270:-1,tile=4x6" -frames:v 1 frames/qa_contact.jpg
echo "wrote frames/qa_contact.jpg"

# 音频 QA
echo "==== silencedetect (any >1s silence)===="
ffmpeg -v info -i "$IN" -af silencedetect=n=-35dB:d=1 -f null - 2>&1 | \
  grep -E 'silence_(start|end|duration)' || echo "✅ no >1s silence"

echo "==== volumedetect ===="
ffmpeg -v info -i "$IN" -af volumedetect -f null - 2>&1 | grep -E '(mean|max)_volume'

# 关键时间窗 RMS：旁白段 vs 展示段
echo "==== chapter section volumes (1s RMS sample) ===="
for label_t in "ch1_voice:42" "ch1_show:60" "ch2_voice:104" "ch2_show:130" "ch3_voice:170" "ch3_show:200" "three:230"; do
  label="${label_t%:*}"; t="${label_t#*:}"
  v=$(ffmpeg -ss "$t" -t 1 -i "$IN" -af volumedetect -f null - 2>&1 | grep mean_volume | awk -F: '{print $NF}' | tr -d ' ')
  printf "  %-12s t=%4ss  mean=%s\n" "$label" "$t" "$v"
done

ls -la "$IN" frames/qa_contact.jpg
