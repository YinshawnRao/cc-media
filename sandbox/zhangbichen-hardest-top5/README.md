# 张碧晨最难的5首歌

竖屏 1080×1920 难度盘点，倒数揭晓 #5→#1。男声 zm_yunxi，固定 CTA 结尾。

## 排名（倒数揭晓顺序）
5. 开往早晨的午夜 — 深夜质感、气息控制
4. 凉凉（与杨宗纬）— 古风合唱分寸、清冷感
3. 笼（《消失的她》）— 情绪密度、窒息压迫感
2. 年轮（《花千骨》）— 长线条、情绪递进与克制
1. 光的方向（《长歌行》）— 大歌气势、高位稳定穿透

## 选源
见 `SOURCES.md`。要点：官方MV全是剧集/电影画面无本人 → 4首用她官方Live、《笼》用电影MV(贴题)。全部耦合(画面+音频同源)。

## 复现
```bash
bash build/clips.sh                      # 精切+vfill 竖屏化（耦合）
tools/tts/venv/bin/python build/narrate_segments.py   # 旁白 TTS
tools/tts/venv/bin/python build/full_build.py         # 对齐闸门→master.wav+index.html
npx hyperframes@0.6.69 render --output renders/full_raw.mp4 --sdr -w 2
ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k renders/zhangbichen-hardest-top5.mp4
```

成片以 mux 后 `renders/zhangbichen-hardest-top5.mp4` 为准（HF 会压平音频动态，必须后期 mux master.wav）。

## 产物归档
`raw/`、`clips/`、`clips_seg/`、`renders/`、`*.wav` 已 gitignore（可由 build 复现）。保留：`build/`、`*.md`、`probe/*.json`。
