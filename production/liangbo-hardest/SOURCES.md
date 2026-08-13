# 梁博最难的5首歌 — 成片归档与复现说明

**成片**：`liangbo-hardest.mp4`（竖屏 1080×1920，约 3:38，h264+aac）
**形式**：难度盘点，倒数 5→1（#1《灵魂歌手》压轴，猩红「公认天花板」角标）。按用户给定排名。
**风格**：暗火/灼烧配色（暖黑 #0b0908 → 琥珀 #ff9d3c → 猩红 #e23a2e），颗粒质感；女声旁白 `zf_xiaoyi`（用户指定开头/转场/结尾女声 → 全程女声）。
**字体**：Noto Serif SC（歌名/标题）+ JetBrains Mono（排名数字/番号）+ Cormorant Garamond italic（西文）+ Noto Sans SC（UI）。
**Hook**：反差——「看似松弛 → 实则华语最难复刻的强混现场」。
**用户偏好落实**：① 每首副歌/精彩人声展示段加长（常规 SHOW=14s，压轴《灵魂歌手》=18s），不刚听就切走；② 黑夜中选「梁博本人画面占比多 + 综合质量高」的一边。
## 揭晓顺序与素材来源（两边都查过 — 硬约束）

切片：`yt-dlp <URL> --cookies <ck> --download-sections "*<起>-<止>" -f "bv*[height<=1080]+ba/b"`
竖屏：`tools/video/vfill.sh <in> clips/<out>.mp4 <crop> <bgBrightness> <sat>`
展示段取该首副歌/高潮的梁博特写，把片段**结尾 trim 到特写帧**（展示=片段末 SHOW 秒）。

| # | 歌 | 选用源 | 取用段(原片) | crop | 对照(另一边)与取舍 |
|---|----|--------|-------------|------|------------------|
| 片头封面/片尾底 | — | YT `Psr28JFrx_s`《灵魂歌手》歌手2017[我是歌手官方频道] | 03:45–04:07 | 864:820:528:0 | 复用 #1 climax 片段做开合呼应；首帧=03:45 正脸特写做封面 |
| 05 | 男孩 | YT `8GmYYyzT_Rs` 歌手2017 MangoTV 纯享 1080p 立体声 | 03:11–03:46 | 864:820:528:0 | 对照 B站 `BV14jzQYhEtU`「4K修复」=AI 插帧放大+音频仅89k(疑单声道)，脸蜡感 → **选 YT** |
| 04 | 出现又离开 | YT `d8CdjWJubU0` 我是唱作人 iQiyi 纯享 1080p 立体声 | 02:40–03:16 | 864:1080:528:0 | 对照 ① B站 `BV17ZL66SEgs`「4K Hires」=同一我是唱作人 footage 再传(带iQiyi台标)；② 梁博官方`BV1Qf4y127R8`《昼夜本色》=B&W 钢琴版，与全片彩色舞台调性不一致→弃。多机位有反应镜头，展示段末~6s 锁梁博连续特写 |
| 03 | 黑夜中 | **B站 `BV1gV411T7cQ`「尖叫之夜」真4K(取1080p流) hevc 立体声** | 03:15–03:49 | 864:1080:528:0 | 对照 YT `0yAm9i5xYxk` 浙江卫视年中盛典官方HD=舞台 LED 满屏 OPPO Reno 赞助商 logo + 梁博特写少 → **选 B站**（梁博本人画面占比多、暗台干净无赞助商、更摇滚）。按用户第2点要求 |
| 02 | 表态 | YT `wiCmV8YSZWM` 我是唱作人 iQiyi 纯享 1080p 立体声 | 05:21–05:55 | 864:1080:528:0 | 对照 B站 `BV1ze411S7Gn`「Hi-Res」=歌词/录音棚视频(非现场动态) → **选 YT**；末段 05:35–05:55 连续梁博麦前特写 |
| 01 | 灵魂歌手 | YT `Psr28JFrx_s` 歌手2017 [我是歌手官方频道] 1080p 立体声 | 03:05–03:45 | 864:820:528:0 | 对照 B站 `BV1NRzfYUEJo`「4K修复」=AI 放大+音频89k → **选 YT**；压轴 SHOW=18s 收在 03:45 正脸特写 |

- **歌手2017 源（男孩/灵魂歌手）**：底部有烧死歌词 + 芒果TV 角标 → **顶对齐裁切 864:820:528:0** 裁净（已抽帧验证）。
- **iQiyi 我是唱作人源（出现又离开/表态）**：右上 iQiyi 台标 + 左下小角标，无中部烧死歌词 → 居中满高 864:1080:528:0（裁掉左右角标）。
- **B站 尖叫之夜（黑夜中）**：暗台干净，左下小角标 → 居中满高裁掉。
- 旁白逐字稿见 `build/narrate_segments.py` / `narration.json`。

## 复现步骤

1. 重下源切片（上表 URL+时间码，需有效 cookie：`sandbox/www.youtube.com_cookies.txt` / `sandbox/www.bilibili.com_cookies.txt`）。
2. 配音（女声）：`tools/tts/venv/bin/python build/narrate_segments.py` → `audio/*.wav` + `narration.json`。已归档。
3. 竖屏化：按上表 crop 跑 `vfill.sh` 得 `clips/vert_<song>_full.mp4`，再 `ffmpeg -ss <start> -t <L+1>` 输出端切出 `clips/vert_<song>.mp4`（结尾落在特写帧；start = 特写时刻 − L）。
4. 合成 + 音频：`python build/full_build.py` → `index.html` + `master.wav`（逐段 床→swell→展示 + 旁白 ducking + 逐首 loudnorm I=-14 + 整体 +3dB）。
5. 渲染 + mux（HyperFrames 压平音频动态，必须后期 mux）：
   ```
   npx hyperframes render --output renders/full_raw.mp4 --sdr
   ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/liangbo-hardest.mp4
   ```

## QA 基线（成片已达标）

- **时长**：3:37（216.7s），1080×1920 H.264 **SDR** + AAC 192k。
- **跨歌响度统一**：五首副歌(SHOW)均值 **−15.0 ~ −16.0dB**（彼此差 <1dB）；master 整体 +3dB(MASTER_GAIN=1.4)。
- **ducking**：旁白段总响度 ~−17dB（音乐床 ducking 到 ~−14dB，人声填充），明显低于副歌展示段。
- **静音**：全片唯一 >1s 的 −35dB 段是 **40.04–41.06（1.02s）**——《男孩》副歌炸入前**歌曲本身的戏剧性停顿**（源自带，非制作空档），画面为梁博闭眼特写、其后副歌即起；属自然短暂停顿(≤1.5s)，符合用户偏好（真静音 > 任何填充/白噪音）。其余无 >1s 静音。
  - 注：为压短此处停顿，已把 `audio/p5_nanhai.wav` 的 ~1.1s 尾部静音 trim 到 17.95s（原档 `audio/p5_nanhai.orig.wav`），并把 swell 起点设在旁白内容结束即起（`sw=ne_loc`）、床位 `BED_N=0.20`。
- **画面**：无水印/网址/烧死歌词/路径/项目内部词；无描述视频自身机制的 meta 文案。倒数 5→1，#1 猩红「公认天花板」角标；**首帧=梁博正脸特写 + 「梁博 / 最难的5首」标题**（可直接作社交缩略图）。
- **素材取舍兑现用户两点**：① 每首展示段加长（常规 SHOW=14s、压轴《灵魂歌手》18s，不"刚听就切走"）；② 《黑夜中》选 B站尖叫之夜（梁博本人画面占比多 + 干净）。
