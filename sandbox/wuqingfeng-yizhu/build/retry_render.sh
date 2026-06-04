#!/usr/bin/env bash
# HyperFrames 在本机 GPU 截帧不稳定（随机崩）。自动重试直到产出完整片。
HF=/Users/yinshawnrao/explorer/cc-media/sandbox/wuqingfeng-yizhu/hf
OUT=/Users/yinshawnrao/explorer/cc-media/sandbox/wuqingfeng-yizhu/renders/full_raw.mp4
TARGET=231.0
cd "$HF"
for n in $(seq 1 10); do
  echo "===== ATTEMPT $n ====="
  pkill -9 -f "hyperframes" 2>/dev/null; pkill -9 -f "Chrome.*headless" 2>/dev/null; pkill -9 -f chrome_crashpad 2>/dev/null
  sleep 3
  rm -f "$OUT" 2>/dev/null
  npx --yes hyperframes@0.6.47 render "$HF" --output "$OUT" --sdr -w 1 >/tmp/wqf_render_attempt.log 2>&1
  if [ -f "$OUT" ]; then
    d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT" 2>/dev/null)
    ok=$(awk -v d="${d:-0}" -v t="$TARGET" 'BEGIN{print (d>=t)?1:0}')
    if [ "$ok" = "1" ]; then echo "SUCCESS attempt $n: dur=$d"; exit 0; fi
    echo "attempt $n incomplete: dur=${d:-none}"
  else
    echo "attempt $n: no output"
  fi
  tr '\r' '\n' < /tmp/wqf_render_attempt.log | grep -oE "(Streaming|Capturing) frame [0-9]+/[0-9]+" | tail -1
done
echo "EXHAUSTED 10 attempts without complete render"
exit 1