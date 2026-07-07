# 张韶涵自己都忘了的5首歌

竖屏 1080×1920 音乐遗珠盘点，倒数揭晓 #5→#1。约 4:55。

- 揭晓顺序：#5《伤日快乐》→ #4《念念》→ #3《绝不》→ #2《控制不了》→ #1《瞬间移动》
- 设计：极光青配色（暗底 + #76d3e0 强调，#1 金色），衬线大标题 + 玻璃歌名卡 + 左侧排名。
- 封面 = 第一首出场歌《伤日快乐》婚纱 MV 动态画面，连续流入 #5。
- 结尾固定引流 CTA（全系列统一），排在作品 outro 之后。

## 复现
```bash
# 1) 配音（Kokoro zm_yunxi）
tools/tts/venv/bin/python build/narrate_segments.py
# 2) 竖屏化各源（crop 见 SOURCES.md）→ clips/vert_*.mp4
# 3) 人声段（含解耦 studio 音轨）
tools/tts/venv/bin/python ../../tools/video/vocal_segments.py clips/vert_p5_shangri.mp4 clips/vert_p4_niannian.mp4 clips/vert_p2_kongzhi.mp4 raw/juebu_audio.wav raw/shun_audio.wav -o probe/vocal_analysis.json
# 4) 建 master.wav + 单 footage_track + index.html（内置展示段对齐闸门）
tools/tts/venv/bin/python build/full_build.py
# 5) 渲染 + 后期 mux
npx hyperframes@0.6.69 render --output renders/full_raw.mp4 --sdr -w2
ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/angela-forgotten-top5.mp4
```

选源与各首坑见 `SOURCES.md`。素材 / 渲染产物已 gitignore。

## 已知短板
- **#1《瞬间移动》**：2010 单曲全网无 MV，footage 只能用 2026 玩家巡演观众直拍（偏暗、广角、少特写），已提亮 + 解耦录音室音轨保证听感；为本期唯一画质偏弱源。
