# Sources — 金海心最被低估的5首歌

Cookie files checked:
- YouTube: `sandbox/www.youtube.com_cookies.txt`
- B站: `sandbox/www.bilibili.com_cookies.txt`

Selection rule: every song was searched on YouTube and B站. Final clips were frame-checked; platform/UP watermarks and burned text were cropped out when possible.

## Search Summary

| Rank | Song | YouTube candidates | B站 candidates | Final choice |
| --- | --- | --- | --- | --- |
| 05 | 来不及 | YT `9qxj9IEuPtQ` — 赵小盒, 高画质官方完整版MV | B站 `BV1oL8wevEtm` — 4K60 AI修复；`BV12dhbzxEXK` — exact song | **B站 `BV1oL8wevEtm`**. Clean dynamic MV, 1440x1080/60fps section, only bottom lyrics cropped. |
| 04 | 比天空还远的季节 | YT `tnEgoAKIikU` — exact song audio/static style; same-album YT MVs include `L9uvDlf_7Vw`/`PngYWPnVuJI` | B站 `BV1P7v9B5EBf` — exact song, 640x480 low-bitrate static with bilibili watermark; B站 `BV1pq7zzGEca` — 《阳光下的星星》无字版 1080p | **Audio from exact B站 `BV1P7v9B5EBf`; visual from same-album B站 `BV1pq7zzGEca`**. Exact source was static/watermarked, so clean same-album MV visual is used as rescue footage. |
| 03 | 对岸 | YT Topic `gP8N8pynppY` — exact official audio; no clear MV in search | B站 `BV1m9hbzoEbp` — exact song, 1080p but static lyric/cover; B站/YouTube 《悲伤的秋千》 candidates had T-Video/bilibili and lyric burn-ins | **Audio from exact B站 `BV1m9hbzoEbp`; visual from YouTube 《悲伤的秋千》 `4OfIIt3to2Y` after aggressive full-width crop**. Same-album visual rescue; crop removes top/bottom platform/lyric marks. |
| 02 | 睡不着的海 | YT `AEwbUQIwRMY` — 金海心 睡不着的海 MV 1999 | B站 `BV1As8RzSE8n` — 母带/全网首发 MV 1999, 1440x1080 | **B站 `BV1As8RzSE8n`**. Better resolution and cleaner frame than YouTube; bottom lyrics cropped. |
| 01 | 右手戒指 | YT `v6qRQoCHu8o` — 高画质官方完整版MV; Topic `ImwC8J4Hai8` audio | B站 `BV1vu4y1c73t` — 720x576 MV; other exact uploads lower quality | **YouTube `v6qRQoCHu8o`**. Dynamic MV and stable stereo audio; top logo and bottom lyrics cropped. |

## Final Clip Files

- `clips/vert_p5_laibuji.mp4`
- `clips/vert_p4_bitian.mp4`
- `clips/vert_p3_duian.mp4`
- `clips/vert_p2_sleep.mp4`
- `clips/vert_p1_right.mp4`

## Crop / Rescue Notes

- 《右手戒指》: crop `640:255:0:145` removes upper channel logo and lower burned lyrics, leaving a clean central 4:3 band.
- 《睡不着的海》: crop `1440:800:0:0` removes bottom lyric line while preserving face and street shots.
- 《对岸》: exact B站 video is static, so it contributes audio only. Visual rescue uses 《悲伤的秋千》 with crop `960:430:0:135`, removing top logo and bottom T-Video/bilibili/lyrics.
- 《比天空还远的季节》: exact B站 video is static and watermarked, so it contributes audio only. Visual rescue uses clean same-album 《阳光下的星星》无字版.
- 《来不及》: crop `1440:850:0:0` removes bottom lyrics.

Probe sheets are saved in `probes/`.
