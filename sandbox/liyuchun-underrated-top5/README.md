# 李宇春最被低估的5首歌

竖屏盘点视频，按用户给定排名倒序揭晓：

1. 第 5 名：《小宇宙》
2. 第 4 名：《冷暖》
3. 第 3 名：《似火年华》
4. 第 2 名：《一而再再而三地喜欢你》
5. 第 1 名：《西门少年》

## 文件结构

- `raw/`：YouTube / B站下载候选素材。
- `clips/`：`tools/video/vfill.sh` 生成的 1080x1920 竖屏素材。
- `audio/`：Kokoro 中文旁白。
- `clips_seg/`：`build/full_build.py` 生成的分段视频。
- `probe/`：人声检测与展示段对齐计划。
- `qa/`：抽帧、音频检测输出。
- `renders/`：渲染与最终成片。

## 复现步骤

```bash
tools/tts/venv/bin/python sandbox/liyuchun-underrated-top5/build/narrate_segments.py
tools/tts/venv/bin/python sandbox/liyuchun-underrated-top5/build/full_build.py
cd sandbox/liyuchun-underrated-top5
npx hyperframes lint
npx hyperframes inspect
npx hyperframes render --output renders/full_raw.mp4 --sdr
ffmpeg -y -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/liyuchun-underrated-top5.mp4
```

最终发布前必须重新做抽帧和 `volumedetect` / `silencedetect` QA。
