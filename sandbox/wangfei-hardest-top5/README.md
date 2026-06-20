# 王菲最难的5首歌

Working sandbox for a vertical countdown video.

Target:

- Title: 王菲最难的5首歌
- Voice: female `zf_xiaoyi`
- Order: 5 -> 1 during the countdown
- Opening: no full ranking reveal
- Ending: ranking summary allowed, then fixed CTA as the last narration line
- Final render must be muxed with pre-mixed `master.wav`

Expected final artifact:

- `renders/wangfei-hardest-top5.mp4`
- Duration: 309.45s
- Format: 1080x1920, 30fps, SAR 1:1, DAR 9:16
- Audio: AAC stereo, muxed from `master.wav`

Build:

```bash
tools/tts/venv/bin/python sandbox/wangfei-hardest-top5/build/narrate_segments.py
tools/tts/venv/bin/python sandbox/wangfei-hardest-top5/build/full_build.py
npx hyperframes lint sandbox/wangfei-hardest-top5
npx hyperframes render sandbox/wangfei-hardest-top5 --output sandbox/wangfei-hardest-top5/renders/full_raw.mp4 --sdr
ffmpeg -i sandbox/wangfei-hardest-top5/renders/full_raw.mp4 -i sandbox/wangfei-hardest-top5/master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest sandbox/wangfei-hardest-top5/renders/wangfei-hardest-top5.mp4 -y
```

Fallback used for this run:

```bash
tools/tts/venv/bin/python sandbox/wangfei-hardest-top5/build/ffmpeg_compose.py
```

`index.html` remains the HyperFrames source. Browser render failed locally at frame capture because the sandboxed file-server/runtime path was unstable; the final MP4 was produced by the deterministic offline FFmpeg compositor using the same clips, overlays, timing, and `master.wav`.

Ranking:

- `05` 《开到荼蘼》
- `04` 《彼岸花》
- `03` 《寒武纪》
- `02` 《多得他》
- `01` 《脸》

Source notes:

See `SOURCES.md` for YouTube + B站 coverage, candidates, rejection reasons, and final source choices.

QA:

- HyperFrames lint: 0 errors, 3 non-blocking warnings.
- HyperFrames inspect: first run found `#ghost` overflow, fixed; later inspect attempts timed out during navigation on the heavy media page.
- Final MP4 `ffprobe`: 1080x1920 H.264, 30fps, AAC stereo, duration 309.45s.
- `silencedetect=n=-35dB:d=1`: no silence intervals reported.
- `volumedetect`: mean volume -16.8 dB, max volume -0.4 dB.
- `freezedetect=n=-60dB:d=2`: no freeze intervals reported.
- `blackdetect`: two dark-card/dark-footage false positives at 175.93-177.03s and 237.67-243.93s; reviewed frames `qa/final_t176.png` and `qa/final_t238.png`.
- Visual contact sheet: `qa/final_contact.jpg`; sampled frames show readable text, correct 05 -> 01 ranking, and no platform watermark, URL, local path, or prompt leakage.
