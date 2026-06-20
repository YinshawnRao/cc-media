# 动力火车最难的5首歌（声乐难度盘点，倒数 5→1）

竖屏 1080×1920 短视频，女声旁白，倒数揭晓。片头只给封面+作品描述（不剧透排名），片尾列完整榜单。

## 排名（难度 1=最难）
1. 明天的明天的明天　2. 彩虹　3. 无情的情书　4. 背叛情歌　5. 除了爱你还能爱谁

## 复现
```bash
tools/tts/venv/bin/python build/narrate_segments.py   # 女声旁白 -> audio/
python3 build/clips.py                                 # 切+letterbox 展示 footage -> clips/
python3 build/full_build.py                            # master.wav + index.html
npx hyperframes render --output renders/full_raw.mp4 --sdr
ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/donglihuoche-hardest-top5.mp4
```

- `build/song_cfg.py` — 单一配置源（源/副歌窗/show/crop），clips.py 与 full_build.py 共用。
- 选源与 crop 见 `SOURCES.md`；设计见 `design.md`。
- 成片以 mux 后的 `renders/donglihuoche-hardest-top5.mp4` 为准（HyperFrames 会压平音频动态，必须后期 mux master.wav）。
- 双人组合 → footage 一律 letterbox，禁竖裁放大。
