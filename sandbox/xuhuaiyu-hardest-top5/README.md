# 徐怀钰最难的5首歌

倒数盘点视频，排名按用户指定：05《妙妙妙》、04《心中的遗憾》、03《分飞》、02《Call Me》、01《飞起来》。

最终成片：

```text
renders/xuhuaiyu-hardest-top5.mp4
```

规格：
- 1080x1920 竖屏
- H.264 + AAC 48 kHz stereo
- 时长 `274.646s`
- 大小约 `156 MB`

## 构建

旁白已生成在 `audio/`。如需重建旁白：

```bash
../../tools/tts/venv/bin/python build/narrate_segments.py
```

重建 HyperFrames 入口和预混母带：

```bash
python3 build/full_build.py
```

渲染画面：

```bash
npx hyperframes lint
npx hyperframes inspect --samples 12
npx hyperframes render --output renders/full_raw.mp4 --sdr
```

最终必须用 `master.wav` 后期 mux：

```bash
ffmpeg -v error -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/xuhuaiyu-hardest-top5.mp4 -y
```

## QA 结果

HyperFrames:
- `lint`: 0 errors, 3 warnings
- `inspect --samples 12`: 0 layout issues

`lint` 警告为主时间线元素偏密、字体未通过 `@font-face` 固定。最终抽帧未发现可见版式问题。

音频：
- `silencedetect=n=-35dB:d=1`: 无 `silence_start`
- 展示段 volumedetect：
  - 05《妙妙妙》：mean `-15.7 dB`，max `-0.5 dB`
  - 04《心中的遗憾》：mean `-15.9 dB`，max `-3.4 dB`
  - 03《分飞》：mean `-14.6 dB`，max `-1.5 dB`
  - 02《Call Me》：mean `-15.0 dB`，max `-1.4 dB`
  - 01《飞起来》：mean `-15.2 dB`，max `-0.1 dB`
  - 片头旁白窗口：mean `-18.0 dB`，max `-2.2 dB`

视觉：
- `qa/final_frames/contact_20.jpg` 覆盖封面、片头、每首歌转场/展示和片尾。
- `qa/final_frames/contact_9.jpg` 用于检查大字版式和片尾榜单。
- 未发现平台水印、网址、路径、提示词泄漏。
- 片头没有提前列出完整排名，片尾完整回顾排名。
