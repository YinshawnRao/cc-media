# 没有张雨生，就没有最初的阿妹

竖屏长片（9:16 · 1080×1920 · 9:23 · H.264 SDR）。从"伯乐/制作人/引路人"视角，讲张雨生如何看见张惠妹、把她推向天后之路。8 首倒数（8→1）+ 片尾彩蛋《听你·听我》。

- **成片**：`zys-amei-bole.mp4`（已 mux 预混 master.wav）。
- **结构**：封面 → 开场钩子 → 第8…第1 → 彩蛋《听你·听我》→ 结尾。倒数顺序≈时间线 1996→2000。

## 事实口径（与原 brief 的修正，已落到上屏字幕）

1. **#8《最爱的人伤我最深》= 张雨生自己EP《两伊战争—红色热情》(1996) 的男女对唱**，张雨生只**合唱**（词邬裕康/曲陈志远），非他词曲。卡片只标"合唱"。
2. **彩蛋《听你·听我》不是张雨生写的**：词光禹/曲陈志远，1997《给雨生的歌》慈善单曲（他车祸昏迷期间录），**张惠妹原唱**。卡片标"阿妹献给雨生 · 词光禹/曲陈志远"，绝不标他为词曲。
3. 全片口径 = 张雨生**写+制作了阿妹早期最重要的几首主打 / 挖掘了她**，**不说"他制作了整张专辑"**（两张专辑均多制作人；他做的是单曲）。#2/#1 标"遗作"。

## 选源（7 首官方MV + 2 首 Live；均 letterbox 保原比例、裁烧词/水印、无台标泄漏）

| # | 歌 | 源 | 备注 |
|---|---|---|---|
|8|最爱的人伤我最深|YT官方MV `bM70w2VT0So`|剧情片不露二人；真·师徒同框只在 B&W 录音棚 ~206-211s → 做师徒蒙太奇(+雨生资料egg~70s+姊妹绿幕)；音乐用官方对唱录音 chorus~90s|
|7|水蓝色眼泪|**无官方MV** → YT 4K Live `UnXfMWk7OpY` ~236s|选干净4K(避河岸留言UP主水印)，画面为现代阿妹(年代不符的取舍)|
|6|姊妹|YT官方MV `OO60xtWjLRw` (原版1600×1080) ~140s|绿幕正脸近景；烧词 crop `1600:930:0:20`|
|5|一想到你呀|YT官方MV `W51yU6cyj7Y` ~170s|群舞明亮段；crop `712:392:0:14`|
|4|孤单Tequila|**无官方MV** → YT 2010可乐Live `JAtskxs2qiM` ~150s|裁"Rec by LCH"角标+烧词(`1280:740:80:150`)；阿妹偏远景(最弱环)|
|3|Bad Boy|YT官方MV `FCNVAWwh9CQ` ~125s|红亮片标志造型 hook(f130)；crop `712:410:0:12`|
|2|当我开始偷偷地想你|YT官方MV `r4cYExeaHGk` ~150s|官方MV是舞曲图形风(非"安静")；crop `712:368:0:8`|
|1|不顾一切|YT官方MV `p7FMwynG9Ko` ~216s|火墙 finale；crop `696:316:8:66`|
|彩蛋|听你·听我|YT官方MV `L8DyqVFH6Bo`|纪念MV：雨生资料(~70s)+阿妹录音棚演唱(~158s)做纪念蒙太奇|

cookies：`sandbox/www.youtube.com_cookies.txt` / `…bilibili…`。AV1 切片必须 **output-side seek**。

## 重建步骤

依赖原始素材（`sandbox/zys-amei-bole/raw/*`，已 gitignore，按上表 yt-dlp 重下）+ `tools/`。

```bash
cd sandbox/zys-amei-bole
tools/tts/venv/bin/python build/narrate_segments.py   # 19 段旁白 wav（男声 zm_yunxi）
bash build/prep_pilot.sh        # s8 师徒蒙太奇 clips/vert_s8.mp4
bash build/prep_egg.sh          # 彩蛋纪念蒙太奇 clips/vert_egg.mp4
python3 build/full_build.py     # footage(letterbox) + master.wav + hf/index.html
cd hf && npx hyperframes render --output renders/full_raw.mp4 --sdr -w1   # ~15min(GPU截帧随机崩→-w1+重试)
ffmpeg -i renders/full_raw.mp4 -i ../master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest ../zys-amei-bole.mp4
```
仅改文案/排版：`HTML_ONLY=1 python3 build/full_build.py`（跳过 footage 重切）。

## 已知取舍（源限制）
- **s4 孤单Tequila / s7 水蓝色眼泪 全网无官方MV**，只能用 Live；s4 远景、s7 现代阿妹。
- **s2 当我开始偷偷地想你** 官方MV是舞曲图形风，非旁白要的"安静"，但按"官方优先"用了它。

## QA（成片）
副歌 −14~−16.6 dB / 旁白 −23.9 dB（ducking 一致）；无 >1.5s 静音；letterbox 保原比例；全片无台标/水印/网址/路径；lint 0 error。
