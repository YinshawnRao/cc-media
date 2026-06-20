# linyoujia-underrated-top5 — 林宥嘉最被低估的5首歌

竖屏 1080×1920 倒数盘点（5→1），女声配音（zf_xiaoyi），约 4:00。

## 排名（片头不暴露，片尾揭晓）
5《飞》· 4《4号病房》· 3《拾荒》· 2《慢一点》· 1《耳朵》

## 结构
封面（标题+作品描述，无排名）→ 倒数 5→1（每首：女声解说 over 现场床 → 消化/swell → 副歌展示）→ 片尾揭晓完整榜单+主题升华 → 固定引流 CTA（全片最后一句）。

## 关键做法
- **混合音源**：慢一点 / 飞 = 现场 Live 音画同源（口型同步）；耳朵 / 拾荒 / 4号病房 = **本人特写蒙太奇救场**（录音室音频 + 解耦的本人特写），因这三首官方无演唱 MV / 无干净现场。详见 `SOURCES.md`。
- **音频后期 mux**：HyperFrames 只渲画面，预混 `master.wav` 覆盖音轨（HF 会压平动态）。
- 全部素材走 B站（本期 YouTube cookie 失效，见 SOURCES.md）。

## 复现
```bash
bash build/make_verts.sh          # raw/ 窗口 → 竖屏 letterbox clips/（delogo 水印 + crop 烧词）
tools/tts/venv/bin/python build/narrate_segments.py   # 女声 audio/*.wav
python3 build/full_build.py        # master.wav + index.html（含 vocal 副歌对齐 + ducking 包络）
bash build/render_full.sh          # -w1 + 重试渲染 → renders/full_raw.mp4（--sdr）
# mux:
ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/linyoujia-underrated-top5.mp4
```

## 成片
`renders/linyoujia-underrated-top5.mp4`（mux 后为准）。
