#!/bin/bash
# 渲染 partA/partB（各 <240s → streaming 开启稳定），retry 容错，concat 成 full_raw.mp4。
cd /Users/yinshawnrao/explorer/cc-media/sandbox/tanyonglin-underrated
mkdir -p renders
render_one(){ local comp="$1" out="$2" tgt="$3"; local i
  for i in $(seq 1 6); do
    pkill -9 -f "Chrome.*headless" 2>/dev/null; pkill -9 -f "hyperframes" 2>/dev/null; sleep 1
    echo "=== $comp attempt $i → $out ==="
    npx hyperframes render -c "$comp" --output "$out" --sdr -w 1 > "renders/log_$(basename $out .mp4)_$i.log" 2>&1
    d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$out" 2>/dev/null | cut -d. -f1)
    echo "  $comp attempt $i: dur=${d:-none}s (target ~${tgt}s)"
    if [ -n "$d" ] && [ "$d" -ge "$((tgt-3))" ]; then echo "OK $out $d"; return 0; fi
    tail -3 "renders/log_$(basename $out .mp4)_$i.log"
  done
  echo "FAIL $out"; return 1
}
render_one partA.html renders/partA.mp4 164 || exit 1
render_one partB.html renders/partB.mp4 126 || exit 1
echo "=== concat ==="
printf "file 'partA.mp4'\nfile 'partB.mp4'\n" > renders/concat_parts.txt
ffmpeg -v error -f concat -safe 0 -i renders/concat_parts.txt -c copy renders/full_raw.mp4 -y
echo "CONCAT_OK full_raw dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 renders/full_raw.mp4)"
