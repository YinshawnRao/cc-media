# 薛之谦最被低估的5首歌

Sandbox project for a vertical HyperFrames countdown video.

## Target

Title: 薛之谦最被低估的5首歌

Reveal order: #5 -> #1, preserving the user's ranking:

1. 违背的青春
2. 等我回家
3. 小孩
4. 背过手
5. 银河少年

## Build Flow

```bash
tools/tts/venv/bin/python sandbox/xuezhiqian-underrated-top5/build/narrate_segments.py
python3 sandbox/xuezhiqian-underrated-top5/build/prep_footage.py
python3 sandbox/xuezhiqian-underrated-top5/build/full_build.py
cd sandbox/xuezhiqian-underrated-top5/hf
npx hyperframes lint
npx hyperframes render --output ../renders/full_raw.mp4 --sdr
ffmpeg -i ../renders/full_raw.mp4 -i ../master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest ../renders/xuezhiqian-underrated-top5.mp4
```

Final QA must inspect muxed `renders/xuezhiqian-underrated-top5.mp4`, not the raw HyperFrames render.
