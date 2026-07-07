# 陈慧娴最难的5首歌

竖屏 1080×1920，倒数 #5→#1（#1=月亮 压轴），~4:48。全 **coupled**（footage=该曲 MV，音频=同片原唱棚音/现场音，同窗切，对口型）。

## 榜单（倒数揭晓）
| # | 歌 | 专辑·年 | 源 | 展示窗(源s) |
|---|---|---|---|---|
| 05 | 归来吧 | 归来吧 · 1992 | YT 官方MV `LcZZ4zlC6Pc` 480p | 106–138 |
| 04 | 夜机 | 永远是你的朋友 · 1989 | YT `aOcHnGRUeo4` 1080p 高清MV | 172–203 |
| 03 | 飘雪 | 归来吧 · 1992 | YT 官方MV `oGTEVhr6-5E` 480p | 85–109 |
| 02 | 千千阙歌 | 永远是你的朋友 · 1989 | YT `4GFyzGJlPxg` 480p TVB版 | 264–293.5 |
| 01 | 月亮 | 归来吧 · 1992 | B站 `BV1Mt411d75j` 1080p | 234–260 |

详见 `SOURCES.md`（双平台对照 / 取舍 / 裁切坑）、`design.md`（视觉/节奏）。

## 复现
```bash
# 1. 旁白 TTS（男声 zm_yunxi）
tools/tts/venv/bin/python build/narrate_segments.py
# 2. 竖屏化（letterbox 裁烧词/台标）—— crop 见 SOURCES.md
bash tools/video/vfill.sh raw/src_<k>.* clips/vert_<k>.mp4 <crop>
# 3. 人声段（对齐闸门基准）
tools/tts/venv/bin/python tools/video/vocal_segments.py clips/vert_*.mp4 -o probe/vocal_analysis.json
# 4. build（master.wav + index.html + footage_track；内置 showcase_align 闸门，5/5 OK）
tools/tts/venv/bin/python build/full_build.py        # 全量
AUDIO_ONLY=1 ... build/full_build.py                 # 仅重建音频（复用 footage，调 mgain 用）
# 5. 渲染（--sdr，重试循环）+ mux（HF 压平动态，必须后期盖 master.wav）
bash build/render.sh
ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/chenhuixian-hardest-top5.mp4
```

## QA 基线
- 闸门 showcase_align：FAIL=0 WARN=0（覆盖 72–100%，入点对齐、结尾落句末/gap）。
- 展示段响度：-15.1～-16.3 dB（月亮稍软贴弱声气质）；旁白段 ~-24.5 dB（ducking ~9dB）。
- 整片无 >1s 静音；成片画面无台标/水印/烧词/路径泄漏。
- 固定结尾 CTA 为全片最后一句（防双 CTA：outro 无投票问句）。
