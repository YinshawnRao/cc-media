#!/usr/bin/env bash
# 全片渲染(-w1重试,--sdr) + mux master + QA抽帧。本机GPU截帧随机崩→重试。
P=/Users/yinshawnrao/explorer/cc-media/sandbox/guocaijie-sweet
HF=$P/hf; RAW=$P/renders/full_raw.mp4; OUT=$P/renders/guocaijie-sweet-full.mp4
MASTER=$HF/master.wav; TARGET=306.0
mkdir -p "$P/renders" "$P/qaf"; rm -f "$P/qaf"/*.jpg 2>/dev/null

ok=0
for n in $(seq 1 12); do
  echo "===== RENDER ATTEMPT $n ====="
  pkill -9 -f "hyperframes" 2>/dev/null; pkill -9 -f "Chrome.*headless" 2>/dev/null; pkill -9 -f chrome_crashpad 2>/dev/null
  sleep 2; rm -f "$RAW" 2>/dev/null
  ( cd "$HF" && npx --yes hyperframes@0.6.47 render "$HF" --output "$RAW" --sdr -w 1 ) >/tmp/gcj_full_render.log 2>&1
  if [ -f "$RAW" ]; then
    d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$RAW" 2>/dev/null)
    good=$(awk -v d="${d:-0}" -v t="$TARGET" 'BEGIN{print (d>=t)?1:0}')
    if [ "$good" = "1" ]; then echo "RENDER OK attempt $n dur=$d"; ok=1; break; fi
    echo "attempt $n incomplete dur=${d:-none}"
  else echo "attempt $n no output"; fi
  tr '\r' '\n' < /tmp/gcj_full_render.log | grep -oE "(Streaming|Capturing) frame [0-9]+/[0-9]+" | tail -1
done
[ "$ok" = "1" ] || { echo "RENDER FAILED"; tail -15 /tmp/gcj_full_render.log; exit 1; }

echo "===== MUX ====="
ffmpeg -v error -i "$RAW" -i "$MASTER" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k "$OUT" -y
echo "final: $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")s  $(ffprobe -v error -select_streams v -show_entries stream=width,height,avg_frame_rate -of csv=p=0 "$OUT")  a:$(ffprobe -v error -select_streams a -show_entries stream=channels -of csv=p=0 "$OUT")ch"

echo "===== QA audio ====="
ffmpeg -i "$OUT" -af silencedetect=n=-35dB:d=1.5 -f null - 2>&1 | grep -E "silence_(start|duration)" || echo "  no >1.5s silence"

echo "===== QA frames ====="
for t in 0 2 8 14 20 30 48 64 72 98 116 124 150 172 180 205 228 238 268 292 302; do
  ffmpeg -v error -ss $t -i "$OUT" -frames:v 1 "$P/qaf/f_$(printf '%03d' $t).jpg" -y
done
echo "DONE -> $OUT"
