# dou-family-dbmh — 一家三口同唱一首歌

成片：[`dou-family-dbmh.mp4`](dou-family-dbmh.mp4)（4:49 / 1080×1920 / 30 fps / H.264+AAC / ~128MB）

**主题**：同一首《Don't Break My Heart》被窦唯、王菲、窦靖童唱出了三种气质——原点 / 回声 / 接住。  
**风格**：高级音乐纪录片 + 抖音精品盘点，克制漂亮有余味。  
**格式参考**：CONVENTIONS.md "AI 跨时空同台（音乐实验）" 加章节解说版（本片有完整章节文案而非纯接力）。

## 目录

```
production/dou-family-dbmh/
├── README.md             — 本文件
├── SOURCES.md            — 三条源 URL / 切点 / vfill crop 参数
├── dou-family-dbmh.mp4   — 成片（mux 后）
├── index.html            — HyperFrames composition（最终版）
├── meta.json / hyperframes.json / package.json  — HF 项目元数据
├── narration.json        — 11 段 TTS 文本 + 时长记录
├── scripts/
│   ├── build.py          — 生成 index.html（含 SECTIONS dict + 字体加载 + GSAP 时间线）
│   ├── build_audio.py    — 生成 master.wav（音乐床 + TTS + ducking + 三人接力）
│   ├── narrate_dou.py    — 11 段男声 zm_yunxi TTS 生成
│   └── qa.sh             — 抽帧 + silencedetect + volumedetect QA
├── voice/                — 11 段 Kokoro TTS wav（24kHz）
├── cover/                — 三张时代卡片静帧（已裁干净）
└── audio/master.wav      — 预混后的 48kHz stereo 总音轨
```

## 复现步骤（从零）

> 假设你在 `cc-media/` 仓库根目录，已装好 ffmpeg / yt-dlp / Node 22+ / Kokoro venv（见根 `CLAUDE.md`）。

```bash
# 1. 准备 sandbox 工作区（重新生成时不污染 production）
mkdir -p sandbox/dou-family-dbmh-rebuild/{raw,clips,voice,cover,audio,renders}
cd sandbox/dou-family-dbmh-rebuild

# 2. 下载三条源（cookie 见 sandbox/www.{youtube,bilibili}.com_cookies.txt）
#    URL 与命令见 ../../production/dou-family-dbmh/SOURCES.md
# ...（按 SOURCES.md 跑）...

# 3. 竖屏 vfill（参数见 SOURCES.md）
bash ../../tools/video/vfill.sh raw/douwei_heibao.mp4    clips/vert_douwei_full.mp4    "384:400:128:0"   "-0.18" "1.08"
bash ../../tools/video/vfill.sh raw/faye_budokan.mp4     clips/vert_faye_full.mp4      "1280:900:320:0"  "-0.32" "1.04"
bash ../../tools/video/vfill.sh raw/jingtong_singer2026.mp4 clips/vert_jingtong_full.mp4 "1280:900:320:90" "-0.30" "1.04"

# 4. 抽 cover 静帧（output-side seek，AV1 必需）
ffmpeg -y -i raw/douwei_heibao.mp4    -ss 135 -frames:v 1 -q:v 2 cover/final_douwei.jpg
ffmpeg -y -i raw/faye_budokan.mp4     -ss 165 -frames:v 1 -q:v 2 cover/final_faye.jpg
ffmpeg -y -i raw/jingtong_singer2026.mp4 -ss 237 -frames:v 1 -q:v 2 cover/final_jingtong.jpg
# 再 crop 干净（见 SOURCES.md cover crop）

# 5. 切 sub-clips（stream copy，instant）
# 9 个 sub-clip，命令见 SOURCES.md "Sub-clip 切片表"

# 6. 复用 production/dou-family-dbmh/scripts/ 里的脚本
cp ../../production/dou-family-dbmh/scripts/*.py scripts/
cp ../../production/dou-family-dbmh/scripts/*.sh scripts/
cp ../../production/dou-family-dbmh/{index.html,meta.json,hyperframes.json,package.json,narration.json} .

# 7. 生成 TTS（用 tools/tts/venv 跑 narrate_dou.py）
../../tools/tts/venv/bin/python scripts/narrate_dou.py

# 8. 生成 master.wav
python3 scripts/build_audio.py

# 9. （可选）重生成 index.html（如果改了文案/时间线）
python3 scripts/build.py

# 10. 渲染
npx --yes hyperframes@0.6.52 lint   # 必须 0 error
npx --yes hyperframes@0.6.52 render --quality draft --output renders/full.mp4

# 11. Mux master.wav 覆盖 HF 输出的音轨（HF 会压平动态）
ffmpeg -y -i renders/full.mp4 -i audio/master.wav \
  -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest \
  renders/dou-family-dbmh.mp4

# 12. QA
bash scripts/qa.sh renders/dou-family-dbmh.mp4
```

## 关键参数

- 整片时长：**289.5s = 4:49.5**
- 画幅：1080×1920 (9:16 竖屏)
- TTS：Kokoro `zm_yunxi` 男声，speed 0.95（中等偏慢纪录片节奏）
- 字体：Noto Serif SC（中文衬线主标）+ Cormorant Garamond italic（西文优雅）+ Noto Sans SC（UI）+ JetBrains Mono（数字/番号）
- 音频混音：HF 渲染后 mux master.wav 覆盖
- 响度：mean -18.6dB / max -0.9dB
- 静默：≤ 1.5s 自然停顿（无 ambient pad 兜底，用户偏好真静音 > 底床）

## 任务历程（迭代记录）

| 版本 | 改动 | 用户反馈 |
|---|---|---|
| V1 | 初稿 | 通过基本结构，发现 cover 王菲 blend 太朦胧、窦靖童芒果 TV 水印残留 |
| V2 | 修 cover 两张卡 + 加 freeze-trio | 接受 |
| V3 | 字体升级（Noto Serif SC 等）+ 标题卡上下分离 + 转场卡诗意大字 + 删 cta-fair | 1) 白噪音轰隆隆 2) 开头 5s 静止 3) t=4:31 文字重叠 |
| V4 | 删 ambient pad，封面压到 5.5s，整片 -8.5s，TTS 前移到 t=1.0，outro caption 错峰 | 三卡块底部遮挡标题 |
| V5 | 三卡块上移 180px（最低卡底从 y=1590 移到 y=1410，与标题留 78px 间距）| ✅ 验收通过 |

## 经验教训

详细总结见 [`/CONVENTIONS.md`](../../CONVENTIONS.md) "一家三口同唱 DBMH 验证补充" 章节。要点：

1. **用户对底床/白噪音零容忍** — 别用全片 ambient pad 兜底，自然短暂静音 OK
2. **短视频开头节奏** — 0-1s 必有动作、5s 内必进入实质内容
3. **AV1 输入侧 seek 不准** — 抽帧用 `-i ... -ss N`（output-side）
4. **TTS 中英混读问题** — 旁白避英文，字幕保留
5. **字体决定纪录片质感** — Google Fonts 直接 link，HF 自动 inline
6. **Section 时间线集中管理** — SECTIONS dict + JS 注入，调整时长一处改动
7. **Cover 三卡 + 标题块 collision** — 手算 (x,y,w,h)，留 ≥ 78px 安全间距
