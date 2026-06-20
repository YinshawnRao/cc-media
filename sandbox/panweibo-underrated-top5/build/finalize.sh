#!/usr/bin/env bash
set -e
cd /Users/yinshawnrao/explorer/cc-media/sandbox/panweibo-underrated-top5
ffmpeg -v error -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/panweibo-underrated-top5.mp4 -y
echo "wrote renders/panweibo-underrated-top5.mp4"
ffprobe -v error -show_entries format=duration:stream=width,height,codec_name -of default=nw=1 renders/panweibo-underrated-top5.mp4 | head -8
