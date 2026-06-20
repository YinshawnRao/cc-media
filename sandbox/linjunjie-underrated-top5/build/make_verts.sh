#!/bin/bash
# Cut window -> delogo watermarks -> crop burned lyrics -> letterbox 1080x1920.
# One re-encode per song. Input-side seek (sources are H.264 proxies / raw H.264 / mkv).
set -e
cd /Users/yinshawnrao/explorer/cc-media/sandbox/fangdatong-underrated-top5
mkdir -p clips

LB='scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=28,eq=brightness=-0.34:saturation=1.02'

vert () {
  src="$1"; out="$2"; start="$3"; len="$4"; pre="$5"   # pre = delogo+crop chain (ends with comma if non-empty), then split
  ffmpeg -v error -ss "$start" -i "$src" -t "$len" -filter_complex \
    "[0:v]${pre}split=2[bg][fg];[bg]${LB}[bgb];[fg]scale=1080:-2[fgs];[bgb][fgs]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]" \
    -map "[v]" -map 0:a -c:v libx264 -preset veryfast -crf 19 -r 30 -g 30 -keyint_min 30 \
    -c:a aac -b:a 256k -ar 48000 "clips/$out" -y
  echo "wrote clips/$out  $(ffprobe -v error -show_entries format=duration -of csv=p=0 clips/$out)s  $(ffprobe -v error -select_streams v -show_entries stream=width,height -of csv=p=0:s=x clips/$out)"
}

# 5  Over   : 音乐料理房(TR) + Warner badge(UR) delogo, crop bottom lyric
vert proxy/over.mp4 vert_over.mp4 128 54 \
  "delogo=x=1738:y=58:w=180:h=52,crop=1920:846:0:0,"   # Warner-free window (src56-68 has uncroppable centered Warner)
# 4  暖     : clean, crop bottom lyric only
vert proxy/nuan.mp4 vert_nuan.mp4 145 58 \
  "crop=1920:892:0:0,"
# 3  黑洞里 : 音乐料理房(TR) delogo, crop bottom lyric
vert proxy/heidongli.mp4 vert_heidongli.mp4 172 58 \
  "delogo=x=1738:y=104:w=180:h=54,crop=1920:856:0:0,"
# 2  Orange Moon : clean 720p, full-frame letterbox
vert raw/orangemoon.mp4 vert_orangemoon.mp4 110 58 \
  ""
# 1  Take Me (15 concert) : 音乐料理房(TR) delogo, lyric-safe crop (mixed 2.35:1/16:9 -> crop y<=648)
#    NOTE: MOOV source (rqTrUrMq-rM) rejected: 3 watermark variants (moov dog logo / moov LIVE / Warner) at varying positions.
vert proxy/takeme.mp4 vert_takeme.mp4 152 58 \
  "delogo=x=1738:y=100:w=180:h=58,crop=1920:648:0:0,"
echo ALL_VERTS_DONE
</content>
