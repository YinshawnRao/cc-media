# QA

## 渲染前检查

- `clip_plan.json` 确认每首人声入点提前进入旁白尾部，full-music 段不是纯器乐。
- `qa/clips/vert_*_sheet.jpg` 已抽帧查看：
  - `vert_cover_sheet.jpg`：《暧昧》片段，适合作封面底片。
  - `vert_aimei_sheet.jpg`：画面干净，概念 MV 无平台水印；已延长展示段，覆盖副歌尾段。
  - `vert_youchai_sheet.jpg`：Live 源主体清晰，优于官方 Karaoke 裁后小画面。
  - `vert_qizi_sheet.jpg`：红色 MV 段，裁掉底部字幕后主体完整。
  - `vert_xiaowangshu_sheet.jpg`：Betacam 源干净，无烧死字幕；已延长展示段，覆盖副歌尾句。
  - `vert_anyong_sheet.jpg`：全宽横带裁掉底部歌词，主体可见。
- 预切竖屏片段均为 H.264 + AAC stereo，1080x1920。
- 固定 CTA 文案已作为全片最后一句旁白：

```text
你最想为哪一首投票？评论区告诉我。记得点赞、收藏、关注我，下一期，可能就盘到你单曲循环过的那一首。
```

## 待最终渲染后回填

## 最终渲染结果

最终文件：

```text
renders/wangfei-saddest-top5.mp4
```

`ffprobe`：

- duration: `322.512000`
- size: `215018715`
- video: H.264, 1080x1920, 30 fps
- audio: AAC, stereo, 48 kHz

## HyperFrames 检查

- `hyperframes lint`: 0 error, 3 warning。
  - `timeline_track_too_dense` x2：单文件时间线较长，可维护性提示，不影响渲染。
  - `font_family_without_font_face` x1：渲染时已自动抓取并注入 `Noto Sans SC` / `Noto Serif SC`；`PingFang SC` / `Songti SC` 作为 fallback 未阻塞。
- `hyperframes inspect`: 本机启动后在 navigation 阶段 10s timeout，未能产出布局报告；改用最终 contact sheet + 单帧大图做视觉 QA。

## 音频 QA

- 整片 `silencedetect=n=-35dB:d=1`：无输出，未检测到 >1s 静音。
- full-music 段 `volumedetect`：

| 歌曲 | 时间窗 | mean_volume | max_volume |
| --- | --- | ---: | ---: |
| 暧昧 | 27.291s + 55.0s | -15.8 dB | -0.2 dB |
| 邮差 | 97.218s + 34.0s | -16.2 dB | -2.7 dB |
| 棋子 | 145.906s + 36.0s | -15.9 dB | -3.5 dB |
| 笑忘书 | 196.665s + 42.0s | -15.7 dB | -2.0 dB |
| 暗涌 | 254.044s + 42.0s | -14.4 dB | -0.4 dB |

full-music 均值跨度约 1.8 dB，听感目标为统一响度；旁白期间音乐床由构建脚本固定压到 `BED=0.15`，随后 ramp 到 full-music。

## 画面 QA

最终抽帧：

- `qa/final_contact.jpg`：全片 20 格联系表。
- `qa/final_keyframes.jpg`：关键时间点联系表。
- `qa/final_frames/`：封面、各 full-music 标签、CTA 单帧。

检查结论：

- 第 0 秒封面可作为静态封面，标题、说明、chips 未截断；底片已换为《暧昧》片段。
- 各 full-music 段无黑屏/冻结。
- 画面未见平台水印、网址、路径、提示词泄漏。
- CTA 画面完整，固定 CTA 旁白为全片最后一句。
