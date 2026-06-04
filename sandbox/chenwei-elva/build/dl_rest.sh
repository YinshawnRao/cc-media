#!/usr/bin/env bash
# 顺序下载其余 7 首官方源（严格官方优先口径，见 SOURCES.md）。每首：video + 全曲 wav。
set -u
PROJ=/Users/yinshawnrao/explorer/cc-media/sandbox/chenwei-elva
CK=/Users/yinshawnrao/explorer/cc-media/sandbox/www.youtube.com_cookies.txt
cd "$PROJ" || exit 1
# key=videoID
declare -a JOBS=(
  "turan=KUf5MMj1wKw"      # 07 突然想起你 (官方 KARAOKE 480p)
  "yuji=XyMq9UufGuc"       # 06 雨季中 (官方 1600x1080 干净)
  "mingtian=3bRwMesVCl0"   # 05 明天 (官方 480p)
  "woaini=FSo03Rg9oPY"     # 04 我爱你那么多 (官方 480p)
  "woxihuan=gtyWddGBJ-M"   # 03 我喜欢你快乐 (官方 480p)
  "aida=EHMm_ElRvMA"       # 02 爱的主打歌 (官方 480p)
  "woyao=4KYb2FjT7rs"      # 01 我要的世界 (无官方→最干净二传 1080p Jazz Li)
)
for j in "${JOBS[@]}"; do
  key="${j%%=*}"; vid="${j##*=}"
  echo "=== $key ($vid) ==="
  yt-dlp --cookies "$CK" --no-playlist -f "bv*[height<=1080]+ba/b[height<=1080]" \
    -o "raw/${key}_src.%(ext)s" "https://www.youtube.com/watch?v=$vid" >/dev/null 2>&1
  src=$(ls raw/${key}_src.* 2>/dev/null | head -1)
  if [ -z "$src" ]; then echo "  FAIL download $key"; continue; fi
  ffmpeg -v error -i "$src" -vn -ac 2 -ar 48000 -c:a pcm_s16le "raw/${key}_full.wav" -y
  echo "  $key: $(ffprobe -v error -show_entries stream=width,height -of csv=p=0:s=x "$src" | head -1)  $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$src")s"
done
echo "=== ALL DOWNLOADS DONE ==="
ls -la raw/*_src.* raw/*_full.wav