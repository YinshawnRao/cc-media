# 蔡徐坤最被低估的5首歌（caixukun-underrated-top5）

竖屏 1080×1920 长篇倒数盘点（05→01），男声旁白 `zm_yunxi`，约 4:32。
复用 `chenxiaochun-underrated-top5` 长篇模板（逐段 narration 驱动时间轴 + master.wav 后期 mux）。

## 榜单（揭晓顺序 5→1）

| 名次 | 歌曲 | 专辑/年份 | 展示 footage |
| --- | --- | --- | --- |
| 05 | 《没有意外》 | 单曲 · 2019 | 舞台演唱 Live（蓝调） |
| 04 | 《RIDE OR DIE》(至死不渝) | 单曲 · 2024 | 新加坡泡泡岛 Focus 直拍 |
| 03 | 《感受她》 | 专辑《迷》· 2021 | 2021《迷》巡演 Live |
| 02 | 《Hug me》(抱我) | 单曲 · 2022 | 2024 ART LAB 花海 Live |
| 01 | 《Home》 | 公益单曲 · 2020 | 官方动画公益 MV |

> 选源说明见 `SOURCES.md`：蔡徐坤官方 MV 多为动画/抽象/静态艺术片，按「质量第一」走混合选源（仅 Home 是纯官方 MV，其余用能看到他演唱的干净现场）。

## 复现

```bash
# 1. 配音（Kokoro 男声）
tools/tts/venv/bin/python build/narrate_segments.py
# 2. 竖屏化（已在 clips/，如需重做见 SOURCES.md 的 crop 表）
#    bash tools/video/vfill.sh raw/<src>.mp4 clips/vert_<key>.mp4 <crop>
# 3. 建 master.wav + index.html
python3 build/full_build.py
# 4. 渲染 + mux
HYPERFRAMES_EXTRACT_CACHE_DIR=/tmp/hf_cache_cxk npx --yes hyperframes@0.6.69 render --output renders/full_raw.mp4 --sdr -w 2
ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/caixukun-underrated-top5.mp4
```

成片以 mux 后的 `renders/caixukun-underrated-top5.mp4` 为准（HyperFrames 会压平音频动态，必须用预混 master 覆盖音轨）。

## 设计

冷色现代配色（电光蓝 #6cc0f2 + 紫 #8b6fd0）打底深蓝黑，贴合蔡徐坤更当代/艺术的气质（区别于盘点系列默认暖金）。Songti SC 大标题 + PingFang SC 正文 + JetBrains Mono 序号。
