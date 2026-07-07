# 许巍最被低估的5首歌

竖屏 1080×1920 音乐盘点，倒数 05→01，男声旁白 `zm_yunxi`。成片 ≈ 5:24。

## 排名（倒数揭晓）
- 05《故事》— 爱如少年 2008（第3首）
- 04《夏日的风》— 时光·漫步 2002（第9首）
- 03《简单》— 那一年 2000
- 02《九月》— 那一年 2000
- 01《天鹅之旅》— 时光·漫步 2002（开场第1首，压轴）

五首全部许巍一人词曲唱。选源/坑见 `SOURCES.md`（全 5 首 DECOUPLED：官方录音室音轨 + 本人 MV/Live 画面）。

## 复现
```bash
# 1) 旁白（男声 zm_yunxi）
../../tools/tts/venv/bin/python build/narrate_segments.py
# 2) 人声段检测（音频源，供对齐闸门）—— 已产出 probe/vocal_analysis.json
#    ln -sf raw/p?_aud.wav 命名为 vert_<key>.wav 后跑 tools/video/vocal_segments.py
# 3) 竖屏化（已在 clips/，seek+crop+letterbox 见 SOURCES.md 各首 crop）
# 4) 构建 master.wav + footage_track + index.html（内置展示段对齐闸门，5/5 OK）
../../tools/tts/venv/bin/python build/full_build.py
# 5) 渲染 + mux（HF 压平动态 → 必须后期 mux master.wav）
export HYPERFRAMES_EXTRACT_CACHE_DIR="$PWD/.extract_cache"
npx hyperframes@0.6.69 render --output renders/full_raw.mp4 --sdr -w 2
ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/xuwei-underrated-top5.mp4
```

## 关键约定（本期踩坑）
- **天鹅之旅官方MV不可用**：华纳台标巨幅、周期性、左右上角游走压每段副歌 + 底烧词 → 裁不净，只取音轨，画面改 2018 无尽光芒金光特写。
- **故事官方MV**：青海湖实景，TYPHOON 台标 + 底烧词 + 4:3 内嵌宽银幕 → 中央带裁 1440:560:0:205。
- 全 5 首 DECOUPLED；封面=动态首歌《故事》src[70] 许巍正脸（删 cover_hero 静图，连续流入 #5）。
- 固定结尾 CTA（投票+点赞收藏关注+下期预告）由 `tools/video/outro_cta.py` 提供，永远最后一句。
- 渲染 `--protocol-timeout` 不是合法 flag（会被当路径报错）；单 footage_track 轻量模式 -w2 一次过。

成片：`renders/xuwei-underrated-top5.mp4`
