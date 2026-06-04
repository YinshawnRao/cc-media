#!/usr/bin/env bash
# 渲染全片 12 块（-c 单块、--sdr、崩则重试）→ concat → mux master_full.wav。
HF=/Users/yinshawnrao/explorer/cc-media/sandbox/linxi-faye-fengshen/hf_full
PROJ=/Users/yinshawnrao/explorer/cc-media/sandbox/linxi-faye-fengshen
cd "$HF" || exit 1
BLOCKS="intro s10 s9 s8 s7 s6 s5 s4 s3 s2 s1 outro"
mkdir -p renders; : > renders/concat.txt
for b in $BLOCKS; do
  target=$(python3 -c "import json;print(json.load(open('blocks.json'))['durs']['$b'])")
  ok=0
  for i in 1 2 3 4 5; do
    pkill -9 -f "Google Chrome for Testing" 2>/dev/null
    pkill -9 -f hyperframes 2>/dev/null
    sleep 1
    rm -f "renders/$b.mp4"
    npx --yes hyperframes@0.6.47 render -c "$b.html" --output "renders/$b.mp4" --sdr -w auto >/dev/null 2>&1
    d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "renders/$b.mp4" 2>/dev/null || echo 0)
    ok=$(python3 -c "print(1 if abs(float('${d:-0}' or 0)-$target)<1.3 else 0)" 2>/dev/null || echo 0)
    echo "block $b attempt $i dur=$d target=$target ok=$ok"
    [ "$ok" = "1" ] && break
  done
  if [ "$ok" != "1" ]; then echo "=== BLOCK $b FAILED — trying -w1 ==="
    for i in 1 2; do
      pkill -9 -f "Google Chrome for Testing" 2>/dev/null; sleep 1; rm -f "renders/$b.mp4"
      npx --yes hyperframes@0.6.47 render -c "$b.html" --output "renders/$b.mp4" --sdr -w 1 >/dev/null 2>&1
      d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "renders/$b.mp4" 2>/dev/null || echo 0)
      ok=$(python3 -c "print(1 if abs(float('${d:-0}' or 0)-$target)<1.3 else 0)" 2>/dev/null || echo 0)
      echo "block $b w1 attempt $i dur=$d ok=$ok"; [ "$ok" = "1" ] && break
    done
  fi
  [ "$ok" != "1" ] && { echo "FATAL: block $b unrenderable"; exit 1; }
  echo "file '$b.mp4'" >> renders/concat.txt
done
echo "=== concat ==="
ffmpeg -v error -f concat -safe 0 -i renders/concat.txt -c copy renders/full_video.mp4 -y 2>/dev/null \
 || ffmpeg -v error -f concat -safe 0 -i renders/concat.txt -c:v libx264 -crf 18 -r 30 -pix_fmt yuv420p renders/full_video.mp4 -y
echo "=== mux master ==="
ffmpeg -v error -i renders/full_video.mp4 -i "$PROJ/master_full.wav" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest "$PROJ/renders/linxi-faye-fengshen-full.mp4" -y
echo "DONE:"; ffprobe -v error -show_entries format=duration:stream=codec_name,width,height -of default=noprint_wrappers=1 "$PROJ/renders/linxi-faye-fengshen-full.mp4"
