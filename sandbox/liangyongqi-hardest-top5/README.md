# 梁咏琪最难的5首歌 (liangyongqi-hardest-top5)

竖屏 1080×1920 声乐难度盘点，倒数 5→1，女声配音（`zf_xiaoyi`）。约 5:16。

## 排名（揭晓顺序 5→1）
| # | 歌曲 | 难点 | 展示素材 |
|---|------|------|----------|
| 5 | 高妹正传 | 节奏/咬字/灵动，举重若轻 | 谷Live Studio Live (YT `x21sCp25pMA`) |
| 4 | 嫌弃 | 情绪拧、锋利不嘶吼 | 谷Live Studio Live (YT `qT1JYGOvE38`) |
| 3 | 烟雾弥漫 | 虚实切换、气息音准 | 甄爱SHE 4K修复MV (B站 `BV1Ho4y1r7bo`) |
| 2 | 花火 | 明亮+脆弱+飞起来不唱薄 | 谷Live Studio Live (YT `GMjsHM867YQ`) |
| 1 | 原来爱情这么伤 | 副歌走高+崩塌感，声音不能先阵亡 | weazegigi 4K修复MV (B站 `BV1aL411479N`) |

详见 `SOURCES.md`（选源/坑/crop）、`design.md`（视觉/节奏）。

## 复现
```bash
# 1. 配音（女声）
tools/tts/venv/bin/python build/narrate_segments.py
# 2. 素材切片+竖屏（raw/src_*.mp4 已下载；见 SOURCES.md 的窗口与 crop）
#    mkclip: ffmpeg -ss <S> -i raw/src_X.mp4 -t <L> -filter_complex "crop=...,letterbox" clips/vert_X.mp4
#    注意 嫌弃 源有 6.06s 视频起始偏移，须从 ≥6s input-seek 切，否则音轨被截
# 3. 建 master.wav + index.html
python3 build/full_build.py
# 4. 渲染：本机 HF 对「316s + 7 video」直接 render 会卡死在 "Starting frame capture"(0% CPU)
#    → 改用 graphics-only 透明层 + ffmpeg 合成（见 memory hyperframes-render-flaky-gpu）：
#    a) gfx/index.html = 删 <video>、背景 transparent 的纯图形版
PRODUCER_STREAMING_ENCODE_MAX_DURATION_SECONDS=900 \
  npx hyperframes@0.6.47 render --output gfx/graphics.mov --format mov --sdr -w 1   # 带 alpha 的 prores
#    b) footage 底轨 = 各 clip 从 0 trim 到对应段长后 concat → renders/footage_base.mp4
#    c) 叠加 + mux master.wav：
ffmpeg -i renders/footage_base.mp4 -i gfx/graphics.mov -i master.wav \
  -filter_complex "[0:v][1:v]overlay=0:0:format=auto[v]" \
  -map "[v]" -map 2:a -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k -shortest \
  renders/liangyongqi-hardest-top5.mp4
```
> 注：`gfx/graphics.mov`(~4.6G) 已清理，需要时按上面重渲；`build/render_watchdog.sh` 是直接 render 的看门狗（本机会卡死，仅留作记录）。

## 关键铁律（本期遵守）
- footage 窗 == 音乐窗（自带音轨即音乐，口型同步）；逐首 loudnorm I=-14。
- 渲染后必须用预混 master.wav **后期 mux**（HyperFrames 压平音频动态）。
- 成片画面无水印/网址/提示词/路径；letterbox 保原比例不放大。
- 每首连续 ~34s 副歌展示；不碎镜快闪。
- 最后一句固定引流 CTA（逐字照念），排在作品 outro 之后；outro 自身不带投票问句。
- 开头不暴露排名（封面+作品描述），片尾才列 1→5 榜单。

产物：`renders/liangyongqi-hardest-top5.mp4`（mux 后为准）。`renders/`、`raw/`、`*.mp4`、`master.wav` 已 gitignore。
