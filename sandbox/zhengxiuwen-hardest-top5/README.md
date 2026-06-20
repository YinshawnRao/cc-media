# 郑秀文最难的5首歌

Vertical countdown video sandbox.

- Title: 郑秀文最难的5首歌
- Voice: female `zf_xiaoyi` (Kokoro + misaki[zh])
- Order: countdown 5 → 1 (默契 → 不要惊动爱情 → 值得 → 终身美丽 → 煞科)
- Opening: cover + premise only, no ranking reveal (用户要求留悬念)
- Ending: 作品 outro 总结排名 + 主题升华 → 固定引流 CTA（全片最后一句，女声，逐字照念）
- Final render must be muxed with pre-mixed `master.wav`.

## Pipeline
- `build/narrate_segments.py` — female narration (intro / 5 songs / outro / outro_cta).
- `build/full_build.py` — builds `master.wav` (per-song 床→swell→展示, loudnorm I=-14) + `index.html`.
- Sources / clip windows / crops: see `SOURCES.md`. Design: `design.md`.

## Render + mux
```
npx hyperframes render --output renders/full_raw.mp4 --sdr -w1
ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/zhengxiuwen-hardest-top5.mp4
```

Expected final artifact: `renders/zhengxiuwen-hardest-top5.mp4` (~5:36, 1080×1920 H.264).
