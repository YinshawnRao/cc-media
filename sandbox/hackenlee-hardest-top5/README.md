# 李克勤最难的5首歌

Vertical HyperFrames ranking video for the brief: countdown from fifth place to first place, with female narration and continuous song showcases.

## Ranking

| Rank | Song | Main difficulty |
| --- | --- | --- |
| 5 | 高妹 | Light rhythm, dense Cantonese diction, relaxed timing |
| 4 | 飞花 | High-position chorus, soft breath, clean tail control |
| 3 | 月半小夜曲 | Long phrasing, weak voice, pitch and violin-like line |
| 2 | 大会堂演奏厅 | Dense lyrics, repeated words, elegant but fast delivery |
| 1 | 我不会唱歌 | Liszt-inspired piano movement, rhythm precision, high placement |

## Workflow

1. Search and record YouTube + B站 candidates in `SOURCES.md`.
2. Download selected sources into `raw/`.
3. Convert selected 60s windows to vertical clips in `clips/`.
4. Generate narration:
   ```bash
   tools/tts/venv/bin/python sandbox/hackenlee-hardest-top5/build/narrate_segments.py
   ```
5. Build `master.wav` and `index.html`:
   ```bash
   tools/tts/venv/bin/python sandbox/hackenlee-hardest-top5/build/full_build.py
   ```
6. Render and mux:
   ```bash
   cd sandbox/hackenlee-hardest-top5
   npx hyperframes lint
   npx hyperframes render --output renders/full_raw.mp4 --sdr
   ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/hackenlee-hardest-top5.mp4
   ```

Final QA must include visual contact sheets and audio `silencedetect`/`volumedetect`; do not treat the render as final until muxed with `master.wav`.
