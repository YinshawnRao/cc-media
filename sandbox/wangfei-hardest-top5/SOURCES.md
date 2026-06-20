# SOURCES — 王菲最难的5首歌

成片画幅 1080x1920 / 30fps / H.264 + AAC。Render 必须加 `--sdr`，最终以后期 mux `master.wav` 为准。

## 候选覆盖与取舍

| 歌 | YouTube 候选 | B站候选 | 选择 |
|---|---|---|---|
| 脸 | `Z7FP7zT6klU` 王菲官方频道，626x480 stereo，但大号卡拉OK歌词+电视角标；`F2Aai_9jNJ0` 区雪儿导演上传，640x480 stereo，画面干净 | `BV1ky4y187Lj` 4K30 修复，stereo，但下载整片速度极慢且非官方搬运 | 选 YouTube `F2Aai_9jNJ0`，干净度优先 |
| 多得他 | `CxnF3DJ3pJ8` FayeWongVEVO，1920x1080 stereo，官方 MV | `BV1vee5e1EZx` 1920x1080 stereo 官方拼接 MV；`BV1kT4y1A7PM` 环球候选 playinfo 不可解析；`BV1zs411d7E7` 被删/地区限制 | 选 YouTube VEVO 官方源 |
| 寒武纪 | `768FVRdu4DI` FayeWongVEVO，1096x720 stereo，官方 MV，后段有大号卡拉OK歌词 | `BV1uK4y1N7ir` 1500x1080 stereo 修复，下载整片速度极慢；`BV1bnTDz4E9d` 百代原版 640x480 stereo | 选 YouTube VEVO HD，展示段换到 216.7s 附近最终副歌并裁底避歌词 |
| 彼岸花 | 旧项目已对照：独立棚版 MV 不稳定，多为烧词 Karaoke/连播 | `BV1Gp4y1y7BP` 2010 唱游大世界 Live，1920x1080 stereo，裁掉署名/黑边后干净 | 复用 `sandbox/linxi-faye-fengshen/raw/bianhua_show.mp4` + `bianhua_audio.wav` |
| 开到荼蘼 | `8rnnsxbKBNw` VEVO 官方 MV，1920x1080 stereo，较干净 | 旧项目已对照，B站版本不优于 VEVO | 复用 `sandbox/linxi-faye-fengshen/raw/kaidao_show.mp4` + `kaidao_audio.wav` |

## Final source windows

| key | 歌 | source | source start | show | crop / note |
|---|---|---|---:|---:|---|
| p5_kaidao | 开到荼蘼 | local copy from `linxi-faye-fengshen`, YT `8rnnsxbKBNw` | 89s | 36s | Existing clean letterbox clip, gold dress MV |
| p4_bianhua | 彼岸花 | local copy from `linxi-faye-fengshen`, B站 `BV1Gp4y1y7BP` | 149s | 36s | Existing clean letterbox live clip |
| p3_hanwuji | 寒武纪 | `raw/hanwuji_full.mp4`, YT `768FVRdu4DI` | 216.7s | 34s | Final chorus vocal-heavy segment, crop `1096:500:0:0` to remove burned lyrics |
| p2_duodeta | 多得他 | `raw/duodeta_full.mp4`, YT `CxnF3DJ3pJ8` | 190s | 36s | VEVO 1080p, small bottom subtitle can be cropped |
| p1_face | 脸 | `raw/face_susie.mp4`, YT `F2Aai_9jNJ0` | 126s | 38s | Susie Au upload, no burned lyric/watermark |

## QA notes

- Contact sheets created: `qa/face_contact.jpg`, `qa/face_susie_contact.jpg`, `qa/duodeta_contact.jpg`, `qa/hanwuji_contact.jpg`.
- Final contact sheet: `qa/final_contact.jpg`.
- Specific QA frames: `qa/final_t018.png`, `qa/final_t176.png`, `qa/final_t238.png`, `qa/final_t299.png`.
- Hanwuji replacement QA: full-song vocal scan found a continuous vocal-heavy section at 212.95-261.57s; final showcase uses 216.7-250.7s. New segment contact sheet: `qa/final_hanwuji_new_contact.jpg`; no visible platform watermark, URL, path, or prompt leakage in sampled frames.
- Audio QA: no `silencedetect` intervals; overall `volumedetect` mean -16.8 dB, max -0.4 dB. Hanwuji showcase `volumedetect`: mean -14.9 dB, max -3.9 dB.
- Video QA: `freezedetect` reported no intervals. `blackdetect` reported dark-card/dark-footage false positives at 175.93-177.03s and 237.67-243.93s; both frames reviewed and contain readable content.
