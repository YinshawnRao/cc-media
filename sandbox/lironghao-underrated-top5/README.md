# 李荣浩最被低估的5首歌（竖屏盘点 1080×1920）

倒数 05→01 解说盘点，男声 `zm_yunxi`，约 5:02。成片：`renders/lironghao-underrated-top5.mp4`（mux 后为准）。

## 榜单（揭晓顺序 05→01）
- 05 《成长之重量》— 电影《动物世界》主题曲 2018
- 04 《王牌冤家》— 耳朵 2013
- 03 《落俗》— 李荣浩（同名专辑）
- 02 《满座》— 有理想 2016
- 01 《野生动物》— 有理想 2016（压轴）

## 选源 / 关键决策
见 `SOURCES.md`。要点：YouTube + B站逐曲实测码率/音频，5曲中3首选B站(华纳音乐中国)、2首选YT，非固定偏向单边；《成长之重量》无本人官方MV（电影方"成长版"宣传片全是剧情+发布日期宣传条），改用浙江卫视《亚运好声音》Live 单机位连续片段，letterbox 裁掉台标+歌词字幕+活动角标双水印带。

## 复现
1. 配音：`tools/tts/venv/bin/python build/narrate_segments.py`（→ audio/*.wav）。
2. 源：`raw/` 下各曲全片 mp4 + `*_aud.wav`（PCM 提取音轨，避免 -ss 截断坑）。
3. 竖屏化：`clips/vert_*.mp4`（vfill.sh letterbox，crop 见 SOURCES.md）；`vert_intro.mp4`/`vert_outro.mp4` 分别截自 #5《成长之重量》intro 前一段（与 #5 展示段源时间码首尾相接，封面→#5 无缝）与 #1《野生动物》后段副歌（与 outro 音乐床同源同窗）。
4. 人声段：`probe/vocal_analysis.json`（`vocal_segments.py` 各 vert clip，供对齐闸门）。
5. 构建：`tools/tts/venv/bin/python build/full_build.py` → 过 `showcase_align.gate`(5/5 OK) → master.wav + clips_seg + footage_track.mp4（单轨）+ index.html。
6. 渲染：`npx hyperframes@0.7.26 render --output renders/full_raw.mp4 --sdr`
7. mux：`ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/lironghao-underrated-top5.mp4`

## 展示段对齐闸门（5/5 OK）
- p5_chengzhang: 覆盖 85%
- p4_wangpai: 覆盖 77%
- p3_luosu: 覆盖 97%
- p2_manzuo: 覆盖 81%
- p1_yesheng: 覆盖 98%
