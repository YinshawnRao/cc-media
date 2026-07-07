# sodagreen-underrated-top5 — 苏打绿最被低估的5首歌

竖屏 1080×1920 音乐盘点（倒数 5→1），约 4:55。男声 `zm_yunxi`。

## 榜单
5 频率 · 4 彼得与狼 · 3 包围 · 2 燕窝 · 1 无言歌

## 复现
```bash
# 1) 配音（intro/5首/outro + 固定CTA）
tools/tts/venv/bin/python build/narrate_segments.py
# 2) 人声段（已产 probe/vocal_analysis.json，源时间码，喂展示段对齐闸门）
#    tools/tts/venv/bin/python tools/video/vocal_segments.py raw/*_aud.wav --gap-tol 0.45 --min-dur 1.2 ...
# 3) 构建 master.wav + footage_track + index.html（内置 showcase_align 闸门）
tools/tts/venv/bin/python build/full_build.py        # SAMPLE=1 出样片
# 4) 渲染 + mux
HYPERFRAMES_EXTRACT_CACHE_DIR=.extract_cache npx hyperframes render --output renders/full_raw.mp4 --sdr -w 2
ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/sodagreen-underrated-top5.mp4
```

成片：`renders/sodagreen-underrated-top5.mp4`。选源与事实见 `SOURCES.md`。
