#!/usr/bin/env bash
# 后期 mux + QA: 用 master.wav 覆盖 HF 输出的音轨（HF 会归一化压平动态），
# 再抽帧 contact sheet + silencedetect/volumedetect QA.
# 预期 cwd = sandbox/zhang-shaohan-7albums.
set -euo pipefail

RAW="hf/renders/full_raw.mp4"
MASTER="hf/master.wav"
OUT="hf/renders/zhang-shaohan-7albums.mp4"
QA="qa/final"

if [ ! -f "$RAW" ]; then echo "missing $RAW"; exit 1; fi
if [ ! -f "$MASTER" ]; then echo "missing $MASTER"; exit 1; fi
mkdir -p "$QA"

echo "=== MUX ==="
ffmpeg -y -v warning -i "$RAW" -i "$MASTER" \
  -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest "$OUT"

DUR=$(ffprobe -v error -show_entries format=duration -of default=nokey=1:noprint_wrappers=1 "$OUT")
echo "final dur: ${DUR}s | $(ls -lh "$OUT" | awk '{print $5}')"

echo
echo "=== silencedetect (n=-35dB d=1.5) ==="
ffmpeg -v info -i "$OUT" -af silencedetect=n=-35dB:d=1.5 -f null /dev/null 2>&1 | grep -E "silence_(start|end|duration)" || echo "  no >1.5s silence"

echo
echo "=== volumedetect 全片 ==="
ffmpeg -v info -i "$OUT" -af volumedetect -f null /dev/null 2>&1 | grep -E "mean_volume|max_volume"

echo
echo "=== volumedetect 每段 (旁白/展示对照) ==="
for spec in "intro:0-15" "s1_voice:18-28" "s1_chorus:35-55" "s4_voice:144-152" "s4_chorus:163-180" "s7_voice:271-281" "s7_chorus:290-308" "outro:312-322"; do
  LABEL="${spec%%:*}"
  RANGE="${spec##*:}"
  START="${RANGE%-*}"
  END="${RANGE#*-}"
  DUR_SEG=$((END-START))
  M=$(ffmpeg -v error -ss "$START" -t "$DUR_SEG" -i "$OUT" -af volumedetect -f null /dev/null 2>&1 | grep mean_volume | awk -F'[ :]' '{print $7}')
  echo "  ${LABEL}: mean ${M:-?}dB"
done

echo
echo "=== 抽帧 contact sheet (每 30s 一帧) ==="
ffmpeg -y -v error -i "$OUT" -vf "fps=1/30,scale=240:426,tile=4x3" -frames:v 1 "$QA/contact_sheet.jpg"

# 抽关键帧：开场 t=2/8/15、每首 album_card 出现 t=base/+1.5/chorus_mid，outro t=314
KEY_T=(2 8 15 17 35 55 60 80 102 122 144 164 187 210 230 252 271 295 314 320)
for t in "${KEY_T[@]}"; do
  ffmpeg -y -v error -i "$OUT" -ss "$t" -frames:v 1 "$QA/t${t}s.jpg"
done
echo "frames in: $QA/"
ls "$QA"/

echo
echo "=== final path ==="
echo "$(realpath "$OUT")"
