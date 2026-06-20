# QA — 童安格最被低估的5首歌

## 已完成

- 读取仓库规范、视频 Runbook、HyperFrames/GSAP/TTS 相关技能。
- 双平台搜索完成：每首均查了 YouTube 和 B站，候选记录见 `SOURCES.md`。
- 女声旁白完成：`audio/*.wav`，音色 `zf_xiaoyi`，总旁白约 119.05s。
- 竖屏化完成：`clips/vert_*.mp4`，全部 1080x1920。
- 预切合成完成：`clips_seg/*.mp4`、`master.wav`、`index.html`。
- 第 5 首《整个世界只留下一盏灯》已按反馈重切：初版 231s 附近偏尾奏/背景声，终版改为源时间 180.0s 起的人声演唱段。
- 本地静态结构检查：
  - `index.html` 共 29 个 `clip`。
  - 无重复 `id`。
  - 所有 `clip` 都有 `id` / `data-start` / `data-duration` / `data-track-index`。
  - 同 track 无时间重叠。
- 音频检查：
  - `master.wav` 时长 297.911667s。
  - `silencedetect=n=-35dB:d=1` 无输出，即未检出 >1s 静音。
  - `master.wav` 整体 `mean_volume: -16.4 dB`，`max_volume: 0.0 dB`。
- HyperFrames 官方检查：
  - `npx --yes hyperframes@0.6.69 lint`：0 errors；仅剩 3 条单文件长时间线密度提示。
  - `npx --yes hyperframes@0.6.69 validate`：无 console errors；145 个文字元素通过 WCAG AA。
  - `npx --yes hyperframes@0.6.69 inspect`：本轮因预览控制链路 navigation/WebSocket 超时，未作为交付门禁；最终判断改用 mux 后 MP4 的抽帧、音量和 ASR 检查。
- 渲染与 mux：
  - `renders/full_raw.mp4`：HyperFrames 渲染原始视频，1080x1920，30fps。
  - `renders/tongange-underrated-top5.mp4`：最终后期 mux 版本，使用 `master.wav` 替换渲染音轨。
  - 最终 MP4：1080x1920，30fps，AAC 48kHz stereo，时长 297.911s。
- 最终音频检查：
  - `silencedetect=n=-35dB:d=1` 无输出，即未检出 >1s 静音。
  - `volumedetect`：`mean_volume: -16.4 dB`，`max_volume: 0.0 dB`。
  - 展示段 `volumedetect`：
    - 05: `mean_volume: -15.3 dB`，`max_volume: 0.0 dB`。
    - 04: `mean_volume: -14.7 dB`，`max_volume: -0.4 dB`。
    - 03: `mean_volume: -15.6 dB`，`max_volume: -0.3 dB`。
    - 02: `mean_volume: -15.0 dB`，`max_volume: -0.0 dB`。
    - 01: `mean_volume: -14.7 dB`，`max_volume: -0.4 dB`。
  - 第 5 首终版展示段 ASR：`probe/asr/final_p5_show_fixed.txt` 识别到“只留下一盏灯 / 让我看到的你 / 是不再委屈的眼神 / 整个世界只留下一盏灯”，确认不是背景音乐或尾奏空段。
- 画面抽帧：
  - 原始候选 contact sheet: `probe/raw_contact.jpg`。
  - 竖屏初版 contact sheet: `probe/vert_contact.jpg`。
  - 第 1、2 名重裁后抽帧：`probe/vert_frames/p1_120_recrop.jpg`、`probe/vert_frames/p2_140_recrop.jpg`，确认顶部平台/UP 标识已裁掉。
  - 最终成片 contact sheet: `probe/final_contact.jpg`、`probe/final_contact_fixed.jpg`。
  - 最终高分辨率抽帧：`probe/final_p1_230.jpg`、`probe/final_p1_238.jpg`、`probe/final_p1_250.jpg`、`probe/final_p1_260.jpg`、`probe/final_p1_265.jpg`、`probe/final_p2_184.jpg`、`probe/final_p4_090.jpg`。
  - 第 5 首重切后高分辨率抽帧：`probe/final_p5_052_fixed.jpg`，未见平台/UP 主水印、网址、文件路径、提示词泄漏。
  - 终版抽帧未见平台/UP 主水印、网址、文件路径、提示词泄漏。
  - 第 1 名 238-250s 左右可见 MV 场景内英文招牌，不是平台/UP 主水印；230s、265s 等同段后续帧无该招牌。

## 最终产物

`renders/tongange-underrated-top5.mp4`
