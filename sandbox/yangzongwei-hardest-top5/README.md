# 杨宗纬最难的5首歌

Working sandbox for a vertical countdown video.

Target:

- Title: 杨宗纬最难的5首歌
- Voice: female `zf_xiaoyi`
- Order: 5 -> 1 during the countdown
- Opening: no full ranking reveal
- Ending: ranking summary allowed
- Final render must be muxed with pre-mixed `master.wav`

Expected final artifact:

- `renders/yangzongwei-hardest-top5.mp4`

Render notes:

- `index.html` remains the HyperFrames source.
- HyperFrames lint passed with 0 errors via local npm cache.
- HyperFrames inspect/render were blocked in this sandbox by `listen EPERM: operation not permitted 0.0.0.0`; final delivery was produced with `build/ffmpeg_compose.py` using the same clips and pre-mixed `master.wav`.
- Final MP4: 1080×1920 H.264, AAC stereo, 289.478s.
