# 谭咏麟最被低估的5首歌 — 选源记录

揭晓顺序：倒数 5→1（#1《还是你懂得爱我》压轴）。片头不剧透排名，片尾列完整榜单。
共性：五首均为冷门 deep cut，**无官方棚版 MV**；本人动态画面全部来自演唱会 Live（两平台都搜过，YT 多为 Topic 音频/歌词视频）。

## 元数据（research 已核对）

| # | 歌曲 | 专辑 | 年 | 词曲 | 备注 |
|---|---|---|---|---|---|
| 05 | 黄昏的声音 | 再见吧!?浪漫 | 1987 | 曲 谭咏麟 / 词 林敏骢 / 编 入江纯 | TVB《留住明天》主题曲；无MV |
| 04 | 此刻你在何处 | 爱情陷阱 | 1985 | 曲 芹泽广明 / 词 林敏骢（日曲改编）| 被同名主打盖住；无棚版MV |
| 03 | 永不想你 | 第一滴泪 | 1986 | 林敏骢 包办曲词 | 无MV |
| 02 | 墙上的肖像 | 墙上的肖像(同名) | 1987 | 曲 刘以达 / 词 陈少琪 / 编 周启生 | 达明一派班底；无MV（年份以 research 为准，待用户一瞥确认 1987 vs 1989）|
| 01 | 还是你懂得爱我 | 笑看人生 | 1991 | 曲 徐日勤 / 词 刘卓辉 | 慢歌首选佳作；无棚版MV |

## 最终选源（待下载+抽帧验证）

| # | 视觉源 | 规格 | 音频源 | 模式 |
|---|---|---|---|---|
| 05 | B站 BV1yCNcz6Ebr（2015 银河岁月40载 黄昏的声音 单曲，4k源；avc 1544x1080@60）→ raw/v_p5_alt.mp4 | 1544x1080 h264 立体声 | B站 BV1GYsDeUECy（1987 棚版【无损】）| **decoupled**（旧候选 BV13j421d7Hr 是电台反应视频，作废）|
| 04 | B站 BV1UN4y1j7QT（2015 40载 4K HDR Live）| 4K HEVC HDR（需 tonemap→SDR）| B站 BV1BD42157WA（1985 棚版无损）| **decoupled**（也可 synced，棚版更干净）|
| 03 | YT fhwe4r6tTAM（2004 左麟右李 开心演唱会 官方）| 480p 立体声 | 同源 Live | **synced**（备选 decoupled 棚版 YT 5lM9tVcsc0k）|
| 02 | B站 BV1xm4y1e7U3（2000 千禧 升频；avc 1920x1080@60 内含 4:3 1438x752）→ raw/v_p2_alt.mp4（**取代**旧 2005 浓情30年 v_p2.mp4：千禧无水印、特写更近）| 1920x1080（4:3 pillarbox） h264 立体声 | YT ENHXQfByeRs（1987 棚版 Universal）| **decoupled** |
| 01 | B站 BV18bxbz7E53（1994 大球场纯金曲 Live, 4K60 LD修复）| 2880x2160（升频）| YT Y6OESNs0DG4（棚版 Album Version 4:26）| **decoupled**（备选 synced live FLAC）|

兜底/备选：
- 05 视觉兜底：全场蓝光 BV1Gc411R7hr（60帧 HIRES）按时间码抠 medley 开场。
- 02 视觉次选：BV1xm4y1e7U3（2000 千禧 4K 升频）。
- 01 视觉次选：环球官方 BV1nD4y1o7uW（无水印但偏软）。

## 待验证项（抽帧后回填）
- 各 Live 源：UP主角标/台标/烧字位置 → 定 crop（默认 letterbox 全宽横带）。
- 各曲副歌连续段起止（见 research chorus_hint）→ 定展示窗 ≥27s。
- #4 HDR→SDR tonemap 是否到位（抽帧看色彩不发灰）。
- #5 medley 内谭咏麟特写是否够连续 27s（decoupled，可montage救场）。

## 音频策略
- 03 synced（同源 live）；其余 decoupled（棚版录音，画面单剪）。
- 全片逐首 loudnorm I=-14 统一响度；旁白段音乐 ducking。
