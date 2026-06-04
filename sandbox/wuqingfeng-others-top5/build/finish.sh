#!/usr/bin/env bash
# 渲染后：mux 预混 master.wav（HF 压平音频动态，必须后期覆盖）+ QA 抽帧/音频。
set -e
P=/Users/yinshawnrao/explorer/cc-media/sandbox/wuqingfeng-others-top5
cd "$P"
RAW=hf/renders/full_raw.mp4
FINAL=renders/wuqingfeng-others-top5.mp4
mkdir -p renders qa/final
echo "=== mux master.wav over render ==="
ffmpeg -v error -i "$RAW" -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest "$FINAL" -y
echo "final: $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$FINAL")s  $(ffprobe -v error -select_streams v:0 -show_entries stream=width,height,codec_name,color_space -of csv=p=0 "$FINAL")"
echo "=== QA frames ==="
declare -A T=( [cover]=0.5 [hook]=7.5 [s1card]=23 [s1chorus]=42 [s2card]=57.5 [s2chorus]=78
  [s3card]=95 [s3chorus]=116 [s4card]=139.5 [s4chorus]=160 [s5card]=182.5 [s5chorus]=205 [outro]=229 )
for k in "${!T[@]}"; do
  ffmpeg -v error -ss "${T[$k]}" -i "$FINAL" -frames:v 1 "qa/final/$k.png" -y
done
echo "frames written to qa/final/"
echo "=== final audio QA ==="
ffmpeg -hide_banner -nostats -i "$FINAL" -af silencedetect=n=-35dB:d=1.2 -f null - 2>&1 | grep -E 'silence_(start|duration)' || echo "no silences >1.2s"
