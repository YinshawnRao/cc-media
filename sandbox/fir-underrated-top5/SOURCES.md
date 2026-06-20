# Sources — 飞儿乐队最被低估的5首歌

Cookie 文件已核对：YouTube `sandbox/www.youtube.com_cookies.txt` 结构合格；B站搜索与下载脚本可用。

选源规则：每首都查了 YouTube + B站。YouTube 五首都有 Timeless Music 官方完整版 MV；B站有对应官方/修复/Live 候选。最终优先选择 1080p、立体声、无额外平台/UP 水印且能通过全宽横带 crop 清掉污染的版本。成片画面不显示平台名、URL、路径或来源标签。

## 5. 《眷恋》
- YT: `tN5KvUXrUdw` | Timeless Music 官方 MV | 1600×1080 AV1，约 1.17 Mbps | 底部歌词。
- B站: `BV1DK411V7XJ` | 1080P 修复 MV | 1920×1080 H.264，约 3.83 Mbps，AAC 立体声 | 底部歌词，可 crop。
- 选择：B站修复版。展示窗 `176s` 起，crop `1920:960:0:40`。理由：画质明显优于 YouTube，未见额外平台/UP 水印，底部歌词可通过全宽横带裁掉大部分。

## 4. 《天天夜夜》
- YT: `HXmZiylxAsw` | Timeless Music 官方 MV | 960×720 AV1，立体声 | MV 自带中左/底部歌词图文。
- B站: `BV1KU4y1Y7Tz` | 1080P 修复 MV | 1920×1080 H.264，约 3.32 Mbps，AAC 立体声 | MV 自带中左/底部歌词图文。
- Live 补查：YT `dWnOSZDsuLA`、B站 `BV19b411e7Tg` 均有电视台台标/字幕，且 B站 Live 仅 768×432。
- 选择：B站 1080P 修复 MV。展示窗 `67.9s` 起，crop `1920:1000:0:40`。已知限制：MV 自带歌词图文无法完全裁净；Live 候选污染更重，因此保留画质更高的 MV。

## 3. 《后乐园》
- YT: `lj3ZmTahRgA` | Timeless Music 官方 MV | 712×480 VP9 | 底部歌词。
- B站官方: `BV17q2TBPEuz` | 华纳音乐中国 | 640×336 H.264 | 低清。
- B站修复: `BV1dL411P7dK` | 1080P 重制版 | 1920×1080 H.264，约 5.14 Mbps，AAC 立体声 | 顶部 B站字样 + 底部歌词，均可 crop。
- 选择：B站 1080P 重制版。展示窗 `168.8s` 起，crop `1920:850:0:115`，抽帧确认顶部平台字样和底部歌词都被裁掉，主体完整。

## 2. 《把爱放开》
- YT: `Y0KEJySOSN4` | Timeless Music 官方 MV | 640×480 AV1，立体声 | 底部歌词。
- B站: `BV1TVeVzDEBv` | MV 候选 | 1920×1080 H.264，约 2.72 Mbps，AAC 立体声 | 底部歌词，可 crop。
- 选择：B站 1080P MV。两个候选窗对比后选择 `38s` 起：人声连续约 40 秒；`174s` 后段画面更戏剧化但人声连续只有约 19 秒，容易拖入非唱段。crop `1920:960:0:55`。

## 1. 《应许之地》
- YT: `dM5ye9A0llg` | Timeless Music 官方 MV | 712×480 AV1，立体声 | 底部歌词/片尾标题。
- B站: `BV1Cb411S7jA` | 应许之地 MV | 1920×1080 H.264，约 5.84 Mbps，AAC 立体声 | 片尾有大号源片标题。
- 选择：B站 1080P MV。第一版用 `119s` 中段窗，QA 发现展示中段落到剧情人群，不够压轴。已改为 `294s` 终章窗，crop `1920:720:0:0` 裁掉底部大号“F.I.R. 应许之地”源片标题，保留 Faye/乐队画面。展示时长 25s，避免拖到结尾黑场。

## QA 记录
- 源候选 contact sheet：`qa/cmp_*.jpg`、`qa/crop_*.jpg`。
- 最终成片：`hf/renders/fir-underrated-top5.mp4`。
- HyperFrames lint：0 errors；2 个字体相关 warning。inspect：8 个 sample，0 layout issues。
- 容器：1080×1920 H.264, BT.709 SDR, AAC stereo, 291.125s。
- 音频：`silencedetect=n=-35dB:d=1` 无静音段输出；`volumedetect` mean `-17.3 dB`, max `-1.1 dB`。
- 最终抽帧：`qa/final_timeline_sheet.jpg`、`qa/final_showcases_sheet.jpg`、`qa/final_p1_segment_scan.jpg`、`qa/final_cover.png`、`qa/final_cta.png`。
- 抽帧结论：排序 5→1 正确；#1《应许之地》已换为终章 Faye/乐队窗口；CTA 正常；未见平台名、URL、路径、提示词或额外 UP 水印。#4《天天夜夜》保留 MV 自带歌词图文，原因见上方候选对比。
