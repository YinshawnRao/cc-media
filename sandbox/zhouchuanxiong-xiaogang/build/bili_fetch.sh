#!/usr/bin/env bash
# 背景 gentle Bili 下载器：风控 412 需冷却，每首 sleep-retry，命中冷却窗口即成功。
# 下整片(height<=1080 立体声优先)到 raw/bili/<key>.mp4。后台运行允许 sleep。
set -uo pipefail
cd /Users/yinshawnrao/explorer/cc-media/sandbox/zhouchuanxiong-xiaogang
CK=../../www.bilibili.com_cookies.txt
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
mkdir -p raw/bili
# key:bvid  (cleanest 原版 master 候选)
PAIRS=(
  "hasa:BV13Q4y1A7eS"      # 哈萨雅琪 台版LD KTV(限1080)
  "shebude:BV1cVApz9ELY"   # 舍不得你走 官方MV DVD 1080P
  "fenggan:BV1bQGRzJEUm"   # 风干我的悲伤 歌林原版KTV
  "jipu:BV1HtwizoEKb"      # 吉普赛情人 小刚-吉普赛情人mv
  "peizhe:BV1gJ411M7gM"    # 陪着我尽头 Micronorth
)
for pair in "${PAIRS[@]}"; do
  key="${pair%%:*}"; bv="${pair##*:}"
  if ls raw/bili/${key}.* >/dev/null 2>&1; then echo "[$key] already have, skip"; continue; fi
  ok=0
  for i in $(seq 1 18); do
    yt-dlp "https://www.bilibili.com/video/$bv" --cookies "$CK" --user-agent "$UA" --referer "https://www.bilibili.com/" \
      -f "bv*[height<=1080]+ba/b[height<=1080]" --merge-output-format mp4 \
      -o "raw/bili/${key}.%(ext)s" >"raw/bili/${key}.log" 2>&1
    if ls raw/bili/${key}.mp4 >/dev/null 2>&1; then echo "[$key] OK try $i"; ok=1; break; fi
    echo "[$key] try $i fail ($(grep -oE 'HTTP Error [0-9]+|ERROR' raw/bili/${key}.log | head -1))"; sleep 45
  done
  [ $ok -eq 0 ] && echo "[$key] GAVE UP after 18 tries"
  sleep 8
done
echo "BILI_FETCH_DONE"