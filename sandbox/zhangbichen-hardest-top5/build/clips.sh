#!/usr/bin/env bash
# 张碧晨最难5首：精切+vfill 竖屏化（耦合：视频切点=音频mseek，保口型同步）。
# 全部官方Live(凉凉用官方MV)，画面+音频同源耦合。
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
VF="$ROOT/../../tools/video/vfill.sh"
mkdir -p clips raw

# 提取整源音频（build 用 raw/<aud>_aud.wav，按 mseek 切片做音乐）
extract_aud(){ src="$1"; aud="$2"; [ -f "raw/${aud}_aud.wav" ] || ffmpeg -v error -i "raw/$src" -vn -ar 48000 -ac 2 "raw/${aud}_aud.wav" -y; echo "aud ${aud}"; }

# 精切（混合seek：input粗seek mseek-4 + output精seek 4 = 帧级精准）→ 临时片 → vfill
cut_vfill(){ key="$1"; src="$2"; mseek="$3"; dur="$4"; crop="$5"; br="${6:--0.32}"; sat="${7:-1.06}"
  coarse=$(python3 -c "print(max(0,$mseek-4))")
  fine=$(python3 -c "print($mseek-max(0,$mseek-4))")
  ffmpeg -v error -ss "$coarse" -i "raw/$src" -ss "$fine" -t "$dur" \
    -c:v libx264 -crf 18 -preset veryfast -r 30 -g 30 -keyint_min 30 \
    -c:a aac -ar 48000 -ac 2 "clips/_pre_${key}.mp4" -y
  bash "$VF" "clips/_pre_${key}.mp4" "clips/vert_${key}.mp4" "$crop" "$br" "$sat"
}

# ---- 音频源（耦合：与视频同一条源）----
extract_aud kaiwang_full.mkv   kaiwang
extract_aud liang_mv_full.webm liang
extract_aud long_full.webm     long
extract_aud nianlun_full.mp4   nianlun
extract_aud guang_full.webm    guang

# ---- intro（动态封面：续在 #5 之前，kaiwang@188.85，与 #5 同源连续）----
cut_vfill intro   kaiwang_full.mkv   188.85 14.0  1020:960:415:0

# ---- 5 首（mseek=ch_off-full_start_local；seg_dur=full_start_local+show + 0.6 余量）----
cut_vfill p5_kaiwang kaiwang_full.mkv   202.40 40.2 1020:960:415:0          # 开往早晨 好声音中秋
cut_vfill p4_liang   liang_mv_full.webm 131.38 44.6 1360:1080:280:0         # 凉凉 官方MV(去右竖词)
cut_vfill p3_long    long_full.webm     135.28 35.9 1920:825:0:135  0.04 1.08  # 笼 ZJSTV(暗,微提亮)
cut_vfill p2_nianlun nianlun_full.mp4   6.71   47.5 1280:515:0:110  -0.10 1.08  # 年轮 咪咕
cut_vfill p1_guang   guang_full.webm    128.79 50.6 1020:960:415:0          # 光的方向 好声音

echo "=== done. vert clips: ==="
for f in clips/vert_*.mp4; do echo "$f $(ffprobe -v error -show_entries stream=width,height,duration -of csv=p=0:s=, "$f" | head -1)"; done
