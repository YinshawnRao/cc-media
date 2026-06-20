# QA / Handoff — 陈楚生最被低估的5首歌

## Current State

- Project directory: `sandbox/chenchusheng-underrated-top5/`
- Scripts and docs created:
  - `design.md`
  - `.hyperframes/expanded-prompt.md`
  - `SOURCES.md`
  - `README.md`
  - `build/narrate_segments.py`
  - `build/make_clips.sh`
  - `build/full_build.py`
- Generated assets:
  - `audio/*.wav`
  - `clips/vert_*.mp4`
  - `master.wav`
  - `index.html`
  - `meta.json`
  - `renders/full_raw.mp4`
  - `renders/chenchusheng-underrated-top5.mp4`
  - `qa/final_sheet.jpg`
  - `qa/final_cta_294.jpg`

## Timing

- Total duration: `304.550000s`
- Intro ends: `16.775s`
- Outro starts: `275.35s`
- Full-music windows:
  - `先这样吧`: `35.900s`
  - `辩证关系`: `86.025s`
  - `35`: `135.975s`
  - `追风筝的孩子`: `186.775s`
  - `一个人唱情歌`: `239.350s`

## HyperFrames Check

- `npx hyperframes lint`: `0 error(s), 3 warning(s)`
  - `gsap_studio_edit_blocked` on GSAP-controlled elements.
  - `timeline_track_too_dense` on tracks 2 and 4.
- `npx hyperframes inspect --samples 15`: `0 layout issues across 15 sample(s)`.

## Final Render QA

- Raw render: `renders/full_raw.mp4`
- Final muxed output: `renders/chenchusheng-underrated-top5.mp4`
- Final file size: `156M`
- `ffprobe` final output:
  - duration: `304.550000s`
  - video: H.264, `1080x1920`, `30/1` fps
  - audio: AAC, stereo, `48000 Hz`
- Final `silencedetect=n=-35dB:d=1`: no `silence_start` / `silence_end` events reported.
- Final full-music `mean_volume` checks:
  - `先这样吧`: `-15.2 dB`
  - `辩证关系`: `-14.3 dB`
  - `35`: `-15.7 dB`
  - `追风筝的孩子`: `-16.2 dB`
  - `一个人唱情歌`: `-16.0 dB`
- Final contact sheet: `qa/final_sheet.jpg`
- CTA frame: `qa/final_cta_294.jpg`

## Visual Check

- Cover, five ranking cards, full-music windows, final ranking list, and CTA are present in sampled frames.
- No local path, prompt text, URL, or obvious platform watermark is visible in sampled final frames.
- Known source limitation: `先这样吧` MiniLive contains stage/projection lyric text inside the performance image; platform/account watermark was removed by crop.
