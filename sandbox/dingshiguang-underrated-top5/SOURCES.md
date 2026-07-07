# 丁世光最被低估的5首歌 - sources

Project: `sandbox/dingshiguang-underrated-top5`

Final order follows the user-provided ranking, revealed from #5 to #1:

1. `05` 乌托邦
2. `04` 你的家
3. `03` 月食
4. `02` 如果我们当时一起会怎么样
5. `01` 不散的筵席

## Final source choices

| Rank | Song | Final source | Local file | Why selected |
| --- | --- | --- | --- | --- |
| 05 | 乌托邦 | YouTube official, `armskgaECUk` | `raw/p5_wutuobang.mp4` | Official image and audio. B站 live candidate had top watermark and bottom burned lyrics; official source was cleaner after crop. |
| 04 | 你的家 | YouTube official, `r6RuuYtqfe8` | `raw/p4_nidejia.mp4` | Official source. B站 search did not produce a cleaner relevant Ding Shiguang performance/source. Cropped to avoid visible title/lyric bands. |
| 03 | 月食 | B站 live, `BV1HX4y1v7tS` | `raw/p3_yueshi_live.mp4` | More dynamic than static/official video candidates, with cleaner stage imagery after top crop. |
| 02 | 如果我们当时一起会怎么样 | B站 live, `BV19h411N7oa` | `raw/p2_if_live.mp4` | YouTube candidate was audio/static-like. This live source has stronger visual motion and a usable chorus window after crop. |
| 01 | 不散的筵席 | B站 live, `BV15m4y1i7xt` | `raw/p1_busan_live.mp4` | YouTube official MV and B站 MV copies carried visible old-MV/burned-text baggage. This live source is cleaner and more publishable after a tighter top crop. |

## Dual-platform checks

### 不散的筵席

- YouTube checked: Dean Ting official MV `JZ9KNNjcza0`; Zhejiang/live candidates also checked.
- B站 checked: MV copies including `BV16reYzAEaW`, `BV14s411L7bs`; live candidate `BV15m4y1i7xt`.
- Decision: use B站 live `BV15m4y1i7xt`; crop `1920:820:0:160`.

### 如果我们当时一起会怎么样

- YouTube checked: Topic/static-like source `K95ObHGlKxE`.
- B站 checked: static/MV candidate `BV1GB4y167pf`; live candidate `BV19h411N7oa`.
- Decision: use B站 live `BV19h411N7oa`; crop `1920:900:0:100`.

### 月食

- YouTube checked: Taihe/official candidates `_EXg3J1U4aY`, `9iXM4hRP5nw`.
- B站 checked: Taihe official `BV1ch411X7ws`; live candidate `BV1HX4y1v7tS`.
- Decision: use B站 live `BV1HX4y1v7tS`; crop `1920:900:0:80`.

### 你的家

- YouTube checked: Dean Ting official `r6RuuYtqfe8`.
- B站 checked: related results, but candidates were static, cover/irrelevant, or less clean for this edit.
- Decision: use YouTube official `r6RuuYtqfe8`; crop `1920:820:0:140`.

### 乌托邦

- YouTube checked: Dean Ting official `armskgaECUk`.
- B站 checked: live candidate `BV15FzSYvETi`.
- Decision: use YouTube official `armskgaECUk`; crop `1920:820:0:140`.

## QA notes

- Final mix must use `master.wav` as a post-render mux source, not HyperFrames flattened audio.
- Visual QA should inspect frames from the muxed render, not only `clips_seg/footage_track.mp4`.
- Current planned final duration: `321.625s`.
