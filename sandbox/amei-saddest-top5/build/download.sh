#!/usr/bin/env bash
# Re-download LONGER show-windows (~66-72s) so the chorus lands in the back half (show portion).
# clips.sh will output-seek S=6 inside each → clip-time fsl == chorus_start.
set -uo pipefail
cd "$(dirname "$0")/.."
YTC="../www.youtube.com_cookies.txt"
BLC="../www.bilibili.com_cookies.txt"
mkdir -p raw

dl() { local cookie="$1" url="$2" sec="$3" out="$4" fmt="$5"
  echo ">>> $out  [$sec]"
  yt-dlp "$url" --cookies "$cookie" --download-sections "*$sec" --no-playlist \
    -f "$fmt" -o "raw/$out.%(ext)s" -N 4 2>&1 | tail -2
}

# clip_start(source) = chorus - fsl ; dl_start = clip_start - 6 ; window ~70s
# ① 人质     chorus 02:25, fsl 20.0 -> clip_start 02:05 -> dl 01:59
dl "$YTC" "https://www.youtube.com/watch?v=WzurKmKOUuk" "00:01:59-00:03:11" "renzhi"      "bv*[height<=2160]+ba/b"
# ③ 剪爱     chorus 01:17, fsl 18.3 -> clip_start 00:59 -> dl 00:53
dl "$YTC" "https://www.youtube.com/watch?v=ZH9k3643BH8" "00:00:53-00:02:03" "jianai"      "bv*+140/bv*+ba/b"
# ④ 掉了     chorus 01:30, fsl 19.1 -> clip_start 01:11 -> dl 01:05
dl "$BLC" "https://www.bilibili.com/video/BV1L14y1q7aM" "00:01:05-00:02:15" "diaole"      "bv*[height<=2160]+ba/b"
# ② 我恨我爱你 chorus 01:28, fsl 20.6 -> clip_start 01:07 -> dl 01:01 (widen at 2:10; tail unused)
dl "$BLC" "https://www.bilibili.com/video/BV1ch411v7sS" "00:01:01-00:02:11" "wohenwoaini" "bv*[height<=2160]+ba/b"
# ⑤ 连名带姓  chorus 03:25, fsl 19.6 -> clip_start 03:05 -> dl 02:59
dl "$BLC" "https://www.bilibili.com/video/BV1594y1y77k" "00:02:59-00:04:11" "lianmingdaixing" "bv*[height<=1080]+ba/b"

# 人质 is AV1/webm -> transcode to mp4 so audio length is正常 (avoid opus tail-truncation downstream)
if ls raw/renzhi.webm >/dev/null 2>&1; then
  ffmpeg -v error -i raw/renzhi.webm -c:v libx264 -preset veryfast -crf 16 -pix_fmt yuv420p \
    -r 30 -g 30 -keyint_min 30 -c:a aac -b:a 192k raw/renzhi_fix.mp4 -y
fi

echo "=== RESULT ==="
for f in renzhi renzhi_fix jianai diaole wohenwoaini lianmingdaixing; do
  m=$(ls raw/$f.* 2>/dev/null | grep -vE '\.part$' | head -1)
  [ -n "$m" ] && printf "%-16s %s | vdur=%s | ch=%s\n" "$f" \
    "$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height,codec_name -of csv=p=0:s=x "$m")" \
    "$(ffprobe -v error -select_streams v:0 -show_entries format=duration -of csv=p=0 "$m")" \
    "$(ffprobe -v error -select_streams a:0 -show_entries stream=channels -of csv=p=0 "$m")"
done
echo "ALL DONE"
