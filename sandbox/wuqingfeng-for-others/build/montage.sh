#!/usr/bin/env bash
# 概念MV(怪美/年轮/有形)无14s连续特写 → 拼"歌手镜头蒙太奇"。
# 每镜头独立 crop 居中歌手、裁烧字/男配角；音乐在 full_build 取该曲副歌(解耦,慢歌口型微差不可察)。
# daiwozou(Live)/diaole 是实拍同步,不在此(单窗 clips.sh,start==build W)。
set -euo pipefail
cd /Users/yinshawnrao/explorer/cc-media/sandbox/wuqingfeng-for-others
ROOT=/Users/yinshawnrao/explorer/cc-media
VFILL="$ROOT/tools/video/vfill.sh"
mkdir -p clips_seg tmp/mtg

build_montage() {
  local key="$1"; shift
  local parts=("$@")   # 每项: src|start|dur|crop|eq
  local idx=0; local listfile="tmp/mtg/${key}_list.txt"; : > "$listfile"
  for p in "${parts[@]}"; do
    IFS='|' read -r src start dur crop eq <<< "$p"
    local seg="tmp/mtg/${key}_${idx}.mp4" segA="tmp/mtg/${key}_${idx}A.mp4" vert="tmp/mtg/${key}_${idx}V.mp4"
    local VF="-an"; [ -n "$eq" ] && VF="-vf $eq -an"
    # 输出端 seek 精确切, video-only + eq, 密集关键帧
    ffmpeg -nostdin -v error -i "$src" -ss "$start" -t "$dur" $VF \
      -c:v libx264 -preset veryfast -r 30 -g 30 -keyint_min 30 -pix_fmt yuv420p "$seg" -y
    # 附静音轨给 vfill
    ffmpeg -nostdin -v error -f lavfi -t "$dur" -i anullsrc=r=48000:cl=stereo \
      -i "$seg" -map 1:v -map 0:a -c:v copy -c:a aac -shortest "$segA" -y
    bash "$VFILL" "$segA" "$vert" "$crop" "-0.18" "1.03"
    echo "file '${key}_${idx}V.mp4'" >> "$listfile"
    idx=$((idx+1))
  done
  ffmpeg -nostdin -v error -f concat -safe 0 -i "$listfile" -c copy "clips_seg/${key}.mp4" -y
  echo "=== ${key} montage: $(ffprobe -v error -show_entries format=duration -of csv=p=0 clips_seg/${key}.mp4)s ==="
}

# 怪美的(#5): 护士蓝唇 -> 躺姿青枕 -> 彩带(跳过黄烟,end on hero)。全蔡依林特写,裁底部烧字。
build_montage guaimei \
  "raw/guaimei_yt.mp4|119.0|4.6|500:940:700:0|" \
  "raw/guaimei_yt.mp4|124.0|4.6|500:940:760:0|" \
  "raw/guaimei_yt.mp4|247.8|4.6|520:1000:610:0|"

# 年轮说(#4): 金调侧脸 -> 高调特写 -> 黑白泪痕(climax)
build_montage nianlun \
  "raw/nianlun_yt.mp4|67.8|4.8|540:1040:280:0|eq=brightness=0.04:contrast=1.05:saturation=1.08" \
  "raw/nianlun_yt.mp4|92.8|4.8|520:1000:1340:0|eq=brightness=0.03:contrast=1.04:saturation=1.06" \
  "raw/nianlun_yt.mp4|227.8|4.8|540:1040:400:0|eq=contrast=1.06"

# 有形的翅膀(#1,压轴): 张韶涵 feat.吴青峰 Live(同台合唱他写的歌)。张韶涵特写 -> 吴青峰特写 -> 二人相拥(button)。
# 收束全片主题:词作者与演唱者同框。底部小字幕用 H<=960 裁掉。
build_montage youxing \
  "raw/youxing_feat.mp4|140.0|5.0|540:960:430:0|eq=brightness=0.04:contrast=1.05" \
  "raw/youxing_feat.mp4|165.0|4.8|540:960:430:0|eq=brightness=0.04:contrast=1.05" \
  "raw/youxing_feat.mp4|223.3|3.0|560:960:690:0|eq=brightness=0.06:contrast=1.04"

echo "ALL MONTAGE DONE"
