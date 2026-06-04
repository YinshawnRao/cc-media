# 丁世光为别人写的歌 TOP5（竖屏 1080×1920 音乐盘点剪辑作品）

**成片**：`renders/dingshiguang-others-top5.mp4`（≈4:03，h264 1080×1920 SDR/bt709 + aac，= `hf/renders/full_raw.mp4` 渲染 + 预混 `master.wav` 后期 mux）。
**形式**：**倒数盘点 #5→#1**，《心酸》压轴。**开头不剧透排名**（封面只给作品描述）；每首倒数中口播名次 + 大号排名卡揭晓；**结尾画面揭晓完整榜单 TOP1→TOP5**。每首展示完整副歌，副歌期纯音乐无旁白。女声旁白。本地测试，未发布。

## 榜单（用户给定排名）
1. 《心酸》林宥嘉 — 作曲·编曲 丁世光
2. 《Catherine》陶喆 — 作曲 丁世光
3. 《爱来过》S.H.E — 作曲 丁世光 / 作词 施人诚
4. 《肋骨》周笔畅 — 作曲 丁世光 / 作词 小寒
5. 《讽刺的情书》田馥甄 — 作词·作曲·编曲 丁世光

## 风格
- 黑金 / 暗底 + 单一强调色高级音乐杂志感；每首主题色（#1暖金压轴 / #2暗红黑白 / #3青春玫红 / #4冷蓝 / #5暖琥珀）。
- 字体：Noto Serif SC（标题/歌名）+ Noto Sans SC（UI/词曲）+ JetBrains Mono（名次数字）。
- 封面真人=**丁世光本人**（用户提供照片），圆头像 + 暗夜模糊底；封面只列作品(无序号)不剧透排名。
- 左侧倒数轨 05→01，当前名次高亮、已数过的标灰；#1《心酸》排名卡加金色「榜·首」角标 + 数字弹入强调。

## 结构（每段时长见 build 输出，TOTAL≈242.6s）
封面(4s) → 钩子/开场标题+"从第五名开始"(到24.2s) → 倒数 5 章节[排名卡(NO.+歌名+歌手+词曲+标签)→女声引入(音乐床+ducking)→swell→**完整副歌**展示(纯音乐+大字关键词+观点金句)→收束] → outro(揭晓TOP1→5 + 结尾字幕「他写给别人的歌，也是一部隐藏的丁世光作品集。」)。

## 素材源（两平台对照，详见 `SOURCES.md`）
#1心酸=红牛不插电Live(B站) / #2Catherine=4K修复MV(B站) / #3爱来过=2gether4ever演唱会影像(YT，画面)+录音室原声(montage救场) / #4肋骨=LUNAR巡演官方Live(YT) / #5讽刺的情书=官方MV(YT)。

## 复现
1. cookie：`sandbox/www.youtube.com_cookies.txt` / `sandbox/www.bilibili.com_cookies.txt`。B站搜索用 `tools/video/bili_search.py`。
2. 下源（见 SOURCES）→ `build/transcode.sh` 转 h264 到 `raw_h264/`，音轨抽 `raw/*.wav`（输出端 decode 全片避免 webm 截断）。
3. 配音（女声 zf_xiaoyi）：`tools/tts/venv/bin/python build/narrate_segments.py` → `audio/*.wav` + `narration.json`。
4. 合成+音频：`tools/tts/venv/bin/python build/full_build.py`（倒数序；每首 vseek 对齐副歌；#3 画面/音频解耦；逐段 床→swell→副歌 + ducking + 逐首 loudnorm I=-14 → `master.wav`；生成 `hf/index.html`）。
5. 渲染+mux：`bash build/retry_render.sh`（GPU截帧随机崩，-w1 重试 + --sdr）→ `bash build/finish.sh`（mux + QA 抽帧）。

## QA（工具验证）
- 画面：抽帧 `qa/final/`；封面真人丁世光 + 不剧透排名；5 张排名卡名次/歌名/歌手/词曲准确；各副歌段对应歌手特写；无水印/烧词/路径/meta 残留；SDR bt709。
- 音频：5 首副歌 -14.8~-16.8dB（差<2dB）；旁白段 ~-19.5dB（比副歌低 ~4.5dB，ducking）；无 >1.2s 整片静音。
- lint：0 error（仅 Google Fonts 字体 warning）。

## 仍需人工耳/眼定夺
- #3《爱来过》画面为 S.H.E 演唱会**金色群舞段**（能量偏青春活泼），与抒情原声解耦；若要更抒情的 S.H.E 画面可换源。
- 各首副歌展示段是否最具代表性；跨首响度听感。
