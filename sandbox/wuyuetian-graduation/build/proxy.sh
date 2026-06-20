#!/usr/bin/env bash
cd /Users/yinshawnrao/explorer/cc-media/sandbox/wuyuetian-graduation
for k in sgj ganbei hldwm zyjs; do
  echo "proxy $k ..."
  ffmpeg -v error -i raw/${k}_full.mkv -vf scale=960:-2 -c:v libx264 -preset ultrafast -g 30 -keyint_min 30 -an raw/${k}_proxy.mp4 -y
done
echo "PROXIES DONE"
