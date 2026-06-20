#!/bin/bash
# Cut footage -> crop watermark/burned-lyrics/台标 -> letterbox 1080x1920 (keep原比例, no放大).
# Diversified sources (year/show/outfit), all DECOUPLED from studio audio:
#  #1 水中央  : 2003 DVD MV Penny-solo montage (crop 4:3 sidebars + karaoke + corner logo)
#  #2 钢琴键  : 2022 时光音乐会 我会好好的 (solo closeups; crop 时光 台标 + bottom credit)
#  #3 安心睡着: 2013 纯属意外音乐会 live (clean)
#  #4 转眼    : ~2007 怎样 發現Live (center-crop kills both 台标 + side band member)
#  #5 非诚勿扰: 2016 own neon-noir MV montage (3 Penny closeups + atmospheric b-roll)
#  cover/intro: 2016 钢琴键 MV frontal closeups (gorgeous, unused by #2) ; outro: 2025 野薔薇
set -e
cd /Users/yinshawnrao/explorer/cc-media/sandbox/daipeini-underrated-top5
mkdir -p clips clips/tmp

LB='scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=28,eq=brightness=-0.34:saturation=1.03'

# letterbox a single continuous window: src out start len cropchain
vert () {
  local src="$1" out="$2" start="$3" len="$4" crop="$5"
  ffmpeg -v error -ss "$start" -i "$src" -t "$len" -filter_complex \
    "[0:v]${crop}[c];[c]split=2[bg][fg];[bg]${LB}[bgb];[fg]scale=1080:-2[fgs];[bgb][fgs]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]" \
    -map "[v]" -an -c:v libx264 -preset veryfast -crf 19 -r 30 -g 30 -keyint_min 30 "clips/$out" -y
  echo "wrote clips/$out  $(ffprobe -v error -show_entries format=duration -of csv=p=0 clips/$out)s  $(ffprobe -v error -select_streams v -show_entries stream=width,height -of csv=p=0:s=x clips/$out)"
}

# one montage shot (letterboxed, HARD CUT — no fade-to-black between shots) -> clips/tmp/<idx>.mp4
seg () {
  local src="$1" idx="$2" start="$3" len="$4" crop="$5"
  ffmpeg -v error -ss "$start" -i "$src" -t "$len" -filter_complex \
    "[0:v]${crop}[c];[c]split=2[bg][fg];[bg]${LB}[bgb];[fg]scale=1080:-2[fgs];[bgb][fgs]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]" \
    -map "[v]" -an -c:v libx264 -preset veryfast -crf 19 -r 30 -g 30 -keyint_min 30 "clips/tmp/${idx}.mp4" -y
}

montage () {  # outfile then seg idx list -> concat
  local out="$1"; shift
  : > clips/tmp/${out}.txt
  for x in "$@"; do echo "file '${x}.mp4'" >> clips/tmp/${out}.txt; done
  ffmpeg -v error -f concat -safe 0 -i clips/tmp/${out}.txt -c copy "clips/${out}.mp4" -y
  echo "wrote clips/${out}.mp4  $(ffprobe -v error -show_entries format=duration -of csv=p=0 clips/${out}.mp4)s"
}

# ============ #1 水中央 (2003 DVD MV) — continuous SYNCED window; showcase on Penny run-B 140-160 ============
# Penny is the MV star (brief love-interest/outdoor cuts are normal MV grammar); crop 4:3 sidebars+logo+karaoke
vert raw/shuizhongyang_dvd.mp4 vert_shuizhongyang.mp4 118 42 "crop=1600:580:160:120"

# ============ #2 钢琴键 (2022 时光音乐会《我会好好的》) — Penny-dominant window; showcase on 150-165 ============
# crop kills 芒果tv(top) + 时光 badge(btm-right) + lyric(btm); brief panel cutaways = normal music-show grammar
vert raw/gangqinjian_tv.webm vert_gangqinjian.mp4 126 42 "crop=1920:650:0:165"

# ============ #3 安心睡着 (2013 纯属意外音乐会 Live) — continuous Penny+guitar ============
vert raw/anxin_live.mkv vert_anxin.mp4 70 44 "crop=1920:1040:0:20"

# ============ #4 转眼 (~2007 怎样 發現Live) — center-crop kills 台标+band; showcase on 144-168 run ============
vert raw/zenyang_live.webm vert_zhuanyan.mp4 124 44 "crop=1280:680:340:170"

# ============ #5 非诚勿扰 (2016 neon-noir MV) — atmospheric b-roll -> Penny closeups (showcase) ============
C_FC="crop=1920:980:0:0"
seg raw/feicheng_mv.mkv f0 232 5 "$C_FC"   # bridge (under narration)
seg raw/feicheng_mv.mkv f1 86  5 "$C_FC"   # neon b-roll
seg raw/feicheng_mv.mkv f2 36  8 "$C_FC"   # Penny
seg raw/feicheng_mv.mkv f3 150 4 "$C_FC"   # neon flash
seg raw/feicheng_mv.mkv f4 168 8 "$C_FC"   # Penny (leather)
seg raw/feicheng_mv.mkv f5 122 10 "$C_FC"  # Penny (bar profile, showcase climax)
montage vert_feicheng f0 f1 f2 f3 f4 f5

# ============ cover / intro backdrop (2016 钢琴键 MV frontal closeups) — frame0 = laughing closeup ============
C_PIANO="crop=1920:950:0:30"
# frame0 = 钢琴键 MV laughing closeup (best thumbnail) -> crossfade to clean continuous 野薔薇 backdrop
# (钢琴键 MV cuts to male lead every ~3s so it can't sustain a backdrop; only its frame0 hook is used)
seg raw/gangqinjian_mv.webm   c0 150 2.5  "$C_PIANO"                   # frame0 = laughing closeup (thumbnail)
seg raw/yeqiangwei_live.mkv   c1 100 14.4 "crop=1920:1040:0:20"        # clean continuous Penny backdrop
montage vert_cover c0 c1                                               # ~16.9s (spans intro_end 15.25)

# ============ outro backdrop (2025 野薔薇, distinct window from cover) ; must span outro 31.55s ============
vert raw/yeqiangwei_live.mkv vert_outro.mp4 40 33 "crop=1920:1040:0:20"

echo ALL_VERTS_DONE
