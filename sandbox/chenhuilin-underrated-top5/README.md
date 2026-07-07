# 陈慧琳最被低估的5首歌

竖屏 1080×1920 音乐遗珠盘点，男声旁白 `zm_yunxi`，倒数揭晓 5→1。

## 排名

| 名次 | 歌曲 | 专辑 | 展示源 |
|---|---|---|---|
| 5 | 陪我失眠 | 爱情来了 | B站 1080P 修复 MV |
| 4 | 触不到的恋人 | 爱情来了 | B站环球官方 MV |
| 3 | 香薰恋爱治疗 | 花花宇宙 | B站动态 MV，右侧主体裁切 |
| 2 | 温柔眼泪 | 心口不一 | B站旧 VCD 动态 MV + YouTube 官方人声音轨 |
| 1 | 放不开手 | 心口不一 | B站 1080P 动态 MV，横带裁切 |

完整候选与取舍见 `SOURCES.md`。

## 复现命令

```bash
# 1. 男声旁白
tools/tts/venv/bin/python sandbox/chenhuilin-underrated-top5/build/narrate_segments.py

# 2. 展示片 + 音频窗
tools/tts/venv/bin/python sandbox/chenhuilin-underrated-top5/build/prep_footage.py

# 3. master.wav + HyperFrames HTML
tools/tts/venv/bin/python sandbox/chenhuilin-underrated-top5/build/full_build.py

# 4. 验证
cd sandbox/chenhuilin-underrated-top5/hf
npx --yes hyperframes@0.6.47 lint
npx --yes hyperframes@0.6.47 inspect --samples 8 --timeout 30000

# 5. 渲染 + 后期 mux
./render_retry.sh renders/full_raw.mp4 280
ffmpeg -i renders/full_raw.mp4 -i ../master.wav -map 0:v -map 1:a \
  -c:v copy -c:a aac -b:a 192k -shortest renders/chenhuilin-underrated-top5.mp4
```

## 当前状态

已完成：
- YouTube + B站双平台查源与下载。
- 男声分段旁白：`audio/*.wav`。
- 竖屏展示片：`clips/show_*.mp4`。
- 预混音轨：`master.wav`。
- HyperFrames 工程：`hf/index.html`。
- 修正版渲染、后期 mux 与 QA。

最终成片：`hf/renders/chenhuilin-underrated-top5.mp4`。

## 最终 QA

- HyperFrames lint：0 errors；1 个字体栈 warning。
- HyperFrames inspect：8 个 sample，0 layout issues（`--timeout 30000`）。
- 最终容器：1080×1920 H.264, 30fps, BT.709 SDR, AAC stereo, 279.800s。
- `silencedetect=n=-35dB:d=1` 无静音段输出。
- `volumedetect`: mean volume `-17.2 dB`, max volume `-0.4 dB`。
- 抽帧检查：`qa/final_timeline_sheet.jpg`、`qa/final_cover.png`、`qa/final_p2.png`、`qa/final_p3.png`、`qa/final_p1.png`、`qa/final_outro.png`、`qa/final_cta.png`。
- 抽帧结论：排序 5→1 正确；#3《香薰恋爱治疗》已改为右侧主体裁切避开淡水印；#2《温柔眼泪》已改为 42s 附近歌手段并使用 YouTube 官方人声音轨；封面已改用 #05《陪我失眠》清晰正脸帧，文字上移到中下安全区；未见平台名、URL、路径、提示词或额外水印。
