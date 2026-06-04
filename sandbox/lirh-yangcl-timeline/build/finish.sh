#!/usr/bin/env bash
# 渲染完成后：mux 我们的 master.wav 覆盖 HyperFrames 压平后的音轨，并生成 QA 资源。
set -euo pipefail
cd "$(dirname "$0")/.."

RAW="hf/renders/full_raw.mp4"
OUT="renders/lirh-yangcl-timeline.mp4"
MASTER="hf/master.wav"

mkdir -p renders qa_frames

[ -f "$RAW" ] || { echo "raw render not found: $RAW"; exit 1; }
[ -f "$MASTER" ] || { echo "master.wav missing"; exit 1; }

echo "[mux] writing $OUT"
ffmpeg -v error -i "$RAW" -i "$MASTER" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest "$OUT" -y

echo "[probe] final video"
ffprobe -v error -select_streams v -show_entries stream=width,height,duration,avg_frame_rate -of default=noprint_wrappers=1 "$OUT"
ffprobe -v error -select_streams a -show_entries stream=channels,sample_rate,duration -of default=noprint_wrappers=1 "$OUT"

echo "[QA] silence + volume"
ffmpeg -i "$OUT" -af silencedetect=n=-35dB:d=1 -f null - 2>&1 | grep -E "silence_(start|end|duration)" || echo "  no silences"
ffmpeg -i "$OUT" -af volumedetect -f null - 2>&1 | grep -E "(mean|max)_volume"

echo "[QA] frames (cover, intro, each song key moments, outro)"
# 关键时刻抽帧
declare -a TIMES=(
  "0:cover"
  "8:intro_hook"
  "20:s1_xfgz_enter"
  "45:s1_xfgz_chorus"
  "90:s2_guanzhong_enter"
  "120:s2_guanzhong_chorus"
  "160:s3_manman_enter"
  "190:s3_manman_chorus"
  "230:s4_xianchou_enter"
  "260:s4_xianchou_chorus"
  "300:s5_xingxing_enter"
  "350:s5_xingxing_finale"
  "385:outro"
)
for entry in "${TIMES[@]}"; do
  t="${entry%%:*}"; name="${entry##*:}"
  ffmpeg -v error -ss "$t" -i "$OUT" -frames:v 1 "qa_frames/${name}_t${t}.png" -y
  echo "  qa_frames/${name}_t${t}.png"
done

echo "[done] $OUT"
ls -la "$OUT"
