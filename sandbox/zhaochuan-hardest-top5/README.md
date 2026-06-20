# 赵传最难的5首歌（倒数盘点）

竖屏 1080×1920 声乐难度盘点，倒数 5 → 1，全程女声解说（`zf_xiaoyi`）。约 4:56。

## 榜单
5. 我很丑可是我很温柔 → 4. 红高粱 → 3. 爱要怎么说出口 → 2. 给所有知道我名字的人 → 1. 我是一只小小鸟

## 结构
封面(标题+难度标签) → 逐首：女声解说（音乐床）→ 消化位/swell → 连续副歌展示 28s（letterbox，口型同源同窗）→ 作品 outro（榜单回顾+主题升华）→ 固定引流 CTA（全片最后一句，逐字照念）。

## 复现
```bash
# 1) 配音（女声）
../../tools/tts/venv/bin/python build/narrate_segments.py
# 2) 素材：见 SOURCES.md（YT cookie + tools/video/bili_dl.py），切窗→vfill 全宽 letterbox→clips/vert_*.mp4
# 3) 建 master.wav + index.html
../../tools/tts/venv/bin/python build/full_build.py
# 4) 渲染（silent 占位音轨避免长片内联超时，-w1+重试规避 GPU 随机崩）
cp index.html index_full_bak.html; cp index_render.html index.html
npx hyperframes render --output renders/full_raw.mp4 --sdr -w 1 --protocol-timeout 600000
# 5) 后期 mux 真音频（HF 会压平动态，必须覆盖音轨）
ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/zhaochuan-hardest-top5.mp4
cp index_full_bak.html index.html   # 还原 canonical（master.wav 引用）
```

成片：`renders/zhaochuan-hardest-top5.mp4`。选源与坑见 `SOURCES.md`。
