# 陈慧琳最难的5首歌（倒数盘点）

竖屏 1080×1920 音乐难度盘点，女声解说，倒数揭晓 第5 → 第1，片尾列榜单 + 固定引流 CTA。
成品：`renders/chenhuilin-hardest-top5.mp4`（mux 后为准）。

## 排名（难度，第1最难）
1. 《花花宇宙》— 舞曲女王代名词；电音快节奏里气息·律动·状态全程顶住
2. 《失忆周末》— 节奏密、咬字碎、气口窄，还要边唱边跳（肺活量考核）
3. 《不如跳舞》— 林夕词·雷颂德曲；轻准稳的松弛感最难拿捏
4. 《大日子》— 喜庆快歌，气息一直推、不能靠喊
5. 《谁愿放手》— 慢歌控制：长线条、粤语尾音、真假声边缘

揭晓顺序（片中）：5 → 4 → 3 → 2 → 1。开头不剧透排名。

## 流程
1. `build/narrate_segments.py` — 女声旁白（`zf_xiaoyi`），intro/5首/outro + 固定 CTA（从 `tools/video/outro_cta.py` 导入）。→ `audio/*.wav` + `narration.json`
2. `build/clips.sh` — 按「副歌窗起 − preroll(voice_dur+2.1s)」切片 → `vfill.sh` 竖屏化（letterbox + 裁烧词/水印）→ `clips/vert_*.mp4`
3. `build/full_build.py` — 逐段 床→swell→副歌 建 `master.wav`（每首 loudnorm I=-14 统一响度），生成 `index.html`
4. `build/render.sh` — `npx hyperframes render --sdr`（带重试循环，防 GPU 截帧偶崩）→ `renders/full_raw.mp4`
5. mux：`ffmpeg -i full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac ... renders/chenhuilin-hardest-top5.mp4`

## 选源
见 `SOURCES.md`。要点：官方频道《失忆周末》《不如跳舞》是静态专辑图（弃用，改 637 TWS / B站樱花动态 MV）；B站时光音乐阁 4K 修复带间歇水印（弃用，花花宇宙改 weazegigi 无水印 1080P）。千禧舞曲官方干净源多为 SD，干净度优先于分辨率。

## QA
- 画面：抽帧确认各段对应素材、Kelly 在场不被裁、无烧词/水印/网址/路径/排名提前泄漏。
- 音频：5 首副歌响度一致（实测 -16.7~-17.0 dB）、无 >1s 整片静音、旁白段音乐床 ducking。
- 时长：mux 后 ≈ master 时长（~340s）。
