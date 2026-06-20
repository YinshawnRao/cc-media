# 袁娅维最难的5首歌

Vertical HyperFrames ranking video. The project keeps all reproducible inputs under this sandbox directory.

## Build

```bash
tools/tts/venv/bin/python sandbox/tia-ray-hardest-top5/build/narrate_segments.py
tools/tts/venv/bin/python sandbox/tia-ray-hardest-top5/build/full_build.py
cd sandbox/tia-ray-hardest-top5
npx hyperframes lint
npx hyperframes inspect --samples 12
npx hyperframes render --output renders/full_raw.mp4 --sdr
ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/tia-ray-hardest-top5.mp4
```

## Notes

- Spoken `Starfall` is written as `Star fall` in the TTS text to avoid a wrong merged pronunciation.
- Screen text still displays `《Starfall》`.
- Final deliverable is the post-mux MP4, not the raw HyperFrames render.
