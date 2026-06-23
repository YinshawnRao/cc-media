# 名侦探柯南主题曲 影响力 TOP10（竖屏盘点）

成片：`renders/conan-theme-top10.mp4`（1080×1920，8:57，h264 + aac，倒数 10→1）。

## 形态
- **画面**：全程《名侦探柯南》官方动画画面（用户指定，**不含任何艺人 MV**）——
  剧场版用東宝官方 スペシャルムービー/予告，TV 主题曲用历代 OP/ED 动画。
- **音频**：干净录音室原曲（解耦——动画无口型问题），逐首 loudnorm 统一到 ~-14dB。
- **配音**：男声 `zm_yunxi`，开头 + 10 段转场 + 结尾 + 固定引流 CTA；**日文歌名不进配音**
  （TTS 念不了片假名/英文乐队名），靠"排名 + 剧场版/TV 关联 + 年代 + 口碑"叙述，歌名作屏幕文字。
- **设计**：暗底 + 柯南红(#e23b4e) 侦探调；歌名卡用 Hiragino Mincho（日文）+ 思源体。

## 榜单（倒数揭晓）
10 TWILIGHT!!! / King Gnu（独眼的残像 2025）· 09 恋はスリル… / 愛内里菜（OP8 2000）·
08 相思相愛 / aiko（五棱星 2024）· 07 運命のルーレット廻して / ZARD（OP4 1998）·
06 Time after time / 倉木麻衣（迷宫十字路 2003）· 05 クロノスタシス / BUMP OF CHICKEN（万圣节新娘 2022）·
04 謎 / 小松未歩（OP3 1997）· 03 Secret of my heart / 倉木麻衣（ED9 2000）·
02 渡月橋〜君想ふ〜 / 倉木麻衣（唐红的恋歌 2017）· 01 美しい鰭 / スピッツ（黑铁的鱼影 2023）。

选源与裁切明细见 `SOURCES.md`。

## 构建
```bash
PY=../../tools/tts/venv/bin/python
$PY build/narrate_segments.py        # 男声旁白 -> audio/*.wav
$PY build/full_build.py              # 切 footage + master.wav + footage_track + index.html
bash build/render_loop.sh            # HyperFrames 渲染（见下"渲染坑"）
ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/conan-theme-top10.mp4
```
重建档位：`AUDIO_ONLY=1`（只重建 master.wav，跳过 footage 重切）、`HTML_ONLY=1`（只重生成 index.html）。

## 关键坑（本期踩到，已沉淀进 CONVENTIONS/memory）
1. **YT cookie**：全量 `all_cookies.txt`（含 .google.com 登录态）+ `brew upgrade yt-dlp`(2026.3→2026.6) 解 bot 拦。
2. **12 个 `<video>` 让 HF 渲染挂死**（页面初始化同时建 12 个 frame-player → Chrome protocolTimeout 帧0超时，
   多/单 worker 都挂）。**解法：把 12 段 footage 拼成一条 `footage_track.mp4`，HTML 只挂 1 个 `<video>`**（轻、稳，一次过）。
3. **master.wav 103MB 别进 HF**：渲染挂 `silent.m4a` 占位、真音频后期 mux。
4. **#1 美しい鰭母带偏轻**：换响亮副歌窗(@196)即够，无需额外增益。

## 已知小瑕疵（柯南画面方案固有，可接受）
- 剧场版特报/特殊影片含**偶发的剧情台词字幕**（如「じゃあな…」），展示段窗口多数干净、仅个别帧出现。
- 个别展示段是剧场版**夜戏/暗场**，画面偏暗（属源画面）。
- 迷宫十字路(2003)特报仅 360p（老片源限制，brief 允许）。
- 第10、第2 在卡片入场瞬间，背景特报自带片名卡与歌名卡短暂同框（随即被展示段干净画面取代）。
