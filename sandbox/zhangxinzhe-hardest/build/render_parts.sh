#!/usr/bin/env bash
# 渲染 partA/partB（各 <240s 且 ≤4 video）-w1 + retry 兜随机GPU崩，concat 成 full_raw.mp4，mux master.wav。
cd /Users/yinshawnrao/explorer/cc-media/sandbox/zhangxinzhe-hardest
mkdir -p renders
render_one(){ local comp="$1" out="$2" tgt="$3"; local i d
  for i in $(seq 1 8); do
    pkill -9 -f "Chrome.*headless" 2>/dev/null; pkill -9 -f "hyperframes" 2>/dev/null; pkill -9 -f chrome_crashpad 2>/dev/null; sleep 2
    echo "=== $comp attempt $i → $out ==="
    rm -f "$out" 2>/dev/null
    npx --yes hyperframes@0.6.69 render -c "$comp" --output "$out" --sdr -w 1 > "renders/log_$(basename $out .mp4)_$i.log" 2>&1
    d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$out" 2>/dev/null | cut -d. -f1)
    echo "  $comp attempt $i: dur=${d:-none}s (target ~${tgt}s)"
    if [ -n "$d" ] && [ "$d" -ge "$((tgt-3))" ]; then echo "OK $out $d"; return 0; fi
    tr '\r' '\n' < "renders/log_$(basename $out .mp4)_$i.log" | grep -oE "(Streaming|Capturing) frame [0-9]+/[0-9]+" | tail -1
  done
  echo "FAIL $out"; return 1
}
render_one partA.html renders/partA.mp4 129 || exit 1
render_one partB.html renders/partB.mp4 181 || exit 1
echo "=== concat ==="
printf "file 'partA.mp4'\nfile 'partB.mp4'\n" > renders/concat_parts.txt
ffmpeg -v error -f concat -safe 0 -i renders/concat_parts.txt -c copy renders/full_raw.mp4 -y
echo "CONCAT_OK full_raw dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 renders/full_raw.mp4)"
echo "=== mux master.wav ==="
ffmpeg -v error -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/zhangxinzhe-hardest.mp4 -y
echo "FINAL dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 renders/zhangxinzhe-hardest.mp4)"
