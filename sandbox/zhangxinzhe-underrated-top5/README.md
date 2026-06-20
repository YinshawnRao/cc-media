# zhangxinzhe-underrated-top5

主题：《张信哲最被低估的5首歌》。

结构：竖屏 1080×1920，倒数 5→1，女性配音 `zf_xiaoyi`，每首先讲述再进入连续歌曲展示段。最终固定 CTA 来自 `tools/video/outro_cta.py`。

## 生成流程

```bash
cd /Users/yinshawnrao/explorer/cc-media/sandbox/zhangxinzhe-underrated-top5
../../tools/tts/venv/bin/python build/narrate_segments.py
python3 build/full_build.py
npx --yes hyperframes@0.6.69 lint
npx --yes hyperframes@0.6.69 render --output renders/full_raw.mp4 --sdr
ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/zhangxinzhe-underrated-top5.mp4
```

成片以 mux 后的 `renders/zhangxinzhe-underrated-top5.mp4` 为准。

## 当前产物

- `renders/zhangxinzhe-underrated-top5.mp4` — 最终 mux 成片。
- `renders/full_raw.mp4` — HyperFrames 原始渲染，不作为交付音频。
- `master.wav` — 预混主音轨，最终成片已用它覆盖 raw 音频。
- `qa/contact.jpg` — 关键帧抽帧总览。
