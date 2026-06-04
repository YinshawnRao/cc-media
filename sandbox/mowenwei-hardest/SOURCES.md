# 莫文蔚最难的5首歌 — 成片归档与复现说明

**成片**：`renders/mowenwei-hardest.mp4`（竖屏 1080×1920，约 3:45，h264+aac SDR）
**形式**：难度盘点，倒数 5→1（#1《广岛之恋》压轴，香槟金「公认天花板」角标）。按用户给定排名。
**风格**：暗夜祖母绿 + 香槟金配色（背景 #06140f → 香槟金 #e8c87e → 翡翠 #2fb089 → 暖象牙白 #f2ebdd），颗粒质感；女声旁白 `zf_xiaoyi`（用户指定开头/转场/结尾女声 → 全程女声）。
**字体**：Noto Serif SC（歌名/标题）+ JetBrains Mono（排名数字/番号）+ Cormorant Garamond italic（西文）+ Noto Sans SC（UI）。
**Hook**：反差——「都说她的歌好听又好唱 → 其实没一首好唱，公认最难」。
**用户要求落实**：① 片头**不暴露歌曲排名**，仅封面 + 作品描述，留悬念；② **片尾完整榜单回顾**（05→01 逐行揭晓，与旁白同步）；③ 副歌/精彩展示段给足（常规 SHOW=15s，压轴《广岛之恋》=20s）；④ 开头文案精简、快速进主题（intro 旁白压到 13.8s，#5 在 15.6s 进入）。
**用途**：本地测试，未发布。发布前需另行评估 YouTube / B站 源素材授权（见根 CLAUDE.md Copyright stance）。

## 揭晓顺序与素材来源（两边都查过 — 硬约束）

切片：`yt-dlp <URL> --cookies <ck> --download-sections "*<起>-<止>" -f "bv*[height<=1080]+ba/b[height<=1080]"`
竖屏：`tools/video/vfill.sh <in> clips/<out>_full.mp4 <crop>`，再 `ffmpeg -ss <start> -t <L>` 输出端切出 `clips/<out>.mp4`（展示段落在末 SHOW 秒、结尾锁特写/强帧）。

| # | 歌 | 选用源 | 平台 / 规格 | 取用段(原片) | crop | 对照(另一边)与取舍 |
|---|----|--------|------------|-------------|------|------------------|
| 封面/intro底/outro底 | 广岛之恋 | YT… 改用 **Bili `BV1Ls4y1C7AR`** 原版MV 1080P修复(黑白) | 1920×816 hevc | song 2:00–2:46 | 612:816:654:0 | 复用 #1 同源做开合呼应；首帧=song2:02 莫文蔚黑白正脸特写做封面 |
| 05 | 爱 | **YT `3vtYIj_qtwM`** 莫文蔚官方频道《爱》专辑MV | YT 1080×1080 方画幅 | song 0:58–1:34 | 440:780:648:95(上半身竖裁, 裁掉左侧[i]logo+「莫文蔚 karen mok」文字) | 对照 2023动感盛典Live(芒果TV台标+烧死歌词+广告角标)、2002金曲年代MV(标清) → **用户选官方专辑MV**(干净优雅, 静态慢推镜) |
| 04 | 如果没有你 | **YT `8XBfYgUGf9c`** 莫文蔚官方频道 回蔚巡迴·台北小巨蛋 LIVE | YT 1080p 立体声 | song≈3:18–3:53 | 864:1080:528:0 | 对照 Sony官方MV `pKNMIfF4Zg0`=绿调叙事剧情(无演唱特写) → **改用官方演唱会Live**(演唱特写充足、干净)；末帧锁莫文蔚动情麦前特写 |
| 03 | 扶摇 | **Bili `BV18W411F7Lb`** 剧版《扶摇》同名主题曲MV(1080蓝光) | Bili 1920×1072 | song 0:50–1:28 | 864:1072:528:0(裁右上腾讯视频台标) | OST → **用户明确：用电视剧主题曲MV**(杨幂沙场/飞天大场面, 贴合"气势型大歌")；展示段收在火焰「扶摇」书法字卡(官方片尾, 干净)。对照官方频道`aBb_KpL5CHY`=全程静态海报、爆爆看大喜=脱口秀无演出、B8tswAMISCI=上传者满屏字幕 → 全弃 |
| 02 | 呼吸有害 | **YT `rWNgAbfpWYs`** 莫文蔚官方频道《呼吸有害》Official MV (2020) | YT 1080p | song≈1:07–1:44 | 864:1080:528:0 | 对照 Bili `BV1kd1jYzEaF`「4K修复」=AI放大 → **选 YT 官方MV**(原生HD、伦敦夜景叙事、暖调特写、无台标无歌词) |
| 01 | 广岛之恋 | **Bili `BV1Ls4y1C7AR`** 原版黑白MV 1080P修复 | Bili 1920×816 | song 1:23–2:04 | 612:816:654:0 | **用户明确：用原版MV才有味道、黑白没问题**。对照 滚石官方`iuz6QvKxGPw`=480p标清+画面中下烧死歌词(更糊)、林志炫2025北京4K live(非张洪量原版) → 修复版=同原版内容、清晰度提到1920宽、无烧死歌词；压轴 SHOW=20s 收在 song2:04 莫文蔚黑白特写(与封面呼应) |

