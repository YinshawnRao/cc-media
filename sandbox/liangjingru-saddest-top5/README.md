# 梁静茹最苦的5首歌（liangjingru-saddest-top5）

竖屏 1080×1920 倒数盘点（第5→第1），女声解说，约 4:58。成片：`renders/liangjingru-saddest-top5.mp4`（mux 后为准）。

## 榜单（倒数揭晓）
5. 会过去的 (2009) — 越平静越疼
4. 崇拜 (2007) — 卑微的仰望
3. 慢冷 (2010) — 后劲型的苦
2. 可惜不是你 (2006) — 遗憾系天花板
1. 会呼吸的痛 (2007) — 想念是会呼吸的痛

## 复现
```bash
# 1) 选源 + 切片 + 竖屏化（见 SOURCES.md 的 bvid/crop）
bash build/clips.sh                       # raw/seg_*.mp4 -> clips/vert_*.mp4
# 2) 女声旁白
tools/tts/venv/bin/python build/narrate_segments.py
# 3) 音轨 master.wav + index.html
tools/tts/venv/bin/python build/full_build.py
# 4) 渲染（HF 会压平音频，必须后期 mux）
bash build/render.sh                       # renders/full_raw.mp4 (--sdr, 带重试)
ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a \
  -c:v copy -c:a aac -b:a 192k -shortest renders/liangjingru-saddest-top5.mp4
```

## 关键决策
- **官方 MV 全是剧情片（无本人演唱镜头）→ 展示段一律用本人现场**；详见 `SOURCES.md`。
- 《会过去的》无干净独立现场，用户拍板用墨尔本街头 busking（露脸，保证五首都见本人）。
- 封面用《崇拜》白西装情绪特写（真人、居中、暗底裁切安全），开头不剧透排名。

## 归档
保留可复现输入：`build/`、`SOURCES.md`、`design.md`、`narration.json`。`raw/`、`clips/`、`renders/`、`*.wav`、`frames/`、`qa/` 为产物，按需清理。
