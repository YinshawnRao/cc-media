# 李健最被低估的5首歌

Vertical ranking video for the brief: "李健最被低估的5首歌".

Final MP4:

- `renders/lijian-underrated-top5.mp4`

## Structure

- `raw/` - downloaded source videos
- `clips/` - cleaned 9:16 vertical source clips
- `audio/` - generated narration WAVs
- `clips_seg/` - final timed video segments used by HyperFrames
- `master.wav` - post-mix audio master
- `index.html` - HyperFrames composition
- `renders/full_raw.mp4` - HyperFrames render before final audio replacement
- `renders/lijian-underrated-top5.mp4` - final muxed delivery

## Rebuild

From this directory:

```bash
python3 build/narrate_segments.py
python3 build/full_build.py
npx --yes hyperframes lint
npx --yes hyperframes render --output renders/full_raw.mp4 --sdr
ffmpeg -y -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/lijian-underrated-top5.mp4
```

`npx --yes hyperframes inspect` timed out on this long composition in this run, so validation was done through lint, render, artifact metadata, audio scans, and contact-sheet review.

## QA results from this run

- HyperFrames lint: 0 errors, 3 `timeline_track_too_dense` warnings.
- Showcase alignment: `OK=5/5`, `FAIL=0`, `WARN=0`.
- Final file: H.264, 1080x1920, 30 fps, AAC stereo, 324.683 s, 191,050,240 bytes.
- Audio post-muxed from `master.wav`.
- Silence scan: no `silencedetect` events at `-35dB` for `d=1`.
- Volume scan: mean `-16.8 dB`, max `-0.5 dB`.
- Visual contact sheet: `qa/final_contact_sheet.jpg`.
