# 素材来源与取舍

本轮按根目录 cookie 规范执行，只读取：

- `www.youtube.com_cookies.txt`
- `www.bilibili.com_cookies.txt`

没有使用 `sandbox/` 下的旧 cookie 副本。

## YouTube 复查结果

YouTube flat search 能搜到官方候选，但 2026-06-21 用根目录 YouTube cookie 对官方 MV 详情/下载复查时，`yt-dlp` 仍返回：

```text
Sign in to confirm you're not a bot
```

因此本轮无法实际拉取 YouTube 官方源做帧级/码率级复核。YouTube 候选仍记录如下：

| 歌曲 | YouTube 候选 | 备注 |
| --- | --- | --- |
| 暧昧 | `bR8u65g_t7o` 王菲 Faye Wong - 曖昧 (Official Music Video) | 官方 MV，未能下载复核 |
| 邮差 | `FS9sBncQAeo` 王菲 Faye Wong -《郵差》(Official Music Video) [HD] | 官方 MV，未能下载复核 |
| 棋子 | `aMVnE0WAcuQ` 王菲 Faye Wong - 棋子 (Official Music Video) | 官方 MV，未能下载复核 |
| 笑忘书 | `QSTebfDM3LQ` 王菲 Faye Wong -《笑忘書 (國)》(Official Music Video) [HD] | 官方 MV，未能下载复核 |
| 暗涌 | `xwI8pYCRTcU` 王菲 Faye Wong - 暗湧 (Official Music Video) | 官方 MV，未能下载复核 |

## B站候选与最终选择

| 歌曲 | 最终源 | 规格/画面 | crop | 取舍 |
| --- | --- | --- | --- | --- |
| 暧昧 | `BV1BdRZBaEJC` / `raw/aimei_bili_seedvr.mp4` | SeedVR 修复，1620x1080，画面干净 | `1620:980:0:80` | 比环球官方低清源更清楚，裁后无平台水印/烧词 |
| 邮差 | `BV1Zq4y1E7C8` / `raw/youchai_bili_live1080.mp4` | 1080P Live，1440x1080，主体清楚 | `1440:1080:0:0` | 官方 Karaoke 源 `BV1oW7izWEus` 有大歌词，裁掉后主体只剩小电视框；Live 更适合成片观感 |
| 棋子 | `BV1bR4y157rD` / `raw/qizi_bili_4kfix.mp4` | 4K 修复下采样，1920x1080，红色 MV 段辨识度高 | `1920:900:0:0` | 官方源歌词更重；该源裁掉底部字幕后主体完整 |
| 笑忘书 | `BV14ksteLEgN` / `raw/xiaowangshu_bili_betacam.mp4` | Betacam 高清修复，1440x1080，干净 | `1440:1080:0:0` | 比原版/MTV 低清源更稳，无遮挡 |
| 暗涌 | `BV1pg411K7yb` / `raw/anyong_bili_1080fix.mp4` | 1080P 修复，1440x1080，高码率 | `1440:660:0:0` | 官方环球源 640x480 且歌词明显；修复源用全宽横带裁掉歌词后画质更好 |

## 已下载备选

项目保留了以下备选，便于后续替换：

- 暧昧：`aimei_bili_universal.mp4`、`aimei_bili_ld60.mp4`
- 邮差：`youchai_bili_official1080.mp4`、`youchai_bili_betacam.mp4`、`youchai_bili_mv.mp4`
- 棋子：`qizi_bili_seedvr.mp4`、`qizi_bili_universal.mp4`
- 笑忘书：`xiaowangshu_bili_original.mp4`、`xiaowangshu_bili_4k.mp4`、`xiaowangshu_bili_mtv.mp4`
- 暗涌：`anyong_bili_universal.mp4`

## 人声入点

切片按规范将人声入点对齐到旁白结束前约 2 秒，确保 full-music 段进入后已经在唱：

| 歌曲 | 源人声入点 | 预切起点 | full-music 本地起点 | 展示时长 |
| --- | ---: | ---: | ---: | ---: |
| 暧昧 | 177.17 | 165.895 | 15.025 | 55.0 |
| 邮差 | 63.88 | 52.630 | 15.000 | 34.0 |
| 棋子 | 200.09 | 189.065 | 14.775 | 36.0 |
| 笑忘书 | 95.11 | 84.085 | 14.775 | 42.0 |
| 暗涌 | 160.57 | 148.920 | 15.400 | 42.0 |

## 调整记录

- 2026-06-21：按反馈将《暧昧》展示段从 34s 延长到 55s，覆盖后续 `215.99-233.08` 的连续人声段。
- 2026-06-21：按反馈将《笑忘书》展示段从 32s 延长到 42s，覆盖后续尾句。
- 2026-06-21：封面底片从《棋子》红色 MV 段改为《暧昧》`170.0s` 起的片段。
