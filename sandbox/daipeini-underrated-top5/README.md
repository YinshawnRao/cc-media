# daipeini-underrated-top5 — 戴佩妮最被低估的5首歌

竖屏 1080×1920 倒数盘点（5→1），女声旁白（zf_xiaoyi），~4:01。
固定结尾引流 CTA 逐字照念（全片最后一句）。

## 榜单（倒数揭晓）
- 05 《非诚勿扰》（贼·2016）
- 04 《转眼》（No Penn, No Gain·2003）
- 03 《你怎么可以安心的睡着》（纯属意外·2013）
- 02 《钢琴键》（贼·2016）
- 01 《水中央》（No Penn, No Gain·2003）

## 重建步骤
```bash
# 1. 旁白（女声）
tools/tts/venv/bin/python build/narrate_segments.py
# 2. 切片（特写/letterbox；选源/crop 见 SOURCES.md）
bash build/make_verts.sh
# 3. 录音室音频抽轨 + 人声段（已生成于 raw/*_studio.wav / *.vocal.json）
#    tools/tts/venv/bin/python tools/video/vocal_segments.py raw/*_studio.wav
# 4. master.wav + index.html
tools/tts/venv/bin/python build/full_build.py
# 5. 渲染（-w1 重试，--sdr）+ 后期 mux 预混 master
bash build/render_full.sh
ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/daipeini-underrated-top5.mp4
```

成片以 mux 后的 `renders/daipeini-underrated-top5.mp4` 为准。选源/坑/QA 见 `SOURCES.md`。
