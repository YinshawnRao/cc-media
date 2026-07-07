# 凤凰传奇最被低估的5首歌

竖屏 1080×1920 音乐遗珠盘点，倒数 05→01，男声 `zm_yunxi`，约 4:48。

倒数榜单：05 中国味道 · 04 天籁传奇 · 03 康定情缘 · 02 传奇 · 01 大漠情人。

凤凰传奇 = 玲花 + 曾毅 **二人组合** → footage 全 letterbox 保原比例，禁竖裁放大。

## 复现

```bash
# 1) 旁白（男声 zm_yunxi）
../../tools/tts/venv/bin/python build/narrate_segments.py
# 2) footage 竖屏 letterbox（各首 crop 见 build/clips.sh / SOURCES.md）
bash build/clips.sh        # 注：symphony/天籁/大漠的最终 crop 见对话记录，clips.sh 为初版
# 3) 人声段（供对齐闸门）已在 probe/vocal_src.json → vocal_analysis.json
# 4) 音轨 + HTML + 对齐闸门（违规不出 master）
../../tools/tts/venv/bin/python build/full_build.py
# 5) 渲染 + mux（HF 压平动态 → 必须后期 mux master.wav）
npx --yes hyperframes@0.6.69 render --output renders/full_raw.mp4 --sdr -w 2
ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest \
  renders/fenghuangchuanqi-underrated-top5.mp4
```

## 关键点

- **全 DECOUPLED**：footage = 静音 b-roll，音轨取干净录音室版（详见 `SOURCES.md`）。《传奇》全网无 MV/Live，音轨从无损专辑合集 p11 抽。
- **封面 = #5 中国味道动态画面**（4K交响 玲花+曾毅同台 @源48s），intro 与 #5 同源连续窗，cover→#5 无剪。
- **对齐闸门 5/5 OK**：副歌入点对齐旁白收尾前 2s，结尾落器乐 gap。
- **固定结尾 CTA** 永远是最后一句（作品 outro 之后），不含投票问句。
- 单 `footage_track.mp4`（避免 HF 多 `<video>` 帧0 协议超时）。
- 成片以 mux 后 `renders/fenghuangchuanqi-underrated-top5.mp4` 为准。
