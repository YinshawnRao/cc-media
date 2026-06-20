# QA — 那英最被低估的5首歌

Final artifact:

- `renders/naying-underrated-top5.mp4`

## Checks

- HyperFrames lint: `0 error(s), 4 warning(s)` after fixing clip visibility animation.
- HyperFrames inspect: `ok: true`, `issueCount: 0`, 12 samples.
- Render: `npx hyperframes render --output renders/full_raw.mp4 --sdr` completed.
- Final mux: `ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/naying-underrated-top5.mp4`.

## Final file

`ffprobe`:

- Duration: `291.876000s`
- Video: H.264, `1080x1920`, 30fps, SDR BT.709
- Audio: AAC stereo, 48kHz, 192k-class
- Size: `104476144` bytes

## Audio

`silencedetect=n=-35dB:d=1` reported no silence intervals.

Full-music 20s volume samples:

| Song | Final time sample | mean | max |
|---|---:|---:|---:|
| 船 | 38.95s | -15.8 dB | -3.5 dB |
| 你是我的人 | 87.13s | -16.5 dB | -3.5 dB |
| 一万一千公里 | 136.83s | -15.6 dB | -1.6 dB |
| 白丝线 | 185.25s | -16.7 dB | -5.1 dB |
| 愿赌服输 | 233.53s | -16.6 dB | -3.1 dB |

## Visual

Reviewed:

- `qa/final_sheet.jpg`
- `qa/frame_cover.jpg`
- `qa/frame_p5_label.jpg`
- `qa/frame_p4_label.jpg`
- `qa/frame_p1_label.jpg`
- `qa/frame_outro.jpg`
- `qa/frame_cta.jpg`

Findings:

- No visible local path, prompt text, URL, or platform watermark in final sampled frames.
- Opening does not reveal the full song list.
- Countdown order is 5 -> 1.
- Outro list is 5 -> 1 and fixed CTA appears after the project outro.
- `你是我的人` uses a static album-source visual because no clean dynamic MV/live source was found; this limitation is recorded in `SOURCES.md`.
