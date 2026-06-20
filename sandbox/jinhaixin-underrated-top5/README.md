# jinhaixin-underrated-top5 — 金海心最被低估的5首歌

竖屏 1080x1920 倒数盘点（5 -> 1），女声解说，连续歌曲展示段，最终音频以后期 `master.wav` mux 为准。

倒数顺序：
第5《来不及》 -> 第4《比天空还远的季节》 -> 第3《对岸》 -> 第2《睡不着的海》 -> 第1《右手戒指》。

## Reproduce

```bash
tools/tts/venv/bin/python build/narrate_segments.py
python3 build/full_build.py
npx hyperframes lint
npx hyperframes inspect --samples 12
npx hyperframes render --output renders/full_raw.mp4 --sdr -w 1
ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/jinhaixin-underrated-top5.mp4
```

Final delivery is `renders/jinhaixin-underrated-top5.mp4`.

Sources and crop decisions are documented in `SOURCES.md`.
