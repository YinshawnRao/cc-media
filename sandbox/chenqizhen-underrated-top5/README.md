# chenqizhen-underrated-top5 — 陈绮贞最被低估的5首歌

竖屏 1080×1920 解说盘点，女声旁白（`zf_xiaoyi`），倒数揭晓 5 -> 1。

## 揭晓顺序

| 名次 | 歌曲 | 角度 |
|---|---|---|
| 5 | 距离 | 《Groupies 吉他手》时期的隐藏宝藏，像一封寄不出去的信 |
| 4 | 太聪明 | 爱情里的自我觉察，越长大越刺 |
| 3 | 躺在你的衣柜 | 真爱粉神曲，怪、可爱、悲伤 |
| 2 | 80%完美的日子 | 后期观察生活的迷人状态 |
| 1 | 腐朽 | 《华丽的冒险》里冷静到残忍的遗珠 |

## 复现流程

```bash
# 1) 下载官方源
bash build/download_sources.sh

# 2) 切片 + 竖屏化
bash build/make_clips.sh

# 3) 女声旁白
tools/tts/venv/bin/python build/narrate_segments.py

# 4) 预混音轨 + HyperFrames HTML
python3 build/full_build.py
npx hyperframes lint

# 5) 渲染 + 后期 mux
npx hyperframes render --output renders/full_raw.mp4 --sdr -w1
ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/chenqizhen-underrated-top5.mp4
```

成片以 mux 后的 `renders/chenqizhen-underrated-top5.mp4` 为准。

## 选源备注

五首都做了 YouTube + B站候选对照。最终除《躺在你的衣柜》外均使用官方 MV；《躺在你的衣柜》官方 MV 的长人声段进入片尾黑底字幕，改用 2013 Live，并通过中间竖裁去掉右下 uploader 水印。
