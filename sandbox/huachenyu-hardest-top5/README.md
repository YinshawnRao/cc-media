# 华晨宇最难的5首歌

竖屏 1080×1920 声乐难度盘点，倒数揭晓 5→1。女声旁白（zf_xiaoyi）贯穿开头/转场/结尾 + 固定引流 CTA。

成片：`renders/huachenyu-hardest-top5.mp4`（5:10，H.264 SDR + AAC，已后期 mux `master.wav`）。

> 展示段对齐（硬规则）：每首副歌唱声入点对齐转场旁白收尾前 ~2s，展示段(旁白结束后的 full-music 段)全程有唱、不落器乐段。初版 4/5 首踩坑(唱声被旁白盖住、展示段是伴奏)已按 CONVENTIONS「展示段硬规则 (C)」重对齐。ear-check 样片在 `qa/audio_samples/`。

排名（揭晓序）：05 烟火里的尘埃 · 04 我管你 · 03 寒鸦少年 · 02 斗牛 · 01 齐天。

复现：
1. `build/narrate_segments.py`（女声旁白 + 固定 CTA）→ `audio/*.wav` + `narration.json`
2. 选源/切窗/letterbox crop 见 `SOURCES.md`（每首双平台核验；官方MV多为影视/概念 tie-in → 改用现场）
3. `build/full_build.py` → `master.wav` + `index.html`（逐首 loudnorm I=-14；MGAIN 微调）
4. 渲染：`npx hyperframes render --sdr -w1`（渲染用 `renders/silent.m4a` 占位音轨）→ mux `master.wav`

设计见 `design.md`。
