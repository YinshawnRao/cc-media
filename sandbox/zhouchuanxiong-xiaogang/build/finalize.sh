#!/usr/bin/env bash
# 渲染后：用预混 master.wav 后期 mux（HyperFrames 会压平动态）→ QA 抽帧 + 音频检测。
set -uo pipefail
cd /Users/yinshawnrao/explorer/cc-media/sandbox/zhouchuanxiong-xiaogang
RAW=hf/renders/full_raw.mp4
OUT=renders/zhouchuanxiong-xiaogang.mp4
mkdir -p renders frames/final
echo "=== raw probe ==="
ffprobe -v error -show_entries format=duration:stream=width,height,codec_name -of default=nw=1 "$RAW" | head
echo "=== MUX master.wav ==="
ffmpeg -v error -i "$RAW" -i hf/master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest "$OUT" -y
echo "muxed -> $OUT  dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")"
echo "=== AUDIO QA: silencedetect (>1.2s) ==="
ffmpeg -v error -i "$OUT" -af "silencedetect=n=-35dB:d=1.2" -f null - 2>&1 | grep -i silence || echo "  no >1.2s silence"
echo "=== AUDIO QA: per-chapter chorus volume (showcase swell) ==="
# full0 abs times: shebude44.7 fenggan102.4 peizhe161.1 jipu220.4 hasa278.8 ; narration shebude28
for tv in "shebude_chorus:46" "fenggan_chorus:104" "peizhe_chorus:163" "jipu_chorus:222" "hasa_chorus:281" "narr_shebude:30"; do
  nm="${tv%%:*}"; t="${tv##*:}"
  v=$(ffmpeg -v error -ss $t -t 5 -i "$OUT" -af volumedetect -f null - 2>&1 | grep mean_volume | sed 's/.*mean_volume: //')
  printf "  %-16s @%ss  mean=%s\n" "$nm" "$t" "$v"
done
echo "=== FRAME QA: extract key moments ==="
# cover1.5 hook8 title18 card#5@22 #5chorus@46 card#4@78 #4ch@104 card#3@135 #3ch@163 card#2@194 #2ch@222 card#1@253 #1ch@281 outro318 recap322 cta336
declare -a F=("cover:1.5" "hook:8" "title:18" "c5card:22.5" "c5show:46" "c4card:78.5" "c4show:104" "c3card:135.5" "c3show:163" "c2card:194.5" "c2show:222" "c1card:253.5" "c1show:281" "outro:318" "recap:323" "cta:337")
for entry in "${F[@]}"; do nm="${entry%%:*}"; t="${entry##*:}"; ffmpeg -v error -ss $t -i "$OUT" -frames:v 1 frames/final/${nm}.png -y; done
echo "=== contact sheets ==="
cd frames/final
ffmpeg -v error -i cover.png -i hook.png -i title.png -i c5card.png -i c4card.png -i c3card.png -i c2card.png -i c1card.png \
  -filter_complex "[0]scale=-1:520[a];[1]scale=-1:520[b];[2]scale=-1:520[c];[3]scale=-1:520[d];[4]scale=-1:520[e];[5]scale=-1:520[f];[6]scale=-1:520[g];[7]scale=-1:520[h];[a][b][c][d][e][f][g][h]hstack=8" sheet_cards.png -y
ffmpeg -v error -i c5show.png -i c4show.png -i c3show.png -i c2show.png -i c1show.png -i outro.png -i recap.png -i cta.png \
  -filter_complex "[0]scale=-1:520[a];[1]scale=-1:520[b];[2]scale=-1:520[c];[3]scale=-1:520[d];[4]scale=-1:520[e];[5]scale=-1:520[f];[6]scale=-1:520[g];[7]scale=-1:520[h];[a][b][c][d][e][f][g][h]hstack=8" sheet_shows.png -y
echo "FINALIZE_DONE -> $OUT"