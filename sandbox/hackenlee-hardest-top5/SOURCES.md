# Sources — 李克勤最难的5首歌

Cookie files checked: YouTube `sandbox/www.youtube.com_cookies.txt`, B站 `sandbox/www.bilibili.com_cookies.txt`.

Selection rule: both YouTube and B站 were searched for every song. Prefer official MV, but for old songs where the official MV is unavailable, static, or low-performing as a vocal showcase, use a cleaner official/live/restored candidate and document the tradeoff.

## Initial Search Notes

### 1. 《我不会唱歌》
- YT search hit: `JOjCTESMdHs` — `李克勤 - 《我不會唱歌》MV` — channel `李克勤 Hacken Lee` — 3:21.
- Other YT hits include MangoTV/Sing China live versions.
- B站 hits are mostly live: `BV16CF8zvETc` 4K 李克勤&郎朗, `BV1AP41197Kd` 郎朗账号合作, plus concert clips.
- Initial preferred source was YT official MV `JOjCTESMdHs`; final decision below.

### 2. 《大会堂演奏厅》
- YT search hit: `lyhzolB4ue8` — `李克勤 - 《大會堂演奏廳》(HKPO + Hacken Lee Live)` — channel `李克勤 Hacken Lee` — 5:03.
- YT also has `nvsm36MlnK4` on official channel, likely audio/static; `dLEvUwDisIk` is a third-party 1988 MV upload.
- B站 hits are mostly live/TV: `BV1Na41137VA` Alan/Hacken 2003 4K60, `BV1fr4y1T7om` 2021 江苏跨年, `BV1AGEJ6rETV` 2023 港乐.
- Initial preferred source was YT official HKPO live `lyhzolB4ue8`; final decision below.

### 3. 《月半小夜曲》
- YT search did not surface an obvious current official MV; hits include third-party repair/MV and lyric videos.
- B站 hits: `BV1Ar4y1c7V4` MV 1080P, `BV1U64y1q772` 1080p 高清修复 MV, `BV1J64y1F7eb` 环球音乐中国 2002 Live.
- Initial preferred source was a B站 repaired MV candidate; final decision changed after B站 download failure and YouTube MV frame probe.

### 4. 《飞花》
- YT search hit: `NtGu_B6iBFM` — `「飛花（郭可盈客串演出）」- 李克勤` — channel `CuePoint: Movie & Music` — 4:00.
- YT official channel also has `8iqvQaU1LyY` title `飛花`, likely audio/static.
- B站 hits: `BV1QtnnzjECc` `李克勤 - 飞花`, plus KARAOKE/audio candidates.
- Initial preferred source was YT/CuePoint MV or B站 MV; final decision changed after frame probe showed heavy karaoke text and mostly剧情画面.

### 5. 《高妹》
- YT search hit: `5YNfNC6zSKQ` — `李克勤 - 高妹` — channel `李克勤 Hacken Lee` — 3:32.
- YT also has official live `0XXsv36_T18`.
- B站 hits: `BV1dL411x7Pp` 1080p 高清修复 MV, `BV1F8V6zAELX` TVB版MV, `BV1S54y157Gp` 李克勤/梁咏琪 MV.
- Initial preferred source was YT official `5YNfNC6zSKQ`; final decision below.

## Final Selection

### 5. 《高妹》 — YouTube official MV
- Final: YT `5YNfNC6zSKQ` — `李克勤 - 高妹` — channel `李克勤 Hacken Lee`.
- Reason: official channel MV, stereo audio, no platform/UP watermark. B站 has 1080p repaired MV (`BV1dL411x7Pp`) and TVB/MV variants, but YouTube official is the cleanest rights/source signal.
- Limitation: 640×480 AV1; bottom burned lyrics.
- Window: raw `129.00s`, duration `55.65s`; main full-music starts at final timeline `35.35s`.
- Crop: `640:360:0:0` removes bottom lyrics, preserves 4:3/letterbox presentation.

