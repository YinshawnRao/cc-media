# 刀郎最被低估的5首歌

竖屏 1080×1920 倒数盘点（05→01），男声旁白 `zm_yunxi`。总时长 ~4:55。

## 榜单（倒数 05→01）

| 名次 | 歌曲 | 专辑 · 年 | 选源 |
| --- | --- | --- | --- |
| 05 | 风向朝西 | 世间的每个人 · 2020 | 知交线上演唱会（YT） |
| 04 | 瓜洲渡 | 弹词话本 · 2023 | **官方 MV**（B站 BV1CC4y1o7Wm） |
| 03 | 关于二道桥 | 喀什噶尔胡杨 · 2004 | 新疆十年环球巡演 LIVE（YT） |
| 02 | 德令哈一夜 | 刀郎Ⅲ · 2012 | 乌鲁木齐收官演唱会（B站 BV1114tzzEHi） |
| 01 | 喀什噶尔胡杨 | 喀什噶尔胡杨 · 2004 | 知交线上演唱会（YT） |

选源说明、双平台候选、crop/delogo、展示段时间码见 `SOURCES.md`。

## 复现

```bash
# 1) 配音（男声 zm_yunxi）
../../tools/tts/venv/bin/python build/narrate_segments.py
# 2) 竖屏化 footage（delogo 知交赞助标 + 各源裁烧词/UP标）
bash build/make_clips.sh
# 3) 建 master.wav + index.html + clips_seg
python3 build/full_build.py
# 4) 渲染（--sdr 必加）+ 后期 mux 真音轨
npx --yes hyperframes@0.6.69 render --output renders/full_raw.mp4 --sdr --protocol-timeout 600000
ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/daolang-underrated-top5.mp4
```

成片以 mux 后的 `renders/daolang-underrated-top5.mp4` 为准（HyperFrames 会压平音频动态，必须用 `master.wav` 后期 mux）。

## 关键约定

- 刀郎极少出镜、早期专辑基本无棚版 MV；仅《瓜洲渡》有官方 MV，其余用本人现场，已刻意分散不同演唱会/年代/舞台色。
- 固定结尾 CTA 来自 `tools/video/outro_cta.py`（全系列统一，逐字照念，全片最后一句）。
- 展示段 footage 窗 == 音乐窗（口型同步）；各首 loudnorm I=-14 统一响度；旁白段音乐 duck。
- 成片画面无水印 / 网址 / 提示词 / 路径。
