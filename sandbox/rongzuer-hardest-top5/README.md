# 容祖儿最难的5首歌 (rongzuer-hardest-top5)

竖屏 1080×1920 声乐难度盘点，倒数 5→1，女声旁白 (`zf_xiaoyi`)。容祖儿广东歌天后，主题=情绪克制系难歌。

## 排名（片头不揭晓，片尾总结）
1. 破相 — 锋利又体面的崩与收（陈辉阳曲/黄伟文词）
2. 心淡 — 连续推进，整首都要稳
3. 搜神记 — 密集咬字里的稳（林夕词/Christopher Chak曲）
4. 16号爱人 — 不甘，但不能怨
5. 痛爱 — 克制，比痛更难

## 复现
```bash
# 1. 旁白（女声 zf_xiaoyi）
tools/tts/venv/bin/python build/narrate_segments.py     # → audio/*.wav + narration.json
# 2. 素材：见 SOURCES.md 下载 raw/，裁窗 64s → raw/cut_*.mp4，vfill → clips/vert_*.mp4
#    （痛爱/16号 B站 Live，搜神记/心淡/破相 官方MV；crop 见 SOURCES.md）
# 3. 音频+合成
tools/tts/venv/bin/python build/full_build.py           # → master.wav + index.html
# 4. 渲染 + mux（必加 --sdr；HyperFrames 会压平音频动态，必须后期 mux master.wav）
npx hyperframes@0.6.47 render --output renders/full_raw.mp4 --sdr
ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/rongzuer-hardest-top5.mp4
```

## 关键参数 (build/full_build.py)
- SHOW=38s（每首连续副歌展示），LEAD/DIG/BED 同模板。
- MGAIN={"p2_xindan":1.4}（心淡 MV 副歌偏低补偿）。
- INTRO_CLIP=vert_p5_tongai，OUTRO_CLIP=vert_p1_poxiang。
- 固定结尾 CTA 由 tools/video/outro_cta.py 注入（全片最后一句，硬约束）。

成片以 mux 后的 `renders/rongzuer-hardest-top5.mp4` 为准。
