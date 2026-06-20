# Sources — 郁可唯最难的5首歌

Cookie files checked:

- YouTube: `sandbox/www.youtube.com_cookies.txt`
- B站: `sandbox/www.bilibili.com_cookies.txt`

Selection rule: both YouTube and B站 were searched for every song. Prefer official source, clean image, stereo audio, usable continuous vocal section, and no burned-in platform or uploader watermark. Final vertical clips use full-width/near-full-width horizontal crops to preserve the original MV framing.

## 5. 《时间煮雨》

- YouTube candidates:
  - `https://www.youtube.com/watch?v=FtN45E9vG50` | 4:07 | 1080x1080 | audio/topic style | 郁可唯 Yisa Yu
  - `https://www.youtube.com/watch?v=VK5nEJCS2HQ` | 4:06 | movie promo MV mirror
- B站 candidates:
  - `https://www.bilibili.com/video/BV1Ss411S78E` | 4:05 | 1280x544 H.264 + stereo AAC | 小时代电影系列官方高清宣传曲
  - `https://www.bilibili.com/video/BV1Ax411d7aj` | 4:06 | 高清 MV mirror
- Final choice: B站 `BV1Ss411S78E`.
- Reason: YouTube result is square audio/topic style and not a strong visual source; B站 candidate is the actual movie promo MV, stereo, with bottom lyrics removable by crop.
- Clip window: source `00:00:50-00:01:58`, output `raw/p5_shijianzhuyu_bi.mp4`.
- Crop: `1280:470:0:0`, output `clips/vert_shijianzhuyu.mp4`.

## 4. 《思慕》

- YouTube candidates:
  - `https://www.youtube.com/watch?v=luBSh_GxSHI` | 3:05 | 1920x1080 | Croton official drama MV
  - `https://www.youtube.com/watch?v=KGFA6CrKTLk` | 5:07 | 1920x1080 | Taihe official lyric video
- B站 candidates:
  - `https://www.bilibili.com/video/BV1gY15Y2ETp` | 3:06 | 852x480 | drama character MV
  - `https://www.bilibili.com/video/BV16zqMBEEBw` | 3:05 | mirror
- Final choice: YouTube `luBSh_GxSHI`.
- Reason: Croton source is 1080p official drama footage. The 5-minute Taihe source is a lyric video, weaker as primary picture; B站 candidate is lower resolution.
- Clip window: source `00:00:44-00:01:52`, output `raw/p4_simu_yt.mp4`.
- Crop: `1500:900:0:80`, output `clips/vert_simu.mp4`.
- Cover clip: source local `00:00:40.0-00:00:43.9` inside `raw/p4_simu_yt.mp4` (roughly original `00:01:24-00:01:28`), slowed to cover the full intro, same crop, output `clips/vert_cover_simu.mp4`. This keeps the opening background on Yisa Yu herself and avoids the adjacent drama-character cuts.

## 3. 《知否知否》

- YouTube candidates:
  - `https://www.youtube.com/watch?v=xoH29SM3e8I` | 4:36 | 1280x720 | lyric/MV fan channel
  - `https://www.youtube.com/watch?v=pXJU5_2Afxk` | 4:39 | live performance
- B站 candidates:
  - `https://www.bilibili.com/video/BV18t411k7HQ` | 4:36 | 1920x1080 AV1 + stereo AAC | 胡夏、郁可唯版 MV
  - `https://www.bilibili.com/video/BV1pR4y1H7fw` | 4:39 | 4K60 live
- Final choice: B站 `BV18t411k7HQ`.
- Reason: B站 MV source is 1080p with strong stereo audio and suitable drama imagery; YouTube candidate is lower resolution and more lyric-oriented.
- Clip window: source `00:00:52-00:02:00`, output `raw/p3_zhifou_bi.mp4`.
- Crop: `1920:860:0:0`, output `clips/vert_zhifou.mp4`.

## 2. 《指望》

- YouTube candidate: `https://www.youtube.com/watch?v=04VXfavbeDs` | 3:57 | 640x480 | Rock Records official MV | stereo Opus
- B站 candidates:
  - `https://www.bilibili.com/video/BV1ob421E7LE` | 4:03 | 1440x1080 H.264 + stereo AAC | 滚石官方发布高清版
  - `https://www.bilibili.com/video/BV1SM4m1y7pM` | 4:05 | official MV mirror
- Final choice: B站 `BV1ob421E7LE`.
- Reason: YouTube official is only 640x480. The B站 HD source preserves the same MV look at 1440x1080, with stereo audio and only small bottom lyrics removed by crop.
- Clip window: source `00:01:06-00:02:14`, output `raw/p2_zhiwang_bi.mp4`.
- Crop: `1440:930:0:0`, output `clips/vert_zhiwang.mp4`.

## 1. 《路过人间》

- YouTube candidate: `https://www.youtube.com/watch?v=FMl7GEaYwAE` | 4:03 | 1920x1080 | HIM official MV | stereo Opus
- B站 candidates:
  - `https://www.bilibili.com/video/BV1bb411x7pM` | official search result, but current extraction reports deleted or geo-restricted
  - `https://www.bilibili.com/video/BV112EQ6qEWn` | mirror
  - `https://www.bilibili.com/video/BV1JL411u7wk` | mirror
- Final choice: YouTube `FMl7GEaYwAE`.
- Reason: YouTube is accessible 1080p official source with stereo audio. B站 official candidate is currently unavailable/georestricted in the toolchain; mirrors add no clear advantage.
- Clip window: source `00:01:58-00:03:06`, output `raw/p1_luguorenjian_yt.mp4`.
- Crop: `1920:800:0:0`, output `clips/vert_luguorenjian.mp4`.
