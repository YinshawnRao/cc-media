# 苏慧伦最被低估的5首歌

竖屏 1080×1920 长盘点，倒数揭晓 05→01（#1=《你来》压轴），男声 `zm_yunxi`。约 5:16。

## 排名（揭晓序 05→01）

| # | 歌曲 | 专辑 · 年 | 模式 | 画面 |
| --- | --- | --- | --- | --- |
| 05 | 你有离开的自由 | 懒人日记 · 1999 | 耦合 | 同曲官方MV(冷调特写) |
| 04 | 哭过的天空 | 失恋万岁 · 1998 精选 | 耦合 | 同曲官方MV(暗调舞台) |
| 03 | 酿爱 | Lemon Tree · 1996 | 解耦 | 《Lemon Tree》MV(同碟,粉调) |
| 02 | 叶子落下的世界 | 鸭子 · 1996 | 解耦 | 《我一個人住》MV(柔光独镜) |
| 01 | 你来 | 鸭子 · 1996 | 耦合 | 同曲官方MV(亮绿棚景) |

选源细节见 `SOURCES.md`。

## 复现

```bash
# 1. 配音（已生成 audio/*.wav）
tools/tts/venv/bin/python build/narrate_segments.py
# 2. 音轨 + HTML（含展示段对齐闸门，违规不出 master）
tools/tts/venv/bin/python build/full_build.py
# 3. 渲染（--sdr 必加）
npx hyperframes@0.6.69 render --output renders/full_raw.mp4 --sdr -w 2
# 4. mux 预混 master（HF 会压平动态，成片以 mux 后为准）
ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/suhuilun-underrated-top5.mp4
```

环境开关：`SAMPLE=1`（仅 intro+#5+outro 样片）、`HTML_ONLY=1`（跳过音轨重建）。

## 硬规则落点

- footage 全 letterbox（crop 618:384 裁底卡拉OK烧词），不裁切放大。
- 每首连续副歌展示段 ≥29s（#1 给 42s），展示段对齐闸门 5/5 OK。
- 固定结尾 CTA 为全片最后一句（`tools/video/outro_cta.py`），排在作品 outro 之后。
- 成片画面无水印/网址/UP/路径/提示词。
