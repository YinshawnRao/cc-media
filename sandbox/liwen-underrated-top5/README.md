# 李玟（CoCo Lee）最被低估的5首歌（竖屏盘点 1080×1920）

倒数 05→01 解说盘点，男声 `zm_yunxi`。成片：`renders/liwen-underrated-top5.mp4`（mux 后为准）。

## 榜单（揭晓顺序 05→01）
- 05 《爱你是大麻烦》— Promise 承诺 2001（轻快遗珠，开场/封面曲）
- 04 《不爱你了》— Sunny Day 好心情 1998
- 03 《答案》— Sunny Day 好心情 1998（姚谦词/鲍比达曲，杨凡《美少年之恋》主题曲）
- 02 《过完冬季》— Di Da Di 暗示 1998（楼南蔚词/李正帆曲）
- 01 《默默爱你》— Sunny Day 好心情 1998（邬裕康词/Jim Lee曲，压轴）

## 选源 / 关键决策
见 `SOURCES.md`。要点：
- **不爱你了 / 过完冬季 / 默默爱你** = 真官方棚版 MV，本人全程在镜 → **耦合**（footage+音频同源同窗，口型同步）。
- **爱你是大麻烦**（Promise 冷门曲、无棚版 MV，官方频道是 B&W 户外 Live）→ 解耦：录音室音轨 + 同碟《So Crazy》官方 MV（1080p 红裙舞台，贴合"轻快"）。
- **答案**（官方 MV 是杨凡电影《美少年之恋》画面、本人零出镜）→ 解耦：官方录音室音轨 + 同碟《想你的365天》官方 MV（紫调本人特写）。
- 封面 = 第一首出场歌（#5）动态画面：intro 与 #5 footage 取 So Crazy 连续窗（T0=90s 正脸），封面切第一首不剪。
- 英文专辑名/歌名不进配音（Kokoro 中英混读差），口播用中文，英文只上屏幕卡。

## 复现
1. 配音：`tools/tts/venv/bin/python build/narrate_segments.py`（→ audio/*.wav）。
2. 源：`raw/` 下 YT 官方源（id 见 SOURCES.md）；YT 媒体 403 → `--extractor-args player_client=tv`。`*_aud.wav`=音轨，`socrazy_h264.mp4`=#5/intro 画面（AV1→H264 便于精确 seek）。
3. 人声段：`probe/vocal_analysis.json`（vocal_segments 各曲音轨，供对齐闸门，keys=vert_p*）。
4. 构建：`tools/tts/venv/bin/python build/full_build.py` → 内联切 footage（letterbox vfill，耦合用 mseek/解耦用 fseek）→ 过 `showcase_align.gate`(5/5 OK) → master.wav + clips_seg + **footage_track.mp4（单轨）** + index.html。
   - `SAMPLE=1` 只出 intro+#5+outro 样片；`HTML_ONLY=1` 跳过音频/footage 重建。
5. 渲染（**单 footage_track 避免 HF 多 video 帧0 协议超时**，--sdr）：
   `npx hyperframes render --output renders/full_raw.mp4 --sdr -w1`
6. mux：`ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/liwen-underrated-top5.mp4`

## 踩坑记录
- YT 媒体 CDN **403 Forbidden** → `--extractor-args "youtube:player_client=tv"` 走 DASH 救场（cookie 有效仍 403）。
- **官方"Official MV"未必有本人**：答案官方 MV 是电影画面、爱你是大麻烦官方上传是户外 Live → 必须抽帧核实，按解耦救场。
- **So Crazy 是热闹群舞 MV**（频繁大远景 + "So Crazy"/地球图形插屏）：无 30s 纯特写，正脸只在 60/65/90/155s → 封面取 t=90 正脸，展示段落在 131–163 群舞段（贴合"活泼灵动"）。
- AV1 输入端 seek 不准 → 抽帧/切窗用 output-side seek 或先转 H264。
- volumedetect 不能加 `-v error`（会吞 info 行）。
