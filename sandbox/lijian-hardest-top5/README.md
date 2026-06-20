# 李健最难的5首歌

Working project for a vertical HyperFrames countdown video.

## Current Artifacts

- `build/narrate_segments.py` generates female narration wavs.
- `build/full_build.py` generates `master.wav`, `index.html`, and `meta.json`.
- `SOURCES.md` records YouTube+B站 candidate search and final source choices.
- Final render should be muxed with `master.wav`; do not trust HyperFrames render audio as final.

## Build

```bash
tools/tts/venv/bin/python sandbox/lijian-hardest-top5/build/narrate_segments.py
python3 sandbox/lijian-hardest-top5/build/full_build.py
cd sandbox/lijian-hardest-top5
npx hyperframes lint
npx hyperframes render --output renders/full.mp4 --sdr
ffmpeg -i renders/full.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/lijian-hardest-top5.mp4
```
