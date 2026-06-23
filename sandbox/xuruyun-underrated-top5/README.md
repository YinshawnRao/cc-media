# 许茹芸最被低估的5首歌（竖屏盘点 1080×1920）

倒数 05→01 解说盘点，男声 `zm_yunxi`，约 5:01。成片：`renders/xuruyun-underrated-top5.mp4`（mux 后为准）。

## 榜单（揭晓顺序 05→01）
- 05 《半首歌》— 如果云知道 1996
- 04 《白纸黑字》— 只说给你听 2001（许茹芸参与谱曲）
- 03 《忘》— 真爱无敌 1999（许茹芸词曲自创）
- 02 《透气》— 你是最爱 1998（戴佩妮词曲）
- 01 《学琴的孩子》— 你是最爱 1998（压轴）

## 选源 / 关键决策
见 `SOURCES.md`。要点：半首歌/透气/学琴的孩子 官方频道版是**静图+音频**非真 MV → 解耦（官方录音室音轨 + 本人其他官方 MV 画面救场，5 种不同视觉分散）；白纸黑字/忘 是真 MV；学琴用《美夢成真》本人特写蒙太奇（避开该 MV 的男主剧情）。

## 复现
1. 配音：`tools/tts/venv/bin/python build/narrate_segments.py`（→ audio/*.wav）。
2. 源：`raw/` 下 YT 官方源（id 见 SOURCES.md），`*_aud.wav`=录音室音轨，`fp*/fc*`=画面救场 MV 代理。
3. 竖屏化：各 `clips/vert_*.mp4`（内联 letterbox vfill，crop 见 SOURCES.md）；学琴为 3 段特写蒙太奇 concat。
4. 人声段：`probe/vocal_analysis.json`（vocal_segments 各曲音轨，供对齐闸门）。
5. 构建：`tools/tts/venv/bin/python build/full_build.py` → 过 `showcase_align.gate`(5/5 OK) → master.wav + clips_seg + **footage_track.mp4（单轨）** + index.html。
6. 渲染（**单 footage_track 避免 HF 多 video 帧0 协议超时**，-w1 重试 + --sdr）：
   `npx hyperframes@0.6.69 render --output renders/full_raw.mp4 --sdr -w1`
7. mux：`ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/xuruyun-underrated-top5.mp4`

## 踩坑记录
- **HF 长片多 `<video>` 帧0 协议超时**：7 段 footage 各挂 1 个 video → work dir 内联 1.2GB → Chrome 卡死 0 帧。改拼**单条 footage_track.mp4** 只挂 1 个 video（轻量模式）后正常。
- 许茹芸 late-90s 多为剧情 MV（突然想爱你/美夢成真都有男主）→ 解耦画面要逐帧避开男主/文字卡。
- volumedetect 不能加 `-v error`（会吞 info 行）。
