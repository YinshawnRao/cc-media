#!/usr/bin/env bash
# 周传雄「小刚」footage prep：output-seek 精确切窗(chorus-PRE 起,使副歌落在 swell) → 调色(小刚色温弧) → delogo去角标 → vfill letterbox 保原比例。
# 色温弧(倒数5→1): #5挽留 暖sepia → #4失落 冷灰 → #3纯情 蓝暮 → #2心动 金色异域 → #1名片 明亮少年(finale最亮)。
# crop 全宽横带去烧词/URL；角落 logo 用 delogo(hasa两顶角 / peizhe左上缩略图)。
set -uo pipefail
cd /Users/yinshawnrao/explorer/cc-media/sandbox/zhouchuanxiong-xiaogang
VF=../../tools/video/vfill.sh

# prep <key> <src> <win> <len> <crop(letterbox全宽带)> <gradevf(含delogo)> <vfill_br>
prep () {
  local key=$1 src=$2 win=$3 len=$4 crop=$5 grade=$6 br=$7
  echo "=== $key: cut(output-seek win=$win len=$len) + grade ==="
  ffmpeg -v error -i "$src" -ss "$win" -t "$len" -vf "$grade" \
    -c:v libx264 -preset veryfast -crf 18 -g 30 -keyint_min 30 -c:a aac -b:a 192k raw/${key}_pre.mp4 -y
  echo "=== $key: vfill letterbox crop=$crop ==="
  bash "$VF" raw/${key}_pre.mp4 clips/vert_${key}.mp4 "$crop" "$br" 1.0
}

# 倒数 5→1。win=chorus-PRE(PRE=voice+7.2)；len=PRE+SHOW+TAIL+margin。
# ---- #5 舍不得你走 (挽留/暖sepia) src 官方DVD 1920x1080, chorus"舍不得让你走"~98, 裁底烧词(y830+) ----
prep shebude  raw/src_shebude.mp4  73.4  71  "1920:825:0:0" \
  "eq=brightness=0.02:saturation=0.82:contrast=1.04,colorbalance=rm=0.06:rh=0.04:gm=0.01:bm=-0.06:bh=-0.04" -0.16
# ---- #4 风干我的悲伤 (失落/冷灰) src 江男1920x1080, **避开 t108-120 的红色引流水印**, 用 chorus2~160(160-215全程副歌, 干净小刚+马), 裁底2行烧词(y830+) ----
prep fenggan  raw/src_fenggan.mp4  133.8 73  "1920:825:0:0" \
  "eq=brightness=-0.01:saturation=0.74:contrast=1.05,colorbalance=rs=-0.03:rm=-0.04:gm=0.0:bm=0.05:bh=0.04" -0.20
# ---- #3 陪着我尽头 (纯情/蓝暮) src 後援會1920x1080, 小刚海边~166, 裁顶缩略图(y≤220)+裁底2行URL/QR(y≥890) → 薄带 ----
prep peizhe   raw/src_peizhe.mp4   138.8 74  "1920:660:0:225" \
  "eq=brightness=0.02:saturation=0.86:contrast=1.06,colorbalance=rs=-0.04:rm=-0.05:bm=0.08:bh=0.07:bs=0.05" -0.22
# ---- #2 吉普赛情人 (心动/金色异域) src B站480p, 絲路造型~118, 裁顶水印(y0-90), 提亮(SD) ----
prep jipu     raw/src_jipu.mp4     90.2  74  "720:390:0:90" \
  "eq=brightness=0.05:saturation=1.07:contrast=1.05,colorbalance=rm=0.08:rh=0.05:gm=0.02:bm=-0.08:bh=-0.05" -0.16
# ---- #1 哈萨雅琪 (名片/明亮 finale) src 台版LD1470x1080, chorus~126, delogo两顶角(奇歌伴唱TL/@DAVE2013 TR), 裁底烧词(y700+, 保头) ----
# delogo 实测坐标(源1470x1080): 奇歌伴唱 x135-400 y95-340(中偏左,非角); @DAVE2013 x1065-1375 y255-345。
prep hasa     raw/src_hasa.mp4     99.1  77  "1470:690:0:0" \
  "delogo=x=130:y=90:w=278:h=258:show=0,delogo=x=1058:y=250:w=324:h=100:show=0,eq=brightness=0.05:saturation=1.05:contrast=1.03,colorbalance=rm=0.04:rh=0.03:gm=0.01:bm=-0.04:bh=-0.03" -0.12

echo "=== BEDS (intro=shebude柔 / outro=hasa哈萨雅琪finale) ==="
ffmpeg -v error -i raw/src_shebude.mp4 -ss 95 -t 34 -vn \
  -af "aresample=48000,loudnorm=I=-15:TP=-1.5:LRA=11" -ac 2 audio/intro_bed.wav -y
ffmpeg -v error -i raw/src_hasa.mp4 -ss 126 -t 34 -vn \
  -af "aresample=48000,loudnorm=I=-15:TP=-1.5:LRA=11" -ac 2 audio/outro_bed.wav -y

echo "=== PREP ALL DONE ==="
for k in shebude fenggan peizhe jipu hasa; do
  printf "%-9s " $k; ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x clips/vert_${k}.mp4
  printf "  dur="; ffprobe -v error -show_entries format=duration -of csv=p=0 clips/vert_${k}.mp4
done