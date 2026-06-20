# Sources — 温岚最被低估的5首歌

目标：竖屏 1080×1920，倒数揭晓 5→1，女声旁白。按规范每首都查 YouTube + B站候选，优先官方 MV、干净画面、立体声、连续可用展示段。

Cookie：YouTube `sandbox/www.youtube.com_cookies.txt` 本地结构检查合格；B站搜索脚本可用。HyperFrames 渲染、后期 mux 和最终 QA 已完成，最终文件见 `hf/renders/wenlan-underrated-top5.mp4`。

## 平台候选与取舍

### 5. 《爱太急》 — 官方音轨 + 同专辑官方 MV 救场

- YouTube: `PuURCK1IRCs` | 4:55 | 溫嵐 Landy Wen | 《愛太急 (OT:Believe)》| 官方/艺人频道音轨，无动态 MV。
- YouTube: `1NVgQkXQtiQ` | 4:54 | 搬运/歌词向视频 | 非官方。
- B站: `BV1ZzddBbEmM` | 41:32 | 电视特辑候选；`BV1pV4y137KJ` / `BV1YN7AztEdz` 为演唱会长视频；未搜到该曲官方动态 MV。
- 最终：音频用 YouTube 官方音轨 `PuURCK1IRCs`；画面用同专辑/早期风格的《北斗星》阿尔发官方 MV `QAKZGtFeHio` 的 205–236s 近景段。原因：该曲无可确认官方动态 MV，官方音轨优先保证歌曲本体；画面救场源裁掉字幕后无平台水印、无网址。

### 4. 《不吵不闹》 — YouTube 阿尔发官方 MV

- YouTube: `I3XZJfSY0xY` | 3:15 | 阿爾發音樂 | Official Music Video。
- B站: `BV1mVoAB8EDW` / `BV19e4y1N7TA` / `BV1ZfgAexE5D` | 搬运 MV/音频候选。
- 最终：YouTube 官方 MV `I3XZJfSY0xY`。展示窗约 150.5–180.8s，裁切 `640:300:0:60` 去掉上下白带和底部烧词。

### 3. 《动心》 — YouTube 阿尔发官方 MV

- YouTube: `KEyZQCK9uxI` | 4:50 | 阿爾發音樂 | Official Music Video。
- B站: `BV19d4y1K7LK` / `BV1Bi4y147ip` / `BV1Ybz6BAE47` | 搬运官方 MV 候选。
- 最终：YouTube 官方 MV `KEyZQCK9uxI`。展示窗约 223.2–254.5s，裁切 `606:285:0:0` 去掉底部烧词。源仅 606×360，属老歌官方源限制。

### 2. 《爱你的两个我》 — YouTube 阿尔发官方 MV

- YouTube: `tSTRBbrrjIw` | 4:19 | 阿爾發音樂 | Official Music Video。
- B站: `BV1Rg4y157gR` MV 合集、`BV1Tj411J7Cd` 音频/搬运候选；未见更高质量官方单条。
- 最终：YouTube 官方 MV `tSTRBbrrjIw`。展示窗约 58.7–89.0s，裁切 `640:270:0:105` 去黑边/字幕。官方 MV 前半段温岚镜头较多，后段偏剧情，故避开后段。

### 1. 《荒唐》 — YouTube 阿尔发官方 MV

- YouTube: `L3vt0ZP7RcQ` | 5:41 | 阿爾發音樂 | Official Music Video。
- B站: `BV1pF411j729` / `BV1T6cCebEr6` / `BV1zy411h78n` | 搬运 MV 候选。
- 最终：YouTube 官方 MV `L3vt0ZP7RcQ`。展示窗约 197.1–230.4s，裁切 `640:360:0:0` 去掉底部烧词。压轴保留 30s 连续展示。

## 当前 QA 结论

- 五段展示片均已抽帧检查：无平台水印、无网址、无路径、无提示词；官方 MV 烧词已通过全宽横带 crop 尽量移除。
- 全片 `master.wav`：48kHz stereo，276.275s。
- `silencedetect=n=-35dB:d=1` 未报 >1s 整片静音。
- 展示段 `volumedetect`：约 -15.0 至 -15.6 dB；《爱太急》已从 -16.6 dB 调到 -15.3 dB。
- 最终 `hf/renders/wenlan-underrated-top5.mp4`：1080×1920，H.264，30fps，BT.709 SDR，AAC stereo 48kHz，276.275s。
- HyperFrames：`lint` 0 error（仅 GSAP Studio 编辑 warning），`inspect --samples 8` 0 layout issues，`render --sdr --workers 1` 完成。
- 最终抽帧：`qa/final_mux_contact.jpg`、`qa/final_timeline_contact.jpg`。画面内未见平台水印、网址、路径、提示词泄漏；片尾榜单和固定 CTA 可见。
