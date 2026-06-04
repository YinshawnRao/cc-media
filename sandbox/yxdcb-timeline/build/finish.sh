#!/usr/bin/env bash
# 渲染完成后：mux master.wav 覆盖 HF 压平音轨 + QA 抽帧 + 导出封面。
set -euo pipefail
cd "$(dirname "$0")/.."
RAW="hf/renders/full_raw.mp4"; OUT="renders/yxdcb-timeline.mp4"; MASTER="master.wav"
mkdir -p renders qa_frames/final
[ -f "$RAW" ] || { echo "raw render not found: $RAW"; exit 1; }
[ -f "$MASTER" ] || { echo "master.wav missing"; exit 1; }

echo "[mux] -> $OUT"
ffmpeg -v error -i "$RAW" -i "$MASTER" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest "$OUT" -y
echo "[probe]"
ffprobe -v error -select_streams v -show_entries stream=width,height,avg_frame_rate -show_entries format=duration -of default=noprint_wrappers=1 "$OUT"
ffprobe -v error -select_streams a -show_entries stream=channels,sample_rate -of default=noprint_wrappers=1 "$OUT"

echo "[QA] silence (no >1.2s)"
ffmpeg -hide_banner -i "$OUT" -af "silencedetect=n=-35dB:d=1.2" -f null - 2>&1 | grep -E "silence_(start|end|duration)" || echo "  none"
echo "[QA] section levels"
for e in "10:intro" "31:s1narr" "62:s1show" "113:s2show" "165:s3show" "215:s4show" "275:s5show" "303:outro"; do
  t="${e%%:*}"; n="${e##*:}"
  m=$(ffmpeg -hide_banner -ss "$t" -t 9 -i "$OUT" -af volumedetect -f null - 2>&1 | grep mean_volume)
  echo "  $n($t) $m"
done

echo "[QA] cover + key frames"
declare -a T=("0:cover" "9:hook" "30:s1_2006_enter" "64:s1_show" "92:s2_2007_enter" "118:s2_show" \
  "150:s3_2013_enter" "172:s3_show" "205:s4_2020_enter" "228:s4_show" "258:s5_2023_enter" "288:s5_show" "305:outro")
for e in "${T[@]}"; do t="${e%%:*}"; n="${e##*:}"; ffmpeg -v error -ss "$t" -i "$OUT" -frames:v 1 "qa_frames/final/${n}_t${t}.png" -y; done

echo "[cover] export frame 0 (no watermark)"
ffmpeg -v error -ss 0 -i "$OUT" -frames:v 1 renders/cover.png -y

echo "[done]"; ls -la "$OUT" renders/cover.png
