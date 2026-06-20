# 飞儿乐队最被低估的5首歌

竖屏 1080×1920 音乐遗珠盘点，女声旁白 `zf_xiaoyi`，倒数揭晓 5→1。总时长约 4:51。

## 排名

| 名次 | 歌曲 | 专辑 | 展示源 |
|---|---|---|---|
| 5 | 眷恋 | 爱·歌姬 | B站 1080P 修复 MV |
| 4 | 天天夜夜 | 飞行部落 | B站 1080P 修复 MV |
| 3 | 后乐园 | F.I.R. 飞儿乐团 | B站 1080P 重制源 |
| 2 | 把爱放开 | 无限 | B站 1080P MV |
| 1 | 应许之地 | 无限 | B站 1080P MV 终章窗 |

完整候选与取舍见 `SOURCES.md`。

## 当前状态

已完成：
- YouTube + B站双平台查源与下载。
- 女声分段旁白：`audio/*.wav`。
- 竖屏展示片：`clips/show_*.mp4`。
- 预混音轨：`master.wav`。
- HyperFrames 工程：`hf/index.html`。
- 修正版渲染、后期 mux 与 QA。

最终成片：`hf/renders/fir-underrated-top5.mp4`。

已知限制：#4《天天夜夜》MV 源自带歌词图文，Live 候选有电视台台标/字幕且清晰度更低，最终保留 B站 1080P 修复 MV。

## 复现命令

```bash
# 1. 女声旁白
tools/tts/venv/bin/python sandbox/fir-underrated-top5/build/narrate_segments.py

# 2. 展示片 + 音频窗
tools/tts/venv/bin/python sandbox/fir-underrated-top5/build/prep_footage.py

# 3. master.wav + HyperFrames HTML
tools/tts/venv/bin/python sandbox/fir-underrated-top5/build/full_build.py

# 4. 验证
cd sandbox/fir-underrated-top5/hf
npx --yes hyperframes@0.6.47 lint
npx --yes hyperframes@0.6.47 inspect --samples 8

# 5. 渲染 + 后期 mux
./render_retry.sh renders/full_raw.mp4 290
ffmpeg -i renders/full_raw.mp4 -i ../master.wav -map 0:v -map 1:a \
  -c:v copy -c:a aac -b:a 192k -shortest renders/fir-underrated-top5.mp4
```

## 最终 QA

- HyperFrames lint：0 errors；2 个字体相关 warning（Google Fonts / Noto Sans SC 未声明 `@font-face`）。
- HyperFrames inspect：8 个 sample，0 layout issues。
- 最终容器：1080×1920 H.264, BT.709 SDR, AAC stereo, 291.125s。
- `silencedetect=n=-35dB:d=1` 无静音段输出。
- `volumedetect`: mean volume `-17.3 dB`, max volume `-1.1 dB`。
- 抽帧检查：`qa/final_timeline_sheet.jpg`、`qa/final_showcases_sheet.jpg`、`qa/final_p1_segment_scan.jpg`、`qa/final_cover.png`、`qa/final_cta.png`。
- 画面检查：排序 5→1 正确；#1《应许之地》已换为终章 Faye/乐队窗口；CTA 正常；未见平台名、URL、路径、提示词或额外 UP 水印。
