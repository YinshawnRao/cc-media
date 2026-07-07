# 杨丞琳最被低估的5首歌

竖屏 1080×1920 音乐盘点，倒数揭晓 #5→#1，4:15。成片：`renders/yangchenglin-underrated-top5.mp4`。

## 排名（倒数揭晓顺序 = 播放顺序）
- #5 《怕》（2014 双丞戏 · 蒋笃全/谭志华）
- #4 《鱼鳃》（2013 天使之翼 · 小寒/吕康惟）
- #3 《折叠式爱情》（2010 雨爱 · 姚若龙/佳芳同学）
- #2 《自作自受》（2012 想幸福的人 · 蒋笃全/饶善强）
- #1 《冷战》（2008 半熟宣言 · 蒋笃全/韦景云）

> 5 首均非杨丞琳本人创作；文案口径不说「她写的」。选源/坑见 `SOURCES.md`。

## 复现
```bash
# 1) 配音（Kokoro 男声 zm_yunxi）
../../tools/tts/venv/bin/python build/narrate_segments.py
# 2) 竖屏化（letterbox，裁烧死歌词）— 已对 raw/ 跑过，产物在 clips/vert_*.mp4
#    怕 1920:885:0:0  鱼鳃 1920:1080:0:0  折叠式 1280:520:0:80  自作自受 1280:720:0:0  冷战 854:480:0:0
# 3) 人声段检测（含解耦《鱼鳃》的 studio 音轨）
../../tools/tts/venv/bin/python ../../tools/video/vocal_segments.py clips/vert_*.mp4 raw/yusai_audio.wav -o probe/vocal_analysis.json
# 4) build（master.wav + 展示段对齐闸门 + index.html）
../../tools/tts/venv/bin/python build/full_build.py
# 5) 渲染 + mux（分段渲染抗 GPU flake，--sdr）
bash build/render_parts.sh
```

## 结构
- `build/full_build.py` — 时间轴 + master.wav + HTML。支持「解耦」首（`music`/`music_start`/`foot_seek`）：
  《鱼鳃》无棚版 MV → studio 音轨 + 2013 Live 画面；其余 4 首耦合官方 MV。
- `build/narrate_segments.py` — 旁白文案（开场/各首转场/outro/固定 CTA）。
- 封面 = 第一首出场歌《怕》源 t163 特写，intro 与 #5 同源连续窗丝滑流入。
- 固定结尾 CTA 逐字照念，排在作品 outro 之后。

## QA 已核
- 1080×1920 h264 30fps / AAC 48k 立体声 / 255.45s；无 >1s 静音。
- 展示段对齐闸门 5/5 OK（解耦《鱼鳃》用 studio 音轨基准，覆盖 97%）。
- 各首副歌 mean ≈ -16~-17.7dB（差 ~1.3dB），旁白段 -24dB（ducking ~7dB）。
- 烧死歌词（怕/折叠式）已 letterbox 裁净，成片无水印/网址/烧词残留。

## 仍需人工耳/眼定夺
- **《鱼鳃》解耦**：studio 音轨 + Live 画面（口型不强求，已选侧脸为主的窗）。试听 `qa/yusai_showcase_earcheck.mp3`。
- 整片偏暗（多首 MV 本身暗调 + scrim/vignette），符合「克制/脆弱」基调；如需提亮可对 fg 加 eq 重渲。
- 《怕》展示段（开场）偏暗/偏中远景（为保住封面特写选了较后段副歌）。
