# Sources — 那英最被低估的5首歌

Rule: search both YouTube and B站 for every song. Prefer official MV, clean image, stereo audio, usable continuous vocal segment, and no platform or uploader watermark. Old official MV quality is acceptable for this brief.

Cookie files checked:

- YouTube: `sandbox/www.youtube.com_cookies.txt`
- B站: `sandbox/www.bilibili.com_cookies.txt`

## Current source decisions

Four songs have usable YouTube official MV uploads from Timeless Music. `你是我的人` did not yield a YouTube official MV; B站 search also mostly returned album-cover or audio-only style sources. The only downloaded viable source is a square album-cover audio source, so the composition treats it as a physical album sleeve with motion graphics. A higher-bitrate B站 “配乐4k视频” candidate exists, but both 1080p and 480p downloads stalled and were aborted to keep the build moving.

Downloaded source probes:

- YouTube official MV files are 712x480 or 712x480/480p-class, stereo AAC.
- `你是我的人` B站 album source is 1080x1080, stereo AAC, visually static.
- All final showcase windows were back-solved from vocal segment detection so full-volume music starts on singing.

## Candidates

### 第5名《船》

- YouTube: `https://www.youtube.com/watch?v=RL1sd-3p_-A` | 5:10 | Timeless Music | official完整版MV.
- B站: `BV1Xz4y1Q7Gq` | 5:11 | 驰放音乐分享 | 官方版MV.
- B站备选: `BV1Fh411a7ok` | 5:17 | KTV 标清 MV.
- Final choice: YouTube official MV.
- Reason: official source, stereo audio, dynamic MV, no platform watermark; bottom lyric subtitles can be cropped/masked.
- Final window: source `213.60s` for `48.0s`, vfill crop `712:400:0:0`; final HTML adds lower lyric mask.

### 第4名《你是我的人》

- YouTube: `K2DCrK9BcWk` | 5:49 | album upload, not official MV.
- YouTube Topic: `nzHYON3bKoU` | 5:48 | remastered audio, static/topic style.
- B站: `BV1D36eB5Eng` | 5:49 | square album-cover source, stereo audio.
- B站备选: `BV1P3szeKE5L` | 5:49 | 配乐4k视频; detected 1080p/480p dynamic streams, but direct stream downloads stalled before completion.
- Final choice: B站 `BV1D36eB5Eng`.
- Reason: no clean dynamic MV/live source found after YouTube + B站 search; downloaded source has correct song audio and can be presented as album-sleeve visual treatment.
- Final window: source `213.90s` for `51.0s`, vfill crop `1080:900:0:0` to remove bottom metadata.

### 第3名《一万一千公里》

- YouTube: `https://www.youtube.com/watch?v=ylNK4Ug1GKU` | 3:40 | Timeless Music | official完整版MV.
- B站: `BV16t4y1e7iK` | 3:40 | MV.
- B站备选: `BV1yjVBzAEyr` | 3:41 | DVD MTV Karaoke 1080P60.
- Final choice: YouTube official MV.
- Reason: official source, stereo audio, dynamic MV; bottom title/lyric bands can be cropped/masked.
- Final window: source `110.10s` for `51.0s`, vfill crop `712:392:0:0`.

### 第2名《白丝线》

- YouTube: `https://www.youtube.com/watch?v=mLwbepLXFLI` | 4:54 | Timeless Music | official完整版MV.
- B站: `BV1o7411b7Pj` | 4:54 | MTV天籁村.
- B站 official: `BV1hAsgztEh4` | 4:56 | 华纳音乐中国.
- B站备选: `BV1uo4y1X7yL` | 4:49 | KTV 标清版.
- Final choice: YouTube official MV.
- Reason: official source, stereo audio, dynamic MV; subtitle bands are manageable with crop/mask.
- Final window: source `204.70s` for `48.0s`, vfill crop `712:340:0:0`; final HTML adds lower lyric mask.

### 第1名《愿赌服输》

- YouTube: `https://www.youtube.com/watch?v=bY78FSzxMDY` | 3:51 | Timeless Music | official完整版MV.
- B站: `BV1hD4y1D7Tg` | 3:51 | 官方版MV.
- B站 repair: `BV1sRnBzQEET` | 3:52 | 4K修复.
- B站 DVD: `BV1PjJuzAEXT` | 3:57 | DVD MTV Karaoke 1080P60.
- Final choice: YouTube official MV.
- Reason: official source and stereo audio. It has title/lyric overlays, but this is acceptable for old official MV and can be cropped/masked.
- Final window: source `153.40s` for `54.0s`, vfill crop `712:400:0:0`.

## QA artifacts

- Raw source contact sheets: `probes/raw_*_sheet.jpg`
- Final clip sheets: `qa/clip_*_sheet.jpg`
- Final video sheet: `qa/final_sheet.jpg`
- Key frames: `qa/frame_cover.jpg`, `qa/frame_p5_label.jpg`, `qa/frame_p4_label.jpg`, `qa/frame_p1_label.jpg`, `qa/frame_outro.jpg`, `qa/frame_cta.jpg`
