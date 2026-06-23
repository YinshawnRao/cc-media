# QA Status

## HyperFrames

- `/Users/yinshawnrao/.npm-cache/_npx/9034813775a58c19/node_modules/.bin/hyperframes lint`: 0 errors.
- Warnings: dense single-file timeline and system-font fallback only.
- `inspect`: attempted after local-server permission was available, but this HyperFrames build still hit the internal 10s navigation timeout. Final visual verification was done from rendered frame sheets.
- `bash build/render.sh`: official HyperFrames render completed, then muxed `master.wav`.

## Official MP4

Generated official HyperFrames file:

`renders/eason-saddest-top5.mp4`

- Container: MP4.
- Video: H.264, 1080x1920.
- Audio: AAC stereo, muxed from `master.wav`.
- Duration: 293.292s.
- Silence: `silencedetect=n=-35dB:d=1` found no >1s silence.
- Showcase loudness checks:
  - 葡萄成熟时: mean -15.8 dB, max -5.7 dB.
  - 最佳损友: mean -15.7 dB, max -1.4 dB.
  - 人来人往: mean -14.1 dB, max -1.1 dB.
  - 明年今日: mean -15.5 dB, max -2.8 dB.
  - 富士山下: mean -14.6 dB, max -0.9 dB.
- Vocal alignment:
  - Each selected vocal starts 3.75s before the full-volume showcase point.
  - Showcase durations: 31s-42s, all continuous sections.
- Visual QA sheets:
  - `qa/final_contact.jpg`
  - `qa/final_contact_dense.jpg`

## Fallback MP4

The earlier no-server review file remains at `renders/eason-saddest-top5_fallback.mp4`, but the deliverable is the official HyperFrames render above.
