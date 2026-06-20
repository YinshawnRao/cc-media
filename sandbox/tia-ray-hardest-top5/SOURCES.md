# Sources — 袁娅维最难的5首歌

Cookie files checked: YouTube `sandbox/www.youtube.com_cookies.txt` · B站 `sandbox/www.bilibili.com_cookies.txt`

Selection rule: every song was searched on both YouTube and B站. This project prioritizes official MV / official live footage, clean moving performance footage, stereo audio, and a continuous sung showcase. B站 was searched for all songs; B站 direct download for the preferred 《开往春天的地铁》 repaired candidate exposed a valid 1080p stream but stalled before file creation, so the downloaded YouTube / Mango official source is used with crop cleanup.

Ranking order from the brief is preserved. The video reveals in reverse order: 05 -> 01.

## Candidate Notes

### 01.《Starfall》
- YouTube: `ukXlTuH65Bs` MangoTV official Singer 2020 pure performance, 1920x1080, dynamic live footage, stereo. Pollution: top-left Mango logo, top-right Mango HD mark, bottom subtitles, show corner bug.
- YouTube: `3zND0qxnr7Y` TIA RAY official `Starfall (Live)`, 1080x1080 but static Singer title card for the whole video -> rejected.
- B站: `BV1fT4y1g7jC` Singer 2020 live candidate; `BV1cg411G74v` fan upload. Searched as required; not selected over Mango official dynamic source.
- Final: YouTube Mango official `ukXlTuH65Bs`. Crop uses a centered live-performance region to exclude platform/show marks.

### 02.《别废话》
- YouTube: `W2fc8QE_pUQ` Warner Music China official MV, 2560x1066, dynamic MV, stereo. Pollution: top-right Warner mark and bottom bilingual lyrics.
- B站: `BV1Eb4y1X7Bt` 华纳音乐中国 `别废话 - 袁娅维`; `BV1k7411p76P` blue-ray copy; `BV1wa1iYoEex` karaoke. Searched as required.
- Final: YouTube Warner official `W2fc8QE_pUQ`. Crop removes mark and lyrics while keeping the cinematic center action.

### 03.《旅行中忘记》
- YouTube: `OqCQkvA3JLo` TIA RAY official MV, 1920x1080, dynamic MV, stereo. Pollution: top-right Warner mark, occasional vertical title text as part of MV.
- B站: `BV1ms411a7kf` MV; `BV1BJS8YLEdM` 4K repair; `BV1AU4y1f7VK` blue-ray MV. Searched as required.
- Final: YouTube TIA RAY official `OqCQkvA3JLo`. Crop removes the Warner mark and keeps clean closeups.

### 04.《开往春天的地铁》
- YouTube: `26FFlAVWNdE` MangoTV official Singer 2017 performance, 1920x1080, dynamic live footage, stereo. Pollution: Mango logo, HD mark, show corner bug, bottom program bar / subtitles.
- YouTube: `CT4RYZksE-k` TIA RAY official `Live`, appears as audio/title-style upload in search.
- B站: `BV1KXQZY5E5V` 4K repair candidate; stream probe found 1920x1080 AVC + AAC but direct download stalled before writing output. `BV1SLzHYSEXV` and reaction/editorial uploads were also visible in search.
- Final: YouTube Mango official `26FFlAVWNdE`, using a centered crop that removes all top/bottom/right show marks.

### 05.《阿楚姑娘》
- YouTube: `VRQERjVqyd4` Warner Music China official promotional video, 1280x720, mostly still/portrait loop -> rejected for showcase because it is not continuous singing footage.
- YouTube: `dUIEb7cE81s` MangoTV official Singer 2017 performance, 854x480, dynamic live singing. Pollution: Mango logo, show corner bug, subtitles.
- B站: `BV1Js411Y7ag`, `BV1ZJ411G7wG`, `BV1m44y1G7ub` live/MV candidates. Searched as required.
- Final: YouTube Mango official live `dUIEb7cE81s`, because it gives actual sung performance footage.

## Final Windows

The source start for each vertical clip is calculated after TTS is generated:

`clip_start = vocal_show_start - (LEAD + voice_dur + 0.25 + DIG)`

That aligns the full-volume showcase to the real sung entry immediately after the transition narration.

| rank | key | source | vocal show start | show | crop | note |
|---|---|---|---:|---:|---|---|
| 05 | p5_achu | `raw/p5_achu_singer.mp4` | 140.8s | 31s | `420:360:300:60` + timed `delogo` | Singer live; crop excludes Mango logo, subtitle line, and corner bug; timed blur softens the most visible stage sponsor board |
| 04 | p4_chuntian | `raw/p4_chuntian.mp4` | 87.8s | 26s | `780:720:640:110` | Singer 2017; uses the earlier 《开往春天的地铁》 sung section and avoids later `Kiss From A Rose` text |
| 03 | p3_lvxing | `raw/p3_lvxing.mp4` | 105.4s | 31s | `1080:820:420:80` | Official MV; keeps white-room closeups and removes Warner mark |
| 02 | p2_biefeihua | `raw/p2_biefeihua.mp4` | 39.7s | 29s | `1280:820:640:70` | Warner official MV; uses the early TIA-led sung section instead of the later male-rap section |
| 01 | p1_starfall | `raw/p1_starfall.mp4` | 206.8s | 38s | `1040:760:440:90` | Mango Singer 2020; centered single-performer crop removes visible platform/show marks |

## QA Targets

- Final MP4 must be 1080x1920, H.264, AAC stereo.
- Final render must be muxed with `master.wav`, not HyperFrames render audio.
- Frame QA must confirm no platform watermark, URL, local path, prompt text, or project-internal words in sampled frames.
- Audio QA must confirm no unacceptable silence, and showcase sections are materially louder than narration-bed sections.
