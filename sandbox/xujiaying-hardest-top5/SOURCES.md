# Sources — 徐佳莹最难的5首歌

Cookie files checked:

- YouTube: `sandbox/www.youtube.com_cookies.txt`
- B站: `sandbox/www.bilibili.com_cookies.txt`

Selection rule: both YouTube and B站 were searched for every song. Prefer official source, clean image, stereo audio, usable continuous chorus, and no burned-in platform/UP watermark. Short probes were downloaded for both sides where needed, then frame-checked before final clipping.

## 5. 《到此为止》

- YouTube candidate: `https://www.youtube.com/watch?v=T7IK_5XCRiU` | 4:55 | LaLa 徐佳瑩 | Official Music Video
- B站 candidates:
  - `https://www.bilibili.com/video/BV1jW411p7Wb` | 4:56 | 华语新歌MV | 蓝光1080P官方MV
  - `https://www.bilibili.com/video/BV1RE421A76z` | 4:59 | Wui-229 | 4K修复
- Final choice: YouTube official `T7IK_5XCRiU`.
- Reason: YouTube and B站 4K probe looked visually similar; YouTube official kept a stronger stereo Opus track than the B站 HE-AAC probe.
- Clip window: source `00:02:43-00:03:40`, output `raw/p5_daoci_yt.mp4`, crop `1920:980:0:40`.

## 4. 《灰色》

- YouTube candidate: `https://www.youtube.com/watch?v=xtSdgGHqnls` | 5:21 | LaLa 徐佳瑩 | Official Music Video
- B站 candidates:
  - `https://www.bilibili.com/video/BV1FA411N7aD` | 5:20 | 太合音乐 | 官方MV
  - `https://www.bilibili.com/video/BV16Q4y1i7tj` | 5:21 | 贝多芬2020 | 蓝光MV
- Final choice: B站 official `BV1FA411N7aD`.
- Reason: official 1080P H.264 + 48kHz stereo, cleaner than the first B站 mirror probe; right-side lyric area is removed by crop.
- Clip window: source `00:02:53-00:03:51`, output `raw/p4_huise_bi.mp4`, crop `1500:1080:0:0`.

## 3. 《失落沙洲》

- YouTube candidate: `https://www.youtube.com/watch?v=Ie1KcGvBN_k` | 5:35 | 亞神音樂娛樂 | Official Music Video
- B站 candidates:
  - `https://www.bilibili.com/video/BV1RZ4y1879b` | 5:35 | 班扎咕噜 | 1080P重制版
  - `https://www.bilibili.com/video/BV1WmzaYBE9v` | 6:30 | 零丁洋不好re | 4K修复
- Final choice: B站 1080P重制 `BV1RZ4y1879b`.
- Reason: YouTube official is 640x480; B站 1080P重制 is visibly cleaner and stereo. B站 4K live probe was rejected because it was not the official MV look and carried platform/watermark risk.
- Clip window: source `00:02:29-00:03:27`, output `raw/p3_shalu_bi.mp4`, crop `1920:1002:0:0`.

## 2. 《身骑白马》

- YouTube candidate: `https://www.youtube.com/watch?v=VzXOT26_Da8` | 5:18 | 亞神音樂娛樂 | Official Music Video
- B站 candidates:
  - `https://www.bilibili.com/video/BV1Hr4y1t73v` | 5:17 | 班扎咕噜 | 1080P重制版
  - `https://www.bilibili.com/video/BV1da4y137BL` | 5:17 | 超爱大可乐 | 4K修复
  - `https://www.bilibili.com/video/BV1f541167Sk` | 5:18 | 驰放音乐分享 | 纯净官方版MV
- Final choice: B站 4K修复 `BV1da4y137BL`.
- Reason: YouTube/纯净版 were 640x480; B站 4K修复 was sharper and stereo. Bottom burned lyrics were removed by a tighter full-width crop.
- Clip window: source `00:02:38-00:03:36`, output `raw/p2_baima_bi.mp4`, crop `1440:620:240:0`.

## 1. 《极限》

- YouTube candidate: `https://www.youtube.com/watch?v=1EMYVt0odI0` | 3:59 | 亞神音樂娛樂 | Official Music Video
- B站 candidates:
  - `https://www.bilibili.com/video/BV1njfYY7EwH` | 3:59 | 你头上有花吗 | 4K修复+无损音源
  - `https://www.bilibili.com/video/BV1AN411X7zR` | 3:59 | 太合音乐 | 官方MV
- Final choice: B站 4K修复+无损音源 `BV1njfYY7EwH`.
- Reason: sharper 1080P upscale than official 640/720 sources and stereo audio. Bottom-right red stamp was removed by crop.
- Clip window: source `00:02:01-00:03:01`, output `raw/p1_jixian_bi.mp4`, crop `1440:720:240:0`.
