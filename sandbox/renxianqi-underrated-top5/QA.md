# QA

Final output: `renders/renxianqi-underrated-top5.mp4`

Generated on 2026-06-21. Final video is the muxed MP4, not the raw HyperFrames render.

## Build Checks

- `npx --yes hyperframes@0.6.69 lint`: 0 errors, 4 warnings.
  - Warnings: dense tracks on 2/4/8, and font fallback warning for `PingFang SC`.
  - Render compiler mapped and injected deterministic `Noto Sans SC`; `Noto Serif SC` and `PingFang SC` fall back.
- `npx --yes hyperframes@0.6.69 validate`: no console errors; 145 text elements pass WCAG AA.
- `npx --yes hyperframes@0.6.69 render --output renders/full_raw.mp4 --sdr`: completed, 1080x1920, 30fps.
- Final audio was post-muxed with `master.wav`:
  - `ffmpeg -y -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/renxianqi-underrated-top5.mp4`

## Final Media Probe

`ffprobe -v error -show_entries format=duration,bit_rate:stream=index,codec_name,codec_type,width,height,r_frame_rate,sample_rate,channels -of json renders/renxianqi-underrated-top5.mp4`

- Duration: `281.701000`
- Bitrate: `3497374`
- Video: H.264, `1080x1920`, `30/1`
- Audio: AAC, `48000 Hz`, stereo

## Latest Recut Scope

User feedback: `别哭` still sounded like background only, and `安静的人` had too little vocal before ending. This pass only changed #2 and #1. #5, #4, and #3 were left unchanged.

Updated windows:

- #2 `别哭`: source vocal target `185.0s`, showcase `36.0s`.
  - Clip seek: `172.85s`
  - Narration ends at local `14.15s`; full-volume section starts at local `15.75s`.
  - Full-volume source range is approximately `188.60s-224.60s`.
- #1 `安静的人`: source vocal target `211.9s`, showcase `62.0s`.
  - Clip seek: `200.775s`
  - Narration ends at local `13.125s`; full-volume section starts at local `14.725s`.
  - Full-volume source range is approximately `215.50s-277.50s`.

## Vocal Verification

Frequency-band vocal detection alone was not trusted for this pass because it can misclassify mid-frequency background instruments as vocals. Local Whisper `small` transcription was used as an additional check.

`qa/transcribe/recut_clips_v2.json`

- #2 `p2_bieku` transcription includes clear sung lines:
  - local `13.28-18.24`: `我们没有真情可以这风荡雨`
  - local `18.24-22.56`: `别哭 我想爱的你`
  - local `25.92-33.92`: `爱你 爱我之后`
  - local `36.64-41.88`: `爱你 爱我 哦哦哦`
  - Full-volume starts at local `15.75s`, inside this continuous sung section.
- #1 `p1_anjing` transcription includes longer vocal blocks:
  - local `12.00-45.00`: repeated sung phrase block
  - local `51.00-76.00`: additional sung/ad-lib phrases
  - Full-volume starts at local `14.725s`, inside the first vocal block.

`../../tools/tts/venv/bin/python ../../tools/video/vocal_segments.py clips_seg/p2_bieku.mp4 clips_seg/p1_anjing.mp4 -o qa/recut_p2_p1_vocal_segments_v2.json`

- #2 `p2_bieku`: vocal segments `17.18-22.18`, `29.12-31.30`, `39.10-51.57`.
- #1 `p1_anjing`: vocal segment `12.38-45.44`.

## Audio QA

`ffmpeg -hide_banner -i renders/renxianqi-underrated-top5.mp4 -af silencedetect=n=-35dB:d=1 -f null -`

- Result: no `silence_start` / `silence_end` lines reported.

`ffmpeg -hide_banner -i renders/renxianqi-underrated-top5.mp4 -af volumedetect -f null -`

- Mean volume: `-17.7 dB`
- Max volume: `-0.5 dB`

## Visual QA

Generated checks:

- `qa/final_recut_contact.jpg`: final timeline samples at 1, 30, 50, 72, 81, 100, 121, 132, 145, 165, 180, 195, 220, 248, 265, 278 seconds.
- `qa/p2_recut_v2_contact.jpg`: #2 longer recut local contact sheet.
- `qa/p1_recut_v2_contact.jpg`: #1 longer recut local contact sheet.

Visual findings:

- Countdown order is correct: 05 `爱伤了`, 04 `约定蓝天`, 03 `心情车站`, 02 `别哭`, 01 `安静的人`.
- No visible file paths, prompts, URLs, or platform/UP watermarks in sampled final frames.
- #2 `别哭` still uses the clean static high-quality source; the dirty album-source frame with B站 mark and full-screen lyrics was only used for cross-checking, not final video.
- #1 `安静的人` keeps the low-resolution old MV source, but the longer window remains cropped away from top watermark and bottom lyric bands.

## Source Limitation

Both YouTube and B站 were searched for each song. YouTube metadata search returned candidates, but direct extraction/download was blocked by YouTube's bot sign-in gate with the available cookie file. This final cut therefore uses the selected B站 downloadable sources recorded in `SOURCES.md`.

For #1, an additional B站 album/full-disc source `BV1Ny411h7XC` was downloaded only as a cross-check for song identity and lyric placement. The final picture source remains the selected single-MV source.

## Non-Blocking Note

`hyperframes inspect` timed out on this media-heavy project during a prior check and was not rerun for this pass. Final acceptance relied on `lint`, `validate`, successful render, mux, ffprobe, audio filters, Whisper transcription, vocal-segment detection, and visual frame QA.
