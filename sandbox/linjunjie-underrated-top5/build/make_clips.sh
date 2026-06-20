#!/bin/bash
# Build vertical 1080x1920 footage clips for 林俊杰最被低估的5首歌.
# - Continuous clips (own audio): #5 黑键 MV, #2 不流泪 JJ20 Live, #1 距离 ATR Live, intro JJ20.
# - Montage clips (decoupled studio audio): #3 突然累了 seashore JJ montage, #4 陌生老朋友 = 学不会 autumn JJ montage.
# All footage cropped to remove burned lyrics / tour logo, then letterboxed (keep original ratio, no zoom-crop).
set -e
cd /Users/yinshawnrao/explorer/cc-media/sandbox/linjunjie-underrated-top5
mkdir -p clips tmp

LB='scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=26,eq=brightness=-0.30:saturation=1.04'

# vert <src> <out> <start> <len> <pre>   (pre = delogo/crop chain ending with comma, or empty)
vert () {
  src="$1"; out="$2"; start="$3"; len="$4"; pre="$5"
  ffmpeg -v error -ss "$start" -i "$src" -t "$len" -filter_complex \
    "[0:v]${pre}split=2[bg][fg];[bg]${LB}[bgb];[fg]scale=1080:-2[fgs];[bgb][fgs]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]" \
    -map "[v]" -map 0:a -c:v libx264 -preset veryfast -crf 19 -r 30 -g 30 -keyint_min 30 \
    -c:a aac -b:a 256k -ar 48000 "clips/$out" -y
  echo "wrote clips/$out  $(ffprobe -v error -show_entries format=duration -of csv=p=0 clips/$out)s  $(ffprobe -v error -select_streams v -show_entries stream=width,height -of csv=p=0:s=x clips/$out)"
}

# ---- Continuous clips (own audio) ----
# intro / cover  : 不流泪 JJ20 frontal closeups (generic JJ singing; does NOT reveal any of the 5 songs)
vert raw/jichang_yt_jj20.mp4 vert_intro.mp4 78 58 \
  "crop=1920:812:0:158,"
# 5  黑键 MV : white-studio + rain, JJ; crop bottom-left lyric band
vert raw/heijian_yt_mv.mp4 vert_heijian.mp4 80 56 \
  "crop=1920:1006:0:0,"
# 2  不流泪 JJ20 Live : remove top-left JJ-PRODUCTIONS logo (delogo) + bottom lyric
vert raw/jichang_yt_jj20.mp4 vert_jichang.mp4 128 56 \
  "crop=1920:812:0:158,"
# 1  距离 After The Rain Live : crop bottom lyric
vert raw/juli_live_atr.mp4 vert_juli.mp4 150 56 \
  "crop=1920:944:0:0,"

# ---- Montage clips (decoupled studio audio) ----
# Cut JJ-only sub-clips (no audio), concat, then crop+letterbox, then mux decoupled studio audio.
cut_sub () { src="$1"; tag="$2"; s="$3"; l="$4"
  # keep native resolution (all sub-clips of one montage share a source -> consistent for concat)
  ffmpeg -v error -ss "$s" -i "$src" -t "$l" -an -vf "fps=30,setsar=1,format=yuv420p" -c:v libx264 -preset veryfast -crf 18 -g 30 -keyint_min 30 "tmp/${tag}.mp4" -y; }

montage_vert () { # $1=tag(turan/moshen) $2=crop $3=audio_src $4=astart $5=alen
  tag="$1"; crop="$2"; asrc="$3"; as="$4"; al="$5"
  : > tmp/${tag}_list.txt
  for f in tmp/${tag}_*.mp4; do echo "file '$(basename $f)'" >> tmp/${tag}_list.txt; done
  ffmpeg -v error -f concat -safe 0 -i tmp/${tag}_list.txt -c copy tmp/${tag}_cat.mp4 -y
  ffmpeg -v error -ss "$as" -i "$asrc" -t "$al" -vn -c:a pcm_s16le -ar 48000 -ac 2 "tmp/${tag}_aud.wav" -y
  ffmpeg -v error -i tmp/${tag}_cat.mp4 -i "tmp/${tag}_aud.wav" -filter_complex \
    "[0:v]${crop}split=2[bg][fg];[bg]${LB}[bgb];[fg]scale=1080:-2[fgs];[bgb][fgs]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]" \
    -map "[v]" -map 1:a -c:v libx264 -preset veryfast -crf 19 -r 30 -g 30 -keyint_min 30 -c:a aac -b:a 256k -ar 48000 -shortest "clips/vert_${tag}.mp4" -y
  echo "wrote clips/vert_${tag}.mp4  $(ffprobe -v error -show_entries format=duration -of csv=p=0 clips/vert_${tag}.mp4)s"
}

# 3  突然累了 : seashore JJ montage  (audio = album studio, from the MV's own track)
rm -f tmp/turan_*.mp4
cut_sub raw/turan_bili_mv.mp4 turan_0 152 16   # JJ closeups
cut_sub raw/turan_bili_mv.mp4 turan_1 216 22   # JJ rocks / behind window-bars
cut_sub raw/turan_bili_mv.mp4 turan_2 54 10    # JJ at white piano
cut_sub raw/turan_bili_mv.mp4 turan_3 140 8    # JJ
montage_vert turan "crop=1728:1000:0:0," raw/turan_bili_mv.mp4 130 56

# 4  陌生老朋友 : 学不会 autumn JJ montage  (audio = 陌生老朋友 studio master)
rm -f tmp/moshen_*.mp4
cut_sub raw/xuebuhui_mv.mp4 moshen_0 113 12    # JJ pensive + figurine
cut_sub raw/xuebuhui_mv.mp4 moshen_1 207 8     # JJ station closeup
cut_sub raw/xuebuhui_mv.mp4 moshen_2 134 8     # JJ at grand piano
cut_sub raw/xuebuhui_mv.mp4 moshen_3 58 9      # JJ at table
cut_sub raw/xuebuhui_mv.mp4 moshen_4 183 8     # JJ on rooftop
cut_sub raw/xuebuhui_mv.mp4 moshen_5 44 9      # grand-piano keys (instrumental-feel)
montage_vert moshen "crop=1920:958:0:0," raw/moshen_studio.wav 130 56

echo ALL_CLIPS_DONE
ls -la clips/*.mp4 | awk '{printf "%.1fMB %s\n",$5/1048576,$9}'