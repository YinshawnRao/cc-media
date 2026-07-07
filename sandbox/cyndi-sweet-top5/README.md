# 王心凌最甜的5首歌

Vertical countdown video, playback order from #5 to #1:

1. `05` 爱的套餐
2. `04` 彩虹的微笑
3. `03` 睫毛弯弯
4. `02` 爱你
5. `01` Honey

## Build

Run from repo root:

```bash
tools/tts/venv/bin/python sandbox/cyndi-sweet-top5/build/narrate_segments.py
tools/tts/venv/bin/python sandbox/cyndi-sweet-top5/build/full_build.py
cd sandbox/cyndi-sweet-top5
npx hyperframes lint
npx hyperframes render --output renders/full_raw.mp4 --sdr
ffmpeg -y -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/cyndi-sweet-top5.mp4
```

## Source Prep Already Done

Official YouTube HLS downloads are stored in `raw/`. The derived vertical clips are stored in `clips/` and were generated with `tools/video/vfill.sh`.

`full_build.py` writes:

- `master.wav` - pre-mixed final audio for post-render mux
- `index.html` - HyperFrames composition
- `meta.json` - timing metadata
- `probe/showcase_plan.json` - vocal/showcase alignment plan

Final QA should use `ffprobe`, `silencedetect`, `volumedetect`, and a frame contact sheet.
