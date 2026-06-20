# 郁可唯最难的5首歌

Final render:

- `renders/yukewei-hardest-top5.mp4`
- 1080x1920, H.264, 30fps, AAC stereo
- Duration: 315.275s

## Build

```bash
../../tools/tts/venv/bin/python build/narrate_segments.py
../../tools/tts/venv/bin/python build/full_build.py
npx -y hyperframes@0.6.47 lint sandbox/yukewei-hardest-top5
npx -y hyperframes@0.6.47 inspect sandbox/yukewei-hardest-top5 --samples 12
npx -y hyperframes@0.6.47 validate sandbox/yukewei-hardest-top5
npx -y hyperframes@0.6.47 render sandbox/yukewei-hardest-top5 --output sandbox/yukewei-hardest-top5/renders/full_raw.mp4 --sdr
ffmpeg -i sandbox/yukewei-hardest-top5/renders/full_raw.mp4 -i sandbox/yukewei-hardest-top5/master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest sandbox/yukewei-hardest-top5/renders/yukewei-hardest-top5.mp4 -y
```

## QA Summary

- `npx -y hyperframes@0.6.47 lint`: 0 errors, 3 non-blocking warnings.
- `npx -y hyperframes@0.6.47 inspect --samples 12`: current run hit `Navigation timeout of 10000 ms exceeded`; final render was visually checked by extracted frames instead.
- `npx -y hyperframes@0.6.47 validate`: no console errors, 110 text elements pass WCAG AA.
- Final MP4: 1080x1920 H.264 30fps + 48k stereo AAC.
- Final `silencedetect=n=-35dB:d=1`: no >1s silence reported.
- Final `volumedetect`: mean `-15.7 dB`, max `-0.1 dB`.
- Updated cover frames checked: `qa/final_cover_v2_2s.jpg`, `qa/final_cover_v2_10s.jpg`, `qa/final_cover_v2_15s.jpg`.
- Final keyframe sheet: `qa/final_contact.jpg`.
- Showcase vocal activity check: `qa/show_vocals.json`.

## Notes

- Ranking order in the video is countdown order: 05 `时间煮雨` → 04 `思慕` → 03 `知否知否` → 02 `指望` → 01 `路过人间`.
- Opening cover visual now uses `clips/vert_cover_simu.mp4`, cut from the `思慕` source around the Yisa Yu close-up and slowed to cover the full intro.
- Female narration uses Kokoro `zf_xiaoyi`.
- Final audio is the pre-mixed `master.wav` muxed after HyperFrames render.
- Source search and selection details are in `SOURCES.md`.
