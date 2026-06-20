# Sources — 黄丽玲 A-Lin 最难的5首歌

Cookie files checked:

- YouTube: `sandbox/www.youtube.com_cookies.txt`
- B站: `sandbox/www.bilibili.com_cookies.txt`

Selection rule: every song was searched on both YouTube and B站. Final choice favors official/near-official source, clean frame, stereo/bitrate, and continuous usable vocal segment.

## 5.《失恋无罪》

- YouTube candidate: `https://www.youtube.com/watch?v=lmFlqWPzl-E` — avex 官方 MV, 4:03, 1280x720, clean but lower detail.
- B站 final candidate: `BV17MgTz4EAy` — 4K 修复 MV, downloaded as 1920x1080 H.264, AAC, no visible B站/UP watermark in sampled frames; bottom MV subtitles can be removed by full-width crop.
- Decision: choose B站 repair source for higher visual quality while keeping a clean crop.
- Working raw: `raw/p5_guilty_bi_4k.mp4`
- Planned crop: `1920:870:0:0`

## 4.《有一种悲伤》

- YouTube MV candidate: `https://www.youtube.com/watch?v=BRcudpJzy1I` — official movie-theme MV, 1920x1080, clean, mostly film footage.
- YouTube final candidate: `https://www.youtube.com/watch?v=ZqbjJa4UWBY` — THE FIRST TAKE, 1920x1080, clean studio performance, shows A-Lin singing throughout.
- B站 candidate: `BV1ey4y1y7io` — Sony Music China upload, 1920x1080, clean movie/performance MV.
- Decision: choose THE FIRST TAKE because this entry is about restrained vocal control; the source is clean and singer-focused.
- Working raw: `raw/p4_sorrow_yt_tft.mp4`
- Planned crop: `1920:1080:0:0`
- Final clip window: `156.75s-210.75s` in the raw TFT source. This replaces the earlier `121.6s` window so the full-music showcase starts on the stronger vocal passage around `172.32s`, instead of the softer humming/lead-in section.

## 3.《幸福了 然后呢》

- YouTube final candidate: `https://www.youtube.com/watch?v=m9eoYjo5W8c` — avex 官方 HD MV, 1920x1080, clean after bottom subtitle crop.
- B站 candidate: `BV1nr421x7ny` — 4K repair, downloaded as 1920x1080, but sampled frames show B站 watermark at the top.
- Decision: choose YouTube official HD for cleaner frame.
- Working raw: `raw/p3_happiness_yt.mp4`
- Planned crop: `1920:900:0:0`

## 2.《天若有情》

- YouTube final candidate: `https://www.youtube.com/watch?v=R5E_Am4kNII` — 1080p TV-drama theme MV/片花版, clean after bottom subtitle crop.
- YouTube candidate: `https://www.youtube.com/watch?v=7rbK-MBN9BI` — SMG official duet live, 1080p but has station logos and is not solo.
- B站 candidate: `BV1Lz4y1x7cY` — A-Lin B站 official summer live, 480x852 only; top B站/title text can be cropped, but mid-lower burned lyrics remain.
- Decision: choose YouTube 1080p theme MV. This song is introduced as an open, drama-theme-style big ballad, so the visual source matches the entry.
- Working raw: `raw/p2_tian_yt_mv.mp4`
- Planned crop: `1920:760:0:0`

## 1.《给我一个理由忘记》

- YouTube final candidate: `https://www.youtube.com/watch?v=F5FlN-NBGo8` — avex 官方 MV, 4:47, 640x480, clean after tighter crop.
- B站 candidate: `BV1NW411672N` — official-MV reupload, 480x360, lower than YouTube.
- B站 candidate: `BV1NB4y1k7He` — 1920x1080 live/pure enjoy, but sampled frames show program logos/burned lyric overlays and lower audio bitrate.
- Decision: choose YouTube avex official MV for clean official source despite lower resolution.
- Working raw: `raw/p1_reason_yt.mp4`
- Planned crop: `640:360:0:30`
