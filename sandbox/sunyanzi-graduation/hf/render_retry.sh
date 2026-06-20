#!/usr/bin/env bash
# 本机 GPU 截帧随机崩 -> -w1 + 重试循环（见 hyperframes-render-flaky-gpu 经验）
cd "$(dirname "$0")"
OUT="${1:-renders/sample_raw.mp4}"
MIN="${2:-134}"
mkdir -p renders
rm -f "$OUT" 2>/dev/null
for i in 1 2 3 4 5 6 7 8; do
  echo "=== render attempt $i ($OUT, min ${MIN}s) ==="
  npx --yes hyperframes@0.6.47 render --output "$OUT" --sdr -w1 > "renders/log_$i.log" 2>&1
  if [ -f "$OUT" ] && [ "$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT" 2>/dev/null | cut -d. -f1)" -ge "$MIN" ] 2>/dev/null; then
    echo "=== SUCCESS attempt $i: $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")s ==="; exit 0
  fi
  echo "attempt $i incomplete; tail:"; tail -5 "renders/log_$i.log"; rm -f "$OUT" 2>/dev/null
done
echo "=== ALL ATTEMPTS FAILED ==="; exit 1
