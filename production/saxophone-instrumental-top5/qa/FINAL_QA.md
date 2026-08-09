# 最终成片 QA

权威文件：`renders/saxophone-instrumental-top5.mp4`

- SHA-256：`1ff439eea18097f83a48ed7a332d5de061f6a4511ded364259892e9b3b5275bc`
- 文件大小：301,833,824 bytes（约 288 MiB）
- 时长：541.600 秒（9:01.600）
- 视频：H.264 High、1080×1920、30fps、yuv420p、BT.709 SDR
- 音频：AAC LC、48kHz、双声道立体声、约 192kbps
- 完整解码：通过

## 结构与画面

- 排名顺序：05 → 04 → 03 → 02 → 01，通过。
- HyperFrames lint：0 errors / 0 warnings。
- HyperFrames validate：0 errors / 0 structural warnings。另有 5 个对同一非当前场景封面角标的自动对比度提示；工具在 54.16s 等封面已经退场的采样点把角标文字与底层暗色误配。最终封面抽帧显示该角标为金底深字，实际清晰可读。
- HyperFrames inspect：9 个时间采样，0 个布局问题。
- 从最终 post-mux MP4 抽取 46 个当前关键帧：16 张覆盖封面、每名旁白页、每名完整音乐页、片尾与 CTA；15 张覆盖五个黄铜闸门转场前/中/后；15 张覆盖五首完整音乐窗口的头/中/尾。
- 三张总览：`final-contact-sheet.jpg`、`transition-contact-sheet.jpg`、`music-window-contact-sheet.jpg`。
- 画面复核未发现平台/UP 主水印、网址、路径、提示词、烧录字幕或自定义旁白字幕。
- 第四名采用 104.8–170.3s 替代窗口，避开源视频后段不适合本期叙事的亲密剧情；第五名在约 873s 演职员表前结束。
- `blackdetect=d=0.5:pix_th=0.10` 未检出异常黑场。

## 音频

- HyperFrames 使用 `render_silence.wav` 渲染；最终 AAC 来自后期 mux 的预混 `master.wav`，动态没有被浏览器渲染链压平。
- Integrated loudness：-14.6 LUFS。
- Loudness range：8.9 LU。
- True peak：-0.6 dBFS；volumedetect max：-0.6 dB。
- `silencedetect=n=-35dB:d=1` 未发现超过 1 秒的意外静音。
- 五个连续纯音乐窗口分别为 123.3、65.5、74.5、88.0、96.4 秒，全部通过 `probe/instrumental_plan.json` 门禁。
- 隔离旁白 Whisper small：8/8 窗口 `OK`，完整旁白相似度 0.700–1.000。
- 最终 post-mux AAC Whisper small：7/7 窗口 `OK`，排名/正文上下文均识别；相似度 0.700–0.886，所有窗口 `forbidden_next=false`。
- 原始 ASR 证据保留在 JSON 中；只对本次实际观察到的 `薩克斯/評論區/點贊` 三个繁简体变体做上下文归一化，没有改写音频或美化转写。

## 来源边界

- 五首均执行 YouTube + B站双平台检索，候选、清晰度与选择理由见 `SOURCES.md`。
- 第 01–04 名采用官方 MV/官方上传。
- 第 05 名没有适合作为画面的官方 MV；最终采用真实歌手 1981 年现场的 1440×1080 YouTube 非官方上传，优于 B站 480×360 同场候选，也优于官方 Topic 静态封面。此项限制已明确记录，不把它描述成官方上传。