### 4. 《飞花》 — YouTube official TV/stage Live
- Final: YT `veRXpql9PFY` — Hunan TV International official channel stage clip.
- Reason: the CuePoint MV candidate `NtGu_B6iBFM` has heavy center/bottom karaoke lyrics and mostly剧情画面; B站 `BV1QtnnzjECc` appears to be the same MV family. For a vocal-difficulty video, the official stage clip is cleaner and keeps Hacken Lee onscreen.
- Limitation: not the original MV, but official TV/Live source; some lower-left lyrics in the raw were removed by a tighter crop.
- Window: raw `107.55s`, duration `56.60s`; detected long vocal section `122.42-165.79s`.
- Crop: `1920:650:0:0`.

### 3. 《月半小夜曲》 — YouTube official 2002 Live
- Final: YT `6FM7kARun4w` — `李克勤 - 月半小夜曲 (Live in Hong Kong / 2002)` — channel `李克勤 Hacken Lee`.
- Reason: B站 repaired MV candidates were searched (`BV1Ar4y1c7V4`, `BV1U64y1q772`), but `BV1U64y1q772` direct m4s download twice failed with curl exit 18; YouTube MV fallback `Kt0cNGrhUjg` was mostly剧情/群像 and heavy karaoke text. The official 2002 Live gives singer closeups and a clean sung segment.
- Limitation: official Universal logo appears early in the source, but the chosen window does not show it in the vertical clip contact sheet.
- Window: raw `190.25s`, duration `55.70s`; detected long vocal section `204.20-266.03s`.
- Crop: `640:480:0:0`.

### 2. 《大会堂演奏厅》 — YouTube official HKPO Live
- Final: YT `lyhzolB4ue8` — `李克勤 - 《大會堂演奏廳》(HKPO + Hacken Lee Live)` — channel `李克勤 Hacken Lee`.
- Reason: official channel live with orchestra and Hacken Lee vocal performance. B站 candidates were mostly TV/live reposts; old 1988 MV exists only as third-party upload in current search.
- Limitation: 640×480 AV1; early source has Universal logo, but the chosen window is clean in vertical contact sheet.
- Window: raw `192.40s`, duration `56.15s`; detected long vocal section `206.80-267.80s`.
- Crop: `640:480:0:0`.

### 1. 《我不会唱歌》 — YouTube official MV
- Final: YT `JOjCTESMdHs` — `李克勤 - 《我不會唱歌》MV` — channel `李克勤 Hacken Lee`.
- Reason: official MV directly matches the piano/classical-arrangement point in the brief. B站 live candidates include Lang Lang collaboration and 4K reposts, but current deliverable uses the official MV due source priority and existing successful download.
- Limitation: 640×480 AV1; the selected section is visually piano-heavy with fewer Hacken Lee closeups. If network quota is restored, a Lang Lang/official live candidate should be compared for a stronger singer/piano split.
- Window: raw `105.05s`, duration `57.33s`; detected long vocal section `120.65-196.53s`.
- Crop: `640:270:0:50` removes bottom lyric band and letterbox waste.

## QA So Far

- `clips/vert_*.mp4` generated with `build/cut_clips.sh`; all are 1080×1920 H.264/AAC with dense keyframes.
- Vertical contact sheets checked in `qa/vert_sheet_*.png`; `qa/vert_sheet_feihua_v2.png` is the post-crop-clean version.
- `master.wav` generated by `build/full_build.py`, duration `327.743s`.
- `silencedetect=n=-35dB:d=1` on `master.wav` reports no long silence.
- Showcase 30s `volumedetect` means:
  - `高妹`: `-15.5 dB`, max `-0.2 dB`
  - `飞花`: `-14.0 dB`, max `-1.6 dB`
  - `月半小夜曲`: `-14.8 dB`, max `-0.5 dB`
  - `大会堂演奏厅`: `-13.7 dB`, max `-0.6 dB`
  - `我不会唱歌`: `-14.6 dB`, max `-0.6 dB`
- HyperFrames `npx` lint/render is not yet run because the package is not cached locally and online `npx` access is currently blocked by system usage/network limits.
