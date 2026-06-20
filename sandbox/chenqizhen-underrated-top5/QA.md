# QA / Handoff — 陈绮贞最被低估的5首歌

## Current State

- Project directory: `sandbox/chenqizhen-underrated-top5/`
- Scripts and docs created:
  - `design.md`
  - `.hyperframes/expanded-prompt.md`
  - `SOURCES.md`
  - `README.md`
  - `build/download_sources.sh`
  - `build/make_clips.sh`
  - `build/narrate_segments.py`
  - `build/full_build.py`
- Generated assets:
  - `audio/*.wav`
  - `clips/vert_*.mp4`
  - `master.wav`
  - `index.html`
  - `meta.json`
  - `renders/full_raw.mp4`
  - `renders/chenqizhen-underrated-top5.mp4`
  - `qa/final_sheet.jpg`

## Timing

- Total planned duration: `300.0s`
- Intro ends: `19.825s`
- Outro starts: `269.65s`
- Full-music windows:
  - `距离`: `39.05s`
  - `太聪明`: `87.625s`
  - `躺在你的衣柜`: `137.7s`
  - `80%完美的日子`: `188.8s`
  - `腐朽`: `235.65s`

## Source / Clip QA

- `clips/vert_juli.mp4`: 64s, 1080x1920, official MV, bottom lyric band cropped.
- `clips/vert_taicongming.mp4`: 64s, 1080x1920, official MV, bottom lyric band cropped; source is only 640x480.
- `clips/vert_yigui.mp4`: 64s, 1080x1920, 2013 Live, single-subject crop removes right-bottom `yoyo` watermark.
- `clips/vert_wanmei80.mp4`: 64s, 1080x1920, official MV, no obvious watermark.
- `clips/vert_fuxiu.mp4`: 64s, 1080x1920, official MV, no platform watermark; stylized text is part of source MV.

Contact sheets:
- `qa/clip_juli_sheet.jpg`
- `qa/clip_taicongming_sheet.jpg`
- `qa/clip_yigui_sheet.jpg`
- `qa/clip_wanmei80_sheet.jpg`
- `qa/clip_fuxiu_sheet.jpg`

## Audio QA

- `master.wav` duration: `300.000000s`
- `silencedetect=n=-35dB:d=1`: no silence events reported.
- Full-music `mean_volume` checks:
  - `距离`: `-13.9 dB`
  - `太聪明`: `-15.5 dB`
  - `躺在你的衣柜`: `-16.1 dB`
  - `80%完美的日子`: `-14.1 dB`
  - `腐朽`: `-14.8 dB`

## HyperFrames Check

- `npx hyperframes lint`: `0 error(s), 3 warning(s)`
  - `gsap_studio_edit_blocked` on GSAP-controlled elements.
  - `timeline_track_too_dense` on tracks 2 and 4.
- `npx hyperframes inspect --samples 15`: `0 layout issues across 15 sample(s)`.

## Final Render QA

- Raw render: `renders/full_raw.mp4`
- Final muxed output: `renders/chenqizhen-underrated-top5.mp4`
- `ffprobe` final output:
  - duration: `300.000000s`
  - video: H.264, `1080x1920`, `30/1` fps
  - audio: AAC, stereo, `48000 Hz`
- Final `silencedetect=n=-35dB:d=1`: no silence events reported.
- Final full-music `mean_volume` checks:
  - `距离`: `-14.2 dB`
  - `太聪明`: `-15.3 dB`
  - `躺在你的衣柜`: `-16.1 dB`
  - `80%完美的日子`: `-14.4 dB`
  - `腐朽`: `-15.0 dB`
- Final contact sheet: `qa/final_sheet.jpg`

Visual check over `qa/final_sheet.jpg`: intro, five ranking cards, full-music windows, outro ranking and CTA are present. No platform watermark, URL, local path, or prompt text was visible in the sampled frames.
