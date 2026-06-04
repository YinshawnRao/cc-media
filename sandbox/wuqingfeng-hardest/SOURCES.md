# 吴青峰最难的5首歌 — 成片归档与复现说明

**成片**：`renders/wuqingfeng-hardest.mp4`（竖屏 1080×1920，约 3:38，h264+aac SDR）
**形式**：难度盘点，倒数 5→1（#1《频率》压轴，紫→品红「公认天花板」角标）。按用户给定排名。
**风格**：夜空/极光配色（深墨蓝 #070b12 → 冰青 #5fe3d4 → 蓝 #7fb0ff → 紫 #b78bff；压轴用紫→品红 #ff6ec7 热点）。区别于梁博片的暖火配色，贴合青峰清亮/空灵/头声的气质。
**字体**：Noto Serif SC（歌名/标题）+ JetBrains Mono（排名数字/番号）+ Cormorant Garamond italic（西文）+ Noto Sans SC（UI）。
**Hook**：反差——「听起来像羽毛一样飘 → 实则华语最难'进入赛道'的唱法」。#1《频率》用「不是唱不上去，是连赛道都进不去」收口。
**配音**：女声 `zf_xiaoyi`（用户指定开头/转场/结尾女声 → 全程女声）。旁白逐字稿见 `build/narrate_segments.py` / `narration.json`。中英混读坑：旁白不放音名(C#3/A5)，改「两个八度/头声极限」，音名留屏幕字幕。
**用户偏好落实**：① 每首副歌/人声展示段加长（常规 SHOW=14s，压轴《频率》=18s），不刚听就切走；② 每首锁青峰本人连续特写、展示段结尾落在特写帧；③ 封面真人头像（青峰本人）。
**用途**：本地测试，未发布。发布前需另行评估 YouTube / B站 源素材授权（见根 CLAUDE.md Copyright stance）。

## 揭晓顺序与素材来源（两边都查过 — 硬约束）

切片：`yt-dlp <URL> --cookies <ck> --download-sections "*<起>-<止>" -f "bv*[height<=1080]+ba/b"`
竖屏：`tools/video/vfill.sh <in> clips/<out>_full.mp4 <crop> [br] [sat]`，再输出端切到 `clips/<out>.mp4`（结尾落在特写帧；展示=片段末 SHOW 秒）。

| # | 歌 | 选用源 | 取用段(原片) | crop | 对照(另一边)与取舍 |
|---|----|--------|-------------|------|------------------|
| 封面/intro底/片尾底 | 地心 | YT `qhCsATUqsqA` 歌手2019 E8[湖南卫视官方HD] | 00:48–01:12 | 864:820:528:0 | 取 t≈48–54 蓝光特写做封面首帧(1080p 清晰、青峰本人、冷色贴主题)；与 #3 展示段(不同段)区分，片尾复用做开合呼应 |
| 05 | 我好想你 | **B站 `BV1jy4y1976d`「2013 秋·故事 高雄预购握唱会」** | 03:26.5–04:06.5 | 864:1080:528:0 | 对照 ① YT `Zs8TRQ4PTYk` 官方MV=纯风景空镜无青峰；② YT `v-QRYgM_iRg` 十週年版=有QQ音乐水印+多远景 → **选 B站**（亲密红帽特写、画面干净无水印、青峰占比满）。音轨 mean −11dB 健康 |
| 04 | 起风了 | YT `4o0BD1KUL5g` 歌手2019 E3[湖南卫视官方HD] 1080p | 03:16–03:57 | 864:820:528:0 | 歌手官方纯享、暖品红舞台青峰特写多；芒果TV独播水印(右上)+底部烧死歌词 → 顶对齐裁切裁净 |
| 03 | 地心 | YT `qhCsATUqsqA` 歌手2019 E8[湖南卫视官方HD] 1080p | 02:21–03:02.5 | 864:820:528:0 | 同源蓝舞台、轻声到高位爆发特写；对照 B站 `BV1Z4411x7aN`「5.1声道蓝光」=同 footage 再压 → 选 YT 官方。展示段收在 t≈179 爆发特写 |
| 02 | 痛快的哀艳 | **B站 `BV1Lb411m7qf`「第27届金曲奖」(台視HD直播)** | 00:37.5–01:19 | 864:820:528:0 | 对照 ① 官方「痛快版/哀艳版」MV=纯管弦乐/概念无青峰；② 春浪Live=画面中部烧大歌词、无特写 → **选金曲奖**（蓝/品红光青峰特写在 t≈60–78，史诗交响编制贴合「大体量」）。台視/金曲27角标(顶角)+底部歌词 → 裁净 |
| 01 | 频率 | YT `OCdbpCKBx70`「小巨蛋演唱会版」官方MV | 00:57–01:41 | 384:440:120:0 | **源限制：此干净特写版仅 640×480 (4:3 SD)**。对照 B站 `BV1JhpezzEBa` 2025二十年一刻=1080p 但 UP水印+烧字+暖橙大远景青峰小、冷暖不符 → 仍**选 YT 官方**（暗台白衫青峰连续特写、cover级）。压轴 SHOW=18s 收在 t≈97 特写。**清晰度已回报用户**。 |

- **歌手2019 源（地心/起风了）**：芒果TV「独播」水印(右上) + 湖南卫视 logo(左上) + 底部烧死歌词 → 顶对齐居中裁 `864:820:528:0` 裁净（抽帧验证）。
- **金曲奖源（痛快的哀艳）**：「台視HD」(右上) + 「金曲27」(左上) + 底部卡拉OK歌词 → 同 `864:820:528:0`（角标在左右两端被 x 裁掉，底歌词被顶裁掉）。
- **频率 480p**：4:3 SD，干净特写但软；vfill 用较温和裁切 `384:440:120:0` 保锐度，BR=-0.18 不压暗前景。属源限制（最佳干净特写源只有 SD）。
- **我好想你**：B站秋故事 1080p 干净，`10.1预售` 角标仅出现在早段(非取用窗口)，取用段 03:26+ 无角标。

## 复现步骤

1. 重下源切片（上表 URL+时间码，需有效 cookie：`sandbox/www.youtube.com_cookies.txt` / `sandbox/www.bilibili.com_cookies.txt`）。
2. 配音（女声）：`tools/tts/venv/bin/python build/narrate_segments.py` → `audio/*.wav` + `narration.json`。
3. 竖屏化：按上表 crop 跑 `vfill.sh` 得 `clips/vert_<song>_full.mp4`，再 `ffmpeg -i full -ss <start> -t <L+0.5>` 输出端切出 `clips/vert_<song>.mp4`（结尾特写落在 clip-time = L）。
4. 合成 + 音频：`python build/full_build.py` → `index.html` + `master.wav`（逐段 床→swell→展示 + 旁白 ducking + 逐首 loudnorm I=-14 + 整体 +3dB）。
5. 渲染 + mux（HyperFrames 压平音频动态，必须后期 mux）：
   ```
   npx hyperframes@0.6.47 render --output renders/full_raw.mp4 --sdr
   ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/wuqingfeng-hardest.mp4
   ```
   本片实际续跑采用分段渲染避开长片 Chrome 内存累积问题：
   ```
   WINDOW=0,83 SEG=seg1 python build/seg_build.py
   (cd hf_seg1 && npx hyperframes@0.6.47 render --output ../renders/seg1.mp4 --sdr --workers 3)
   WINDOW=83,154 SEG=seg2 python build/seg_build.py
   (cd hf_seg2 && npx hyperframes@0.6.47 render --output ../renders/seg2.mp4 --sdr --workers 3)
   WINDOW=154,218.125 SEG=seg3 python build/seg_build.py
   (cd hf_seg3 && npx hyperframes@0.6.47 render --output ../renders/seg3.mp4 --sdr --workers 3)
   ffmpeg -f concat -safe 0 -i renders/segments.txt -c copy renders/full_segmented_raw.mp4
   ffmpeg -i renders/full_segmented_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/wuqingfeng-hardest.mp4
   ```

## 已知坑（本片记录）
- HyperFrames render 在本机对此 CJK 多字体重页偶发 auto-worker calibration 超时 → 回退 1 worker（仍出正确帧，只是慢）。如需 5 worker 可重试一次（字体已缓存后更易过）。
