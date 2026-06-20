# 华晨宇最被低估的5首歌（竖屏盘点）

被低估的遗珠盘点，揭晓序 5→1，女声旁白(zf_xiaoyi)，1080×1920 / 30fps，约 4:48。

## 榜单（揭晓序 5→1）
05《Let You Go》· 04《消失的昨天》· 03《造物者》· 02《微光》· 01《我离孤单几公里》

## 复现
```bash
# 1. 旁白（女声）
../../tools/tts/venv/bin/python build/narrate_segments.py
# 2. 切片(crop+letterbox) + master.wav + index.html（单一来源）
../../tools/tts/venv/bin/python build/full_build.py
#    SAMPLE_KEYS=p2_weiguang,p1_wligj 出样片；SKIP_CLIPS=1 复用已切 clips
# 3. 渲染 + mux（HF 会压平动态 → master.wav 后期覆盖音轨）
npx hyperframes render --output renders/full_raw.mp4 --sdr -w 3
ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/huachenyu-underrated-top5.mp4
```

## 要点
- 5 首取自 5 场不同演出（避免审美疲劳）；选源/裁切/窗口见 `SOURCES.md`，设计见 `design.md`。
- 展示段 vocal onset 对齐转场旁白收尾前 ~2s（CONVENTIONS 展示段硬规则 C）。
- 结尾＝作品 outro（榜单+升华，无投票问句）→ 消化位 → 固定引流 CTA（全片最后一句，女声照念）。
- 成片＝mux 后的 `renders/huachenyu-underrated-top5.mp4`（非 HF 直出）。

## 产物（gitignore）
`raw/` 源素材、`renders/`、`*.mp4`、`master.wav`、`*.wav` 不入库；保留 `build/`、`*.md`、`narration.json`。
