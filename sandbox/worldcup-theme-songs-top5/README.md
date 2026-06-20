# 世界杯最佳主题曲 TOP5

Local sandbox project for a vertical HyperFrames countdown video.

## Build

```bash
cd /Users/yinshawnrao/explorer/cc-media/sandbox/worldcup-theme-songs-top5
../../tools/tts/venv/bin/python build/narrate_segments.py
../../tools/tts/venv/bin/python build/full_build.py
npm run check
npx --yes hyperframes@0.6.52 render --output renders/full_raw.mp4 --sdr
ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/worldcup-theme-songs-top5.mp4 -y
```

Final output should be the muxed MP4 in `renders/`, not the raw HyperFrames render.
