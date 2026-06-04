#!/usr/bin/env bash
DIR=/Users/yinshawnrao/explorer/cc-media/sandbox/zsh-gaokao-mazu/scene_raw
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
pex () { # id name
  curl -sL -A "$UA" "https://www.pexels.com/download/video/$1/" -o "$DIR/$2.mp4"
  local r=$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x "$DIR/$2.mp4" 2>/dev/null)
  local sz=$(wc -c < "$DIR/$2.mp4" 2>/dev/null)
  echo "$2.mp4 | $r | ${sz}B"
  sleep 1
}
pex 31948465 p1_write
pex 5734765  p1_classroom
pex 8533913  run_track
pex 19539315 p2_rainrun
pex 14501261 p2_rainstreet
pex 6581005  p2_police
pex 31240469 school_gate
pex 854549   p2_waiting
pex 16538871 p3_rainsil
pex 2960875  p3_raindrop
pex 5108693  p3_umbrella
pex 14009143 p3_backwalk
pex 8061028  p4_capwave
pex 7945811  p4_capthrow
pex 1860175  p4_sky
pex 4079865  p4_writing
pex 4524597  p4_runsun
echo "=== SCENE DOWNLOAD DONE ==="
ls -la "$DIR"/*.mp4 | wc -l
