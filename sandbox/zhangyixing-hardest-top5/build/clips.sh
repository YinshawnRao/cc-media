#!/usr/bin/env bash
# 张艺兴最难5首：精切+vfill 竖屏化。全部耦合（画面+音频同源同窗，口型同步）。
# 选源依据见 SOURCES.md；展示段窗口取自 probe/vocal_analysis.json 最长连续人声段。
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
VF="$ROOT/../../tools/video/vfill.sh"
mkdir -p clips

# 精切（混合seek：input粗seek mseek-4 + output精seek 4 = 帧级精准）→ 临时片 → vfill
cut_vfill(){ key="$1"; src="$2"; mseek="$3"; dur="$4"; crop="$5"; br="${6:--0.15}"; sat="${7:-1.05}"
  coarse=$(python3 -c "print(max(0,$mseek-4))")
  fine=$(python3 -c "print($mseek-max(0,$mseek-4))")
  ffmpeg -v error -ss "$coarse" -i "raw/$src" -ss "$fine" -t "$dur" \
    -c:v libx264 -crf 18 -preset veryfast -r 30 -g 30 -keyint_min 30 \
    -c:a aac -ar 48000 -ac 2 "clips/_pre_${key}.mp4" -y
  bash "$VF" "clips/_pre_${key}.mp4" "clips/vert_${key}.mp4" "$crop" "$br" "$sat"
}

# ---- intro / outro（同源《莲》镜头，与主展示段一样按官方 MV 原有剪辑节奏 coupled）----
# intro: 11-29s 城门前登场（单镜连续，已抽帧确认）。
# outro: 51-81s 避开 t=48-49 的"莲LIT"片名卡，士兵对话+行军+持械特写（随 MV 自身剪辑节奏，非单镜但无卡片/水印）。
cut_vfill intro lian_full.mp4 11.0 18.0  1920:760:0:180
cut_vfill outro lian_full.mp4 51.0 30.0  1920:760:0:180

# ---- 5 首展示段（buffer 提前 ~20s 留旁白+消化位余量，build 阶段再精切 show）----
cut_vfill p5_jiu     jiu_full.mp4      35.0  41.0  1000:900:460:12   0.05 1.0
cut_vfill p4_mianshan mianshan_full.mp4 128.0 54.0  1920:754:0:164
cut_vfill p3_menglin menglin_full.mp4  165.0 54.0  1920:816:0:132
cut_vfill p2_feitian feitian_full.mp4  131.0 59.0  1920:1080:0:0
cut_vfill p1_lian    lian_full.mp4     133.0 62.0  1920:760:0:180

echo "=== done. vert clips: ==="
for f in clips/vert_*.mp4; do echo "$f $(ffprobe -v error -show_entries stream=width,height,duration -of csv=p=0:s=, "$f" | head -1)"; done
