# 梁咏琪最被低估的5首歌

竖屏 1080×1920 音乐盘点，倒数 05→01（#1=《失散车站》压轴），男声旁白 `zm_yunxi`，总时长 ~4:55。
开头 / 每首转场 / 结尾均有配音；固定引流 CTA 为全片最后一句。

## 榜单（倒数揭晓 05→01）

| # | 歌曲 | 专辑 / 年 |
| --- | --- | --- |
| 05 | 地球的住客 | Suddenly, This Summer · 2001 |
| 04 | 喜剧收场 | G For Girl · 2001 |
| 03 | 旅程 | 爱自己 · 1996 |
| 02 | 荷花 | G For Girl · 2001 |
| 01 | 失散车站 | Suddenly, This Summer · 2001 |

## 选源 / 事实

见 `SOURCES.md`。核心：5 首官方上传都是「静态封面 + 录音」(Art Track)，无真 MV → **全部解耦**
（官方录音室音轨 + 本人其他真 MV 特写蒙太奇）。全 5 首为**粤语**（brief 误判为国语，已纠正）。

## 复现

```bash
# 1) 配音（Kokoro 男声 + 固定 CTA）
tools/tts/venv/bin/python build/narrate_segments.py
# 2) 画面蒙太奇（解耦 footage，逐源 letterbox 裁净水印/烧词）
python3 build/montage.py
#    + intro/outro 底片 + cover_hero（见 build 注释 / 历史命令）
# 3) 人声段检测 → vocal_analysis.json（键 = vert_<key>，源时间）
# 4) master.wav + index.html（含展示段对齐闸门，违规不出 master）
python3 build/full_build.py
# 5) 渲染 + 后期 mux（HF 压平动态，必须用 master.wav 覆盖音轨）
npx hyperframes@0.6.69 render --output renders/full_raw.mp4 --sdr -w 2
ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/liangyongqi-underrated-top5.mp4
```

成片：`renders/liangyongqi-underrated-top5.mp4`（mux 后为准）。
