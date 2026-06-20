# 温岚最被低估的5首歌

竖屏音乐遗珠盘点，倒数揭晓 5→1，女声旁白 `zf_xiaoyi`。当前已完成素材、旁白、切片、预混音轨、HyperFrames 渲染、后期 mux 和最终 QA。

## 排名

| 名次 | 歌曲 | 来源策略 |
|---|---|---|
| 5 | 爱太急 | 官方音轨 + 同专辑官方 MV 画面救场 |
| 4 | 不吵不闹 | 阿尔发官方 MV |
| 3 | 动心 | 阿尔发官方 MV |
| 2 | 爱你的两个我 | 阿尔发官方 MV |
| 1 | 荒唐 | 阿尔发官方 MV |

## 关键文件

- `SOURCES.md` — YouTube + B站候选、最终选源、裁切和 QA 记录。
- `build/song_config.py` — 单一配置源：排名、切点、展示时长、crop、音频窗、增益。
- `build/narrate_segments.py` — 女声旁白文案和 wav 生成。
- `build/prep_footage.py` — 素材竖屏化和 `audio_src/*.wav` 切片。
- `build/full_build.py` — 生成 `master.wav`、`hf/index.html`、封面和 HF 素材。
- `master.wav` — 预混主音轨，最终 MP4 必须用它后期 mux。
- `hf/index.html` — HyperFrames composition。
- `hf/renders/wenlan-underrated-top5.mp4` — 最终 mux 成片。
- `qa/final_mux_contact.jpg` / `qa/final_timeline_contact.jpg` — 最终抽帧 QA 图。

## 复现命令

```bash
# 1. 女声旁白
tools/tts/venv/bin/python sandbox/wenlan-underrated-top5/build/narrate_segments.py

# 2. 展示片 + 音频窗
tools/tts/venv/bin/python sandbox/wenlan-underrated-top5/build/prep_footage.py

# 3. master.wav + hf/index.html
tools/tts/venv/bin/python sandbox/wenlan-underrated-top5/build/full_build.py

# 4. HyperFrames 检查与渲染
cd sandbox/wenlan-underrated-top5/hf
npx hyperframes lint
npx hyperframes inspect --samples 8
npx hyperframes render --output renders/full_raw.mp4 --sdr

# 5. 后期 mux 预混音轨
ffmpeg -i renders/full_raw.mp4 -i ../master.wav -map 0:v -map 1:a \
  -c:v copy -c:a aac -b:a 192k -shortest renders/wenlan-underrated-top5.mp4
```

## 当前状态

已完成：
- 双平台候选检索与选源记录。
- 女声旁白 wav 与 `narration.json`。
- 五段竖屏展示片，展示段 26–30s。
- `master.wav` 预混音轨，展示段响度已拉齐。
- `hf/index.html` 与本地结构检查：25 个 timed clips，无同轨重叠，媒体引用存在且时长覆盖。

最终输出：
- `hf/renders/wenlan-underrated-top5.mp4`

最终 QA：
- `npx -y hyperframes lint`：0 error；仅剩 GSAP timeline 控制元素导致 Studio 拖拽写回受限的 warning，不影响渲染。
- `npx -y hyperframes inspect --samples 8`：0 layout issues。
- `npx -y hyperframes render --output renders/full_raw.mp4 --sdr --workers 1`：完成，SDR 生效。
- `ffmpeg` 后期 mux：用 `../master.wav` 覆盖 HyperFrames 音轨。
- `ffprobe`：1080×1920，H.264，30fps，BT.709 SDR，AAC stereo 48kHz，276.275s。
- `silencedetect=n=-35dB:d=1`：无 >1s 静音事件。
- 五段展示段 `volumedetect`：mean volume 约 -15.0 至 -15.6 dB。
- 抽帧 QA：无平台水印、网址、路径、提示词泄漏；片尾榜单和固定 CTA 可见。
