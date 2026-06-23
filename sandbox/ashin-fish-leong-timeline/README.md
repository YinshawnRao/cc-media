# 阿信 x 梁静茹音乐时间线

主题：《原来阿信把另一种五月天，写进了梁静茹的歌里》

当前状态：素材、女性旁白、`master.wav`、最终使用的 7 条竖屏片段、HyperFrames `index.html`、最终 MP4 和封面 PNG 已完成。

## 关键产物

- `SOURCES.md`：YouTube + B站候选、选择理由、限制记录。
- `narration.json`：TTS 文案和时长。
- `build_meta.json`：全片时间轴、每首源窗口、展示段绝对时间。
- `master.wav`：最终应 mux 的预混音轨，时长 `574.675s`。
- `hf/index.html`：HyperFrames composition。
- `hf/parts_html/part_*.html`：长视频稳定渲染用分段 composition。
- `hf/clips_seg/*.mp4`：7 条最终竖屏片段。
- `hf/renders/parts/*.mp4`：分段渲染画面。
- `hf/renders/full_raw.mp4`：分段 concat 后的无音轨画面。
- `renders/ashin-fish-leong-timeline.mp4`：已用 `hf/master.wav` 后期 mux 的最终视频。
- `renders/cover.png`：从 8 秒标题帧导出的封面图。
- `qa_frames/contact_sheet.png`：片头、7 首完整展示段和 CTA 抽帧检查图。

## 当前时间线

- 片头：0.000–20.000
- 彩虹：20.000–99.600，完整展示段 40.400–98.400
- Beautiful：99.600–171.750，完整展示段 118.550–170.550
- 听不到：171.750–242.875，完整展示段 189.675–241.675
- 燕尾蝶：242.875–318.300，完整展示段 262.100–317.100
- 纯真：318.300–396.900，完整展示段 337.700–395.700
- 丝路：396.900–477.400，完整展示段 416.200–476.200
- 可乐戒指：477.400–547.325，完整展示段 496.125–546.125
- Outro + 固定 CTA：547.325–574.675

## 已完成 QA

- HyperFrames：`lint` 0 errors / 0 warnings；`validate` 无 console errors，220 个文字元素通过 WCAG AA；`inspect --samples 12` 无 layout issues。
- 最终 MP4：`1080x1920`，`30fps`，视频时长约 `574.667s`；音频 `AAC stereo 48kHz`，时长 `574.675s`。
- `master.wav`：`silencedetect=n=-35dB:d=1` 无 >1s 静音。
- 最终 MP4：`silencedetect=n=-35dB:d=1` 无 >1s 静音；整体 `mean_volume: -15.7 dB`，`max_volume: -0.9 dB`。
- 最终 MP4：7 个完整展示段 mean volume 范围约 `-15.2 dB` 到 `-14.1 dB`。
- 7 个歌曲口播均在完整展示段开始前 `3.65s` 结束，没有旁白压住主歌唱段。
- `hf/clips_seg/*.mp4` 时长均等于或略大于 `data-duration`，不会因素材短导致黑屏。
- 抽帧复查过最终片段 crop 和最终 MP4 代表帧：片头两张卡已显示阿信/梁静茹人像；底部文案和 CTA 已上移到安全区；左侧时间轴线未遮挡主体；平台/UP 主标、顶部修复标和底部歌词残留已清理。
- `hf/index.html` 静态泄漏检查未发现会出现在画面里的平台名、BV 号、本地路径或提示词。

## 复现

```bash
cd /Users/yinshawnrao/explorer/cc-media/sandbox/ashin-fish-leong-timeline
./build/finish.sh
```

最终输出：

```text
renders/ashin-fish-leong-timeline.mp4
renders/cover.png
```
