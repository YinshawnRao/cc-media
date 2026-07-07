# maobuyi-underrated-top5 — 毛不易最被低估的5首歌

竖屏 1080×1920 音乐盘点，倒数 05→01，男声旁白 `zm_yunxi`，全片 ~5:25。

## 排名（揭晓序 05→01）
05《等》· 04《于是没有洗头》· 03《深夜一角》· 02《水乡》· 01《南一道街》

## 选源 / 事实
见 `SOURCES.md`。要点：5 首全为毛不易本人词曲自创；《幼鸟指南》是 **2021**（非 2023）；
只有《水乡》《于是没有洗头》有官方 MV（水乡 MV 无本人出镜）→ 全 5 首解耦（录音室音轨 + 本人现场/官方MV画面）。

## 复现
```bash
# 1. 配音（男声 zm_yunxi）
tools/tts/venv/bin/python build/narrate_segments.py
# 2. 人声段检测 → 对齐闸门基准（音源在录音室音轨时间基准）
tools/tts/venv/bin/python tools/video/vocal_segments.py raw/p{1..5}_aud.wav -o probe/vocal_raw.json
#    （键名 remap 成 vert_p*_* 写 probe/vocal_analysis.json）
# 3. 画面：每源预切窗口 + vfill letterbox → clips/vert_*.mp4
# 4. 构建 master.wav + index.html（内含 showcase_align.gate 对齐闸门）
tools/tts/venv/bin/python build/full_build.py        # SAMPLE=1 只出#5样片；HTML_ONLY=1 跳过音频
# 5. 渲染 + 后期 mux（HF 会压平动态，必须用 master.wav 覆盖音轨）
npx hyperframes@0.6.69 render --output renders/full_raw.mp4 --sdr -w 2
ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/maobuyi-underrated-top5.mp4
```

## 关键约束（本片已遵守）
- 后期 mux master.wav（HF 压平动态）；展示段 letterbox 保原比例（不竖裁放大）；
- 每首连续副歌展示 ≥28s（4首≥35s）；末句固定引流 CTA（`tools/video/outro_cta.py`）；
- 成片无水印/网址/路径/台标残留（逐源 crop + 抽帧核）。

## 产物
`renders/maobuyi-underrated-top5.mp4`（mux 后为准）。
