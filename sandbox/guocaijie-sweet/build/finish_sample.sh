#!/usr/bin/env bash
# 样片渲染(-w1 重试, --sdr) + mux master + QA。本机 GPU 截帧随机崩 → 重试直到完整。
P=/Users/yinshawnrao/explorer/cc-media/sandbox/guocaijie-sweet
HF=$P/hf; RAW=$P/renders/sample_raw.mp4; OUT=$P/renders/guocaijie-sample.mp4
MASTER=$HF/master_sample.wav; TARGET=86.5
mkdir -p "$P/renders" "$P/qa"

ok=0
for n in $(seq 1 8); do
  echo "===== RENDER ATTEMPT $n ====="
  pkill -9 -f "hyperframes" 2>/dev/null; pkill -9 -f "Chrome.*headless" 2>/dev/null; pkill -9 -f chrome_crashpad 2>/dev/null
  sleep 2; rm -f "$RAW" 2>/dev/null
  ( cd "$HF" && npx --yes hyperframes@0.6.47 render "$HF" --output "$RAW" --sdr -w 1 ) >/tmp/gcj_render.log 2>&1
  if [ -f "$RAW" ]; then
    d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$RAW" 2>/dev/null)
    good=$(awk -v d="${d:-0}" -v t="$TARGET" 'BEGIN{print (d>=t)?1:0}')
    if [ "$good" = "1" ]; then echo "RENDER OK attempt $n dur=$d"; ok=1; break; fi
    echo "attempt $n incomplete dur=${d:-none}"
  else echo "attempt $n no output"; fi
  tr '\r' '\n' < /tmp/gcj_render.log | grep -oE "(Streaming|Capturing) frame [0-9]+/[0-9]+" | tail -1
done
[ "$ok" = "1" ] || { echo "RENDER FAILED after retries"; tail -20 /tmp/gcj_render.log; exit 1; }

echo "===== MUX (no -shortest; video drives length) ====="
ffmpeg -v error -i "$RAW" -i "$MASTER" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k "$OUT" -y
echo "final: $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")s"
ffprobe -v error -select_streams v -show_entries stream=width,height,avg_frame_rate -of default=noprint_wrappers=1 "$OUT"
ffprobe -v error -select_streams a -show_entries stream=channels,sample_rate -of default=noprint_wrappers=1 "$OUT"

echo "===== QA audio ====="
echo "[silencedetect >1s @-35dB]"
ffmpeg -i "$OUT" -af silencedetect=n=-35dB:d=1 -f null - 2>&1 | grep -E "silence_(start|end|duration)" || echo "  none"
echo "[volumedetect 旁白段 t8-30]"; ffmpeg -ss 8 -t 22 -i "$OUT" -af volumedetect -f null - 2>&1 | grep mean_volume
echo "[volumedetect 副歌展示段 t56-82]"; ffmpeg -ss 56 -t 26 -i "$OUT" -af volumedetect -f null - 2>&1 | grep mean_volume

echo "===== QA frames ====="
for t in 0 2 7 13 19 25 31 37 44 51 58 66 74 80 85; do
  ffmpeg -v error -ss $t -i "$OUT" -frames:v 1 "$P/qa/f_$(printf '%03d' $t).jpg" -y
done
echo "QA frames written to $P/qa"
echo "DONE -> $OUT"