- **广岛之恋原版MV**：艺术蒙太奇(棋盘地/吊灯/黑白人像)，莫文蔚特写多在 song1:00–2:05 段；正片 song3:40+ 修复版接入另一支彩色MV(绿野外景, 不可用)，故压轴只取干净黑白段。
- **扶摇剧版MV**：该上传仅 ~1:32(剧场短版)，结尾自带火焰「扶摇」书法字卡 + 小字「LEGEND OF FUYAO」官方片名(非水印)。
- 旁白逐字稿见 `build/narrate_segments.py` / `narration.json`。

## Cookie 状态
- `sandbox/www.youtube.com_cookies.txt`、`sandbox/www.bilibili.com_cookies.txt` 均于 2026-06-01 当天刷新，全程有效。

## 复现步骤
1. 重下源切片（上表 URL+时间码，需有效 cookie）。
2. 配音（女声）：`tools/tts/venv/bin/python build/narrate_segments.py` → `audio/*.wav` + `narration.json`。
3. 竖屏化 + 切片：按上表 crop 跑 `vfill.sh` 得 `clips/vert_<song>_full.mp4`，再输出端 `ffmpeg -ss <start> -t <L>` 切 `clips/vert_<song>.mp4`（封面/底用 `vert_intro`=广岛 song2:00 段）。
4. 合成 + 音频：`python build/full_build.py` → `index.html` + `master.wav`（逐段 床→swell→展示 + 旁白 ducking + 逐首 loudnorm I=-14 + 整体 +3dB）。`MWW_SAMPLE=1` 出样片。
5. 渲染 + mux（HyperFrames 压平音频动态，必须后期 mux；本机随机帧崩 → 重试循环）：
   ```
   npx hyperframes render --output renders/full_raw.mp4 --sdr -w <n>   # 崩则重试/降 -w1
   ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/mowenwei-hardest.mp4
   ```

## QA 基线（成片已达标）
- **时长 / 编码**：3:44（224.07s），1080×1920 H.264 **SDR** yuv420p + AAC 192k。一次渲染成功（4 workers，未触发随机崩）。
- **跨歌副歌展示响度**：05 −14.8 / 04 −12.6 / 03 −13.7 / 02 −14.5 / **01 −12.3** dB（逐首 loudnorm I=−14 归一；压轴《广岛之恋》最响、符合"climax 最重"的盘点弧线；#4 live 源 RMS 偏高已压 1.5dB）。
- **ducking**：旁白段 −16.5 ~ −17.5dB（音乐床闪避 + 人声填充），低于展示段。
- **静音**：全片无 >1s（−35dB）整片静音。
- **画面**：逐段抽帧验证——无水印/网址/烧死歌词/路径/项目内部词；无描述视频自身机制的 meta 文案。#5《爱》已裁掉源画面左侧 `[i]` 专辑 logo+文字；#3《扶摇》已裁掉右上腾讯视频台标；#3 展示段干净收在火焰「扶摇」书法字卡。
- **节奏**：intro 旁白压到 13.8s、#5 在 **15.6s** 进入正题（快速进主题）；倒数 5→1，#1 香槟金「公认天花板」角标。
- **封面**：首帧=莫文蔚黑白正脸特写 + 香槟金「最难的5首」标题，**不剧透排名**（仅封面+作品描述），可直接作社交缩略图；与 #1 压轴黑白特写呼应。
- **片尾**：完整榜单回顾 05→01 逐行揭晓（暗底面板保证可读性），#1《广岛之恋》翡翠金高亮。
- 仍需人工耳/眼定夺：女声音色/语速听感、各首展示段是否最具代表性、广岛 480p→1080P修复 的清晰度可接受度。
