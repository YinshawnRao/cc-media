# QA 记录

## HyperFrames

- `npx hyperframes lint`：0 errors，3 个单文件 timeline density warnings。
- `npx hyperframes validate`：No console errors，13 text elements pass WCAG AA。
- `npx hyperframes inspect`：长片内部 10s navigation timeout，未作为阻断；已按仓库约定改用 render + artifact QA。
- `npx hyperframes render --output renders/full_raw.mp4 --sdr`：成功，原始渲染 5:08.3。

## 展示段对齐

`tools/video/showcase_align.py check --plan probe/showcase_plan.json --vocals probe/vocal_analysis.json --clips clips`：

- 第 5 名《爱深过做人》：OK，展示段人声覆盖 95%，结尾句末 0.3s 内。
- 第 4 名《他不惯被爱》：OK，展示段人声覆盖 77%，结尾句末 0.5s 内。
- 第 3 名《爱没有假如》：OK，展示段人声覆盖 100%，结尾句末 0.8s 内。
- 第 2 名《杂技》：OK，展示段人声覆盖 94%，结尾句末 0.1s 内。
- 第 1 名《如水》：OK，展示段人声覆盖 96%，结尾句末 0.9s 内。

## 最终成片

- 输出：`renders/weilan-underrated-top5.mp4`
- `ffprobe`：H.264，1080x1920，30fps；AAC stereo，48kHz；时长 307.952s；大小 143,222,486 bytes。
- `silencedetect=n=-35dB:d=1`：无 >1s 静音事件。
- 全片 `volumedetect`：mean -16.8 dB，max -0.3 dB。
- 抽样窗口：
  - 18-26s 旁白床：mean -21.5 dB。
  - 42-52s 展示段：mean -14.3 dB。
  - 78-86s 旁白床：mean -23.0 dB。
  - 102-112s 展示段：mean -16.8 dB。
  - 234-242s 旁白床：mean -23.1 dB。
  - 252-262s 展示段：mean -15.4 dB。
- 视觉抽帧：`qa/final_keyframes_sheet.jpg`，样本中未见平台水印、网址、文件路径、提示词或项目内部词。

## TTS 开头抽查

`whisper-cli -ng -m ~/.cache/hyperframes/whisper/models/ggml-large-v3.bin -l zh -d 9000 -nt -np` 抽查五段排名旁白开头，均保留排名播报：

- `p5_aishenguozuoren.wav`：识别到“接下来第五名”。
- `p4_tabuguanbeiai.wav`：识别到“接下来第四名”。
- `p3_aimyoujiashe.wav`：识别到“接下来第三名”。
- `p2_zaji.wav`：识别到“接下来第二名”。
- `p1_rushui.wav`：识别到“接下来第一名”。
