#!/usr/bin/env bash
# 场景 b-roll → 1080×1920 cover-crop，按 part 拼蒙太奇（硬切，快切感）。
# 比各段 scene_dur 留 +富余，供 build_html 做交叉淡化重叠(消除段落黑档)。
set -euo pipefail
cd /Users/yinshawnrao/explorer/cc-media/sandbox/zsh-gaokao-mazu
SR=scene_raw; T=clips_seg/tmp; mkdir -p "$T"
enc=(-c:v libx264 -preset veryfast -r 30 -g 30 -keyint_min 30 -pix_fmt yuv420p -an)
COVER='scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,format=yuv420p'

cutv () { ffmpeg -v error -ss "$2" -i "$SR/$1.mp4" -t "$3" -vf "$COVER" "${enc[@]}" "$T/$4.mp4" -y; }
concat () {
  local out="$1"; shift
  : > "$T/list_$out.txt"
  for c in "$@"; do echo "file '$(pwd)/$T/$c.mp4'" >> "$T/list_$out.txt"; done
  ffmpeg -v error -f concat -safe 0 -i "$T/list_$out.txt" -c copy "clips_seg/$out.mp4" -y
  echo "$out.mp4: $(ffprobe -v error -show_entries format=duration -of csv=p=0 clips_seg/$out.mp4)s"
}

# ---- Part1 破茧 考前冲刺 (~15s)：晚自习→刷题→跑操 ----
cutv p1_classroom 2  5.0 p1a
cutv p1_write     1  5.0 p1b
cutv run_track    2  5.0 p1c
concat scene_p1 p1a p1b p1c

# ---- Part2 篇章 赶考新闻感 (~23.5s)：雨奔跑→雨街→警灯→校门→家长等待 ----
cutv p2_rainrun   6  4.7 p2a
cutv p2_rainstreet 0 4.7 p2b
cutv p2_police    4  4.7 p2c
cutv school_gate  1  4.7 p2d
cutv p2_waiting   1  4.7 p2e
concat scene_p2 p2a p2b p2c p2d p2e

# ---- Part3 淋雨一直走 低谷坚持 (~20s)：雨夜剪影→撑伞前行→雨滴→背影(转晨光) ----
cutv p3_rainsil   3  5.0 p3a
cutv p3_umbrella  4  5.0 p3b
cutv p3_raindrop  6  5.0 p3c
cutv p3_backwalk  2  5.0 p3d
concat scene_p3 p3a p3b p3c p3d

# ---- Part4 隐形的翅膀 青春回忆 (~24.5s)：作文纸→抛帽剪影→抛帽→蓝天→奔向阳光 ----
cutv p4_writing   2  4.9 p4a
cutv p4_capwave   1  4.9 p4b
cutv p4_capthrow  2  4.9 p4c
cutv p4_sky       1  4.9 p4d
cutv p4_runsun    3  4.9 p4e
concat scene_p4 p4a p4b p4c p4d p4e

# ---- 张韶涵舞台剪影 clip（破茧觅光直拍，居中裁切避水印+烧词；加长铺满 outro）----
ffmpeg -v error -ss 58 -i raw/s1_pojian.mp4 -t 22 -vf "crop=576:880:672:30,scale=1080:1920,setsar=1,format=yuv420p" "${enc[@]}" clips_seg/zsh_stage.mp4 -y
echo "zsh_stage.mp4: $(ffprobe -v error -show_entries format=duration -of csv=p=0 clips_seg/zsh_stage.mp4)s"

# ---- 开场快切蒙太奇 (~13s)：校门→考生奔跑→家长等待→张韶涵舞台 ----
cutv school_gate  3 3.2 i1
cutv p2_rainrun   12 3.2 i2
cutv p2_waiting   2 3.2 i3
ffmpeg -v error -ss 74 -i raw/s1_pojian.mp4 -t 3.4 -vf "crop=576:880:672:30,scale=1080:1920,setsar=1,format=yuv420p" "${enc[@]}" "$T/i4.mp4" -y
concat scene_intro i1 i2 i3 i4

echo "SCENES BUILD DONE"
ls -la clips_seg/scene_*.mp4 clips_seg/zsh_stage.mp4 | awk '{print $5, $9}'
