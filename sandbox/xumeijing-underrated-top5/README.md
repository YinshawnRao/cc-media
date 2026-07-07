# 许美静最被低估的5首歌（竖屏盘点 1080×1920）

倒数 05→01 解说盘点，男声 `zm_yunxi`，约 5:27。成片：`renders/xumeijing-underrated-top5.mp4`（mux 后为准）。

## 榜单（揭晓顺序 05→01，按用户给定排名 1~5 倒数）
- 05 《玫瑰》— 蔓延 1997
- 04 《放你在心里》— 都是夜归人 1997
- 03 《别走》— 都是夜归人 1997（陈佳明词曲）
- 02 《答案》— 都是夜归人 1997
- 01 《迷乱》— 都是夜归人 1997（压轴）

## 选源 / 关键决策
见 `SOURCES.md`。要点：
- 迷乱/放你在心里 有真官方 MV（耦合，footage+audio 同源）；迷乱用 B站「拾光映画馆」SeedVR2 AI 修复版（远优于原始 640×480）。
- 答案/别走/玫瑰 无官方 MV（YouTube VEVO 15 曲 + B站两份粉丝合集穷举确认）→ 解耦：干净数字专辑音轨 + 她本人其他官方 MV 画面救场（答案←遗憾／别走←铁窗／玫瑰←漩涡），三条画面视觉分散不重复。
- YouTube 侧本期遇到系统性下载 403（yt-dlp 已升级最新版仍复现，非本曲目专属），素材实际全部落地 B站；YT 侧逐曲比对结论一致（该三曲确无官方 MV，非误判）。
- 封面按「盘点类封面=第一首出场歌动态画面」硬约束：intro 与 #5（玫瑰）取自同一条漩涡素材的连续窗，画面不剪不跳，T0 定格在她正脸微笑望镜头的高质量帧。

## 复现
1. 配音：`tools/tts/venv/bin/python build/narrate_segments.py`（→ audio/*.wav）。
2. 源：`raw/` 下 B站源（bvid 见 SOURCES.md），`p*_aud.wav`=各曲录音室/数字专辑音轨。
3. 竖屏化：各 `clips/vert_*.mp4`（vfill.sh，crop 见 SOURCES.md 表）；`vert_intro.mp4`/`vert_outro.mp4` 分别切自 p5/p1 素材的连续窗。
4. 人声段：`tools/tts/venv/bin/python tools/video/vocal_segments.py raw/p*_aud.wav -o probe/vocal_analysis_raw.json`，再按 clip 名 remap 成 `probe/vocal_analysis.json`（解耦曲目人声基准 = 各自数字专辑音轨，非 footage donor 的音轨）。
5. 构建：`tools/tts/venv/bin/python build/full_build.py` → 过 `showcase_align.gate`（5/5 OK）→ master.wav + clips_seg + footage_track.mp4（单轨）+ index.html。
6. 渲染（单 footage_track 避免 HF 多 video 帧0 协议超时）：
   `npx hyperframes@0.6.69 render --output renders/full_raw.mp4 --sdr -w2`
7. mux：`ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/xumeijing-underrated-top5.mp4`

## 踩坑记录
- **YouTube 系统性 403（2026-07）**：yt-dlp 2026.6.9 最新版，任意 YouTube 视频（含与本项目无关的测试视频）下载一律 403，搜索/元数据不受影响。判断为环境级 CDN/token 问题，非 cookie 过期（`check_yt_cookie.py` 通过）。全部素材改走 B站。
- **展示段画面窗口需要比人声窗口更宽的安全边界**：#2 答案的画面救场素材（遗憾 MV）在源 t≈203-206 附近仍有群像镜头残留，首版 `vis_off=205` 卡在边界上，展示段开头 1-2s 露出多人镜头；细化抽帧定位实际干净窗口从 t≈206 才稳定开始，`vis_off` 改到 208（多留 2-3s 余量）后二次渲染修复。**教训：数据点稀疏抽帧找到的"干净"边界要多留 2-3s 余量，不要卡着最后一个干净采样点定窗口**。
- **ffmpeg `-ss` 对 WAV 的 seek 在本机环境不可信**：QA 阶段用 `ffmpeg -ss T -i master.wav ... volumedetect` 抽查 ducking 效果，测出"旁白段音乐几乎没被压低"的假警报；用 Python `wave` 模块直接按采样偏移读取后发现实际 ducking 完全正常（bed ~-46~-51dB vs show ~-11~-18dB，差 30+dB）。根因是 `-ss`（无论放 `-i` 前后）在这台机器上对纯 PCM WAV 的定位存在明显偏差，不能用于精确到零点几秒的音频窗口抽查；**改用 Python `wave`/`numpy` 直接按 sample offset 读取**才是可信的验证方法，或对渲染后的 MP4（AAC/H.264）做同样的 sample-level 检查。
