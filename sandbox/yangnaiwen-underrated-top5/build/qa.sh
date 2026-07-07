#!/usr/bin/env bash
# Final QA on the muxed mp4: contact sheets (cover/cards/showcases/outro/cta) + audio.
set -uo pipefail
cd /Users/yinshawnrao/explorer/cc-media/sandbox/yangnaiwen-underrated-top5
V=renders/yangnaiwen-underrated-top5.mp4
mkdir -p probe/qa
echo "=== video info ===" && ffprobe -v error -select_streams v:0 -show_entries stream=width,height,codec_name,r_frame_rate -of default=nw=1 "$V"
echo "dur: $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$V")s"
# Frame grabs: cover(2), each song card(narration) + showcase, transitions, outro, cta
# timeline: intro 0-18.75; p5 19-68(card~24,show~52); p4 68-117(card~74,show~100); p3 117-169(card~123,show~152);
#           p2 169-222(card~176,show~205); p1 222-269(card~228,show~252); outro 269-300(summary~278, cta~292)
i=0
for t in 2 12 24 52 74 100 123 152 176 205 228 252 278 285 292 297; do
  ffmpeg -v error -ss $t -i "$V" -frames:v 1 -vf scale=300:-1 probe/qa/f_$(printf %03d $i)_$t.png -y
  i=$((i+1))
done
# tile into 2 sheets of 8
ffmpeg -v error -i probe/qa/f_000_2.png -i probe/qa/f_001_12.png -i probe/qa/f_002_24.png -i probe/qa/f_003_52.png -i probe/qa/f_004_74.png -i probe/qa/f_005_100.png -i probe/qa/f_006_123.png -i probe/qa/f_007_152.png -filter_complex hstack=8 probe/qa/sheet1.png -y
ffmpeg -v error -i probe/qa/f_008_176.png -i probe/qa/f_009_205.png -i probe/qa/f_010_228.png -i probe/qa/f_011_252.png -i probe/qa/f_012_278.png -i probe/qa/f_013_285.png -i probe/qa/f_014_292.png -i probe/qa/f_015_297.png -filter_complex hstack=8 probe/qa/sheet2.png -y
echo "=== silencedetect (>1s @ -35dB) ===" && ffmpeg -v error -i "$V" -af "silencedetect=n=-35dB:d=1" -f null - 2>&1 | grep -i silence || echo "  none"
echo "=== final loudness (showcases) ==="
for spec in "p5:50" "p4:100" "p3:152" "p2:205" "p1:252"; do
  k=${spec%%:*}; t=${spec#*:}; ffmpeg -v error -ss $t -t 8 -i "$V" /tmp/q_$k.wav -y
  m=$(ffmpeg -i /tmp/q_$k.wav -af volumedetect -f null - 2>&1 | grep mean_volume | awk '{print $5}')
  echo "  $k showcase: $m dB"
done
echo "QA sheets: probe/qa/sheet1.png probe/qa/sheet2.png"
