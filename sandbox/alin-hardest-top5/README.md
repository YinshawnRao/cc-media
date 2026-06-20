# 黄丽玲 A-Lin 最难的5首歌

Final output:

- `renders/alin-hardest-top5.mp4`
- Duration: 290.357s
- Format: 1080x1920, 30fps, SAR 1:1, DAR 9:16
- Audio: AAC stereo, muxed from `master.wav`

## Build

```bash
tools/tts/venv/bin/python sandbox/alin-hardest-top5/build/narrate_segments.py
tools/tts/venv/bin/python sandbox/alin-hardest-top5/build/full_build.py
tools/tts/venv/bin/python sandbox/alin-hardest-top5/build/ffmpeg_compose.py
```

`build/full_build.py` still generates the HyperFrames HTML (`index.html`) and the post-mix audio master (`master.wav`). The final MP4 was rendered with `build/ffmpeg_compose.py` because this sandbox rejects the local HTTP server that HyperFrames render/inspect needs, even when bound to `127.0.0.1`.

## Ranking

1. `05` 《失恋无罪》
2. `04` 《有一种悲伤》
3. `03` 《幸福了 然后呢》
4. `02` 《天若有情》
5. `01` 《给我一个理由忘记》

The final video presents them countdown-style from 05 to 01.

## Source Notes

See `SOURCES.md` for YouTube + B站 search coverage, candidates, rejection reasons, and final source choices.

## QA

Final checks:

- `ffprobe`: 1080x1920, 30fps, SAR 1:1, DAR 9:16, duration 290.357s.
- `volumedetect`: mean volume -15.9 dB, max volume -0.1 dB.
- `p4_sorrow` showcase check: final full-music segment starts at 76.975s in the rendered video and uses the TFT raw window `172.32s-206.32s`; extracted preview is `qa/sorrow_final_recut/showcase_audio.mp3`.
- `silencedetect=n=-35dB:d=1`: no silence intervals reported.
- `blackdetect=d=0.5:pix_th=0.10`: no black intervals reported.
- `freezedetect=n=-60dB:d=2`: no freeze intervals reported.
- Visual contact sheet: `qa/final_contact.jpg`; sampled frames show readable text and no platform watermark, URL, prompt, or local path leakage.
