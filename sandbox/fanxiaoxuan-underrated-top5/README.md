# 范晓萱最被低估的5首歌（fanxiaoxuan-underrated-top5）

竖屏 1080×1920 音乐盘点，倒数 05→01（#1=《看不见》压轴），男声旁白 `zm_yunxi`，约 5:00。

## 选题与口径
- 主题：范晓萱不只是"小魔女"可爱偶像，而是华语最敢自我推翻、亲手写歌的创作者；盘她转型后被光环盖住的 5 首遗珠。
- 倒数：05 失控的胖子 → 04 因为 → 03 You Don't Trust Me At All → 02 都是你 → 01 看不见。
- 事实口径与选源现实见 `SOURCES.md`（三张专辑全为个人专辑非&100%乐团；她作曲 4/5；都是你=陈韦伶不署她；5 首几乎无棚版 MV → 全解耦）。

## 复现
```bash
# 1) 旁白（Kokoro zm_yunxi）
tools/tts/venv/bin/python build/narrate_segments.py
# 2) 人声段（解耦：对录音室音轨 raw/p?_aud.wav 跑，remap 成 vert_ key）→ probe/vocal_analysis.json
# 3) footage 已 letterbox 到 clips/vert_*.mp4（pre-cut + tools/video/vfill.sh）
# 4) build：master.wav + footage_track + index.html（内置 showcase_align 闸门，5/5 OK 才出 master）
python3 build/full_build.py
# 5) 渲染 + mux（HF 压平动态，必须后期 mux master.wav）
bash build/render.sh            # npx hyperframes@0.6.69 render --sdr -w2，含重试
ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/fanxiaoxuan-underrated-top5.mp4
```

## 关键参数
- 对齐（源时间码 ch_off / show）：p5 29.45/33.0 · p4 46.77/28.4 · p3 152.45/31.0 · p2 200.0/32.0 · p1 196.12/24.9。
- 音乐床：intro=看不见前奏(seek 3)、outro=看不见副歌(seek 196)；mgain p4=1.18 p2/p1=1.06 其余 1.0。
- 成片以 mux 后 `renders/fanxiaoxuan-underrated-top5.mp4` 为准。

## 产物
- `renders/fanxiaoxuan-underrated-top5.mp4` — 最终成片（mux 后）。
- `raw/` `renders/` 已 gitignore；保留 `build/` `SOURCES.md` `narration.json` `probe/showcase_plan.json` 可复现。
