# linjunjie-underrated-top5 — 林俊杰最被低估的5首歌

竖屏 1080×1920 / ~5:17 / **女声**解说盘点，倒数 5→1。开场不揭名次，片尾列榜单 + 固定引流 CTA。

## 榜单（呈现倒数 5→1）
| 名次 | 歌 | 专辑 | 展示位素材 |
|---|---|---|---|
| 5 | 黑键 | 新地球 2014 | 官方 MV（白棚+雨夜，JJ） |
| 4 | 陌生老朋友 | 学不会 2011 | 学不会 MV 的 JJ 独镜蒙太奇 + 录音室音频（解耦） |
| 3 | 突然累了 | 编号89757 2006 | 海边 MV 的 JJ 独镜蒙太奇 + 录音室音频（解耦） |
| 2 | 不流泪的机场 | 西界 2005 | JJ20 重庆 Live（官方 1080p） |
| 1 | 距离 | 第二天堂 2004 | After The Rain Live（暗台亲密特写） |

选源细节与坑见 `SOURCES.md`，设计见 `design.md`。

## 重建
```bash
tools/tts/venv/bin/python build/narrate_segments.py   # 女声旁白 audio/*.wav（含 outro + 固定 CTA）
bash build/make_clips.sh                               # raw → clips/vert_*.mp4（连续片 + 2 个 montage）
python3 build/full_build.py                            # master.wav + index.html
bash build/render_full.sh                              # renders/full_raw.mp4（--sdr -w1 + 重试）
# mux：HyperFrames 会压平音频动态 → 用预混 master 覆盖音轨
ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/linjunjie-underrated-top5.mp4
```

## 成片
`renders/linjunjie-underrated-top5.mp4`（mux 后为准）。
