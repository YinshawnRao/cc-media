# 王嘉尔最难的5首歌

Sandbox build for the requested ranking/countdown video.

Final artifact:

- `renders/wangjiaer-hardest-top5.mp4`
- Duration: `347.10s`
- Format: `1080x1920`, H.264 video, AAC stereo audio.
- Audio source: rendered video stream muxed with pre-mixed `master.wav`.

Core constraints:

- Reveal order: 5 to 1.
- Opening: cover + premise only, no ranking list leak.
- Female narration: intro, each transition, outro.
- Continuous showcase segment per song.
- Use `master.wav` mux after HyperFrames render.

Final QA:

- Source search documented for both YouTube and B站 in `SOURCES.md`.
- HyperFrames lint: 0 errors; warnings only for dense timeline tracks.
- HyperFrames inspect: 0 layout issues across sampled frames.
- Frame check: opening does not expose ranking list; outro does.
- Frame check: sampled vertical frames show no visible platform watermark, URL, local path, or prompt leakage.
- Audio check: `silencedetect=n=-35dB:d=1` reports no >1s silence.
- Main showcase volumedetect ranges: mean about `-14.7` to `-15.5 dB`, max about `-4.2` to `-0.7 dB`.
