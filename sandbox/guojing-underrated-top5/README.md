# 郭静最被低估的5首歌

竖屏 1080×1920 音乐盘点，倒数 05→01，男声旁白 `zm_yunxi`，约 5:11。

## 榜单（倒数揭晓）

| 名次 | 歌曲 | 专辑(年) | 词曲 |
| --- | --- | --- | --- |
| 05 | 下一个奇迹 | 陪着我的时候想着她 (2011) | 姚若龙 / 陈小霞 |
| 04 | 本来 | 陪着我的时候想着她 (2011) | 徐佳莹 |
| 03 | 一个人弹琴 | 我不想忘记你 (2007) | 刘淑莉 |
| 02 | 慢慢纪念 | 下一个天亮 (2008) | 林夕 / 易桀齐 |
| 01 | 不药而愈 | 下一个天亮 (2008) | 王雅君 |

## 复现

```bash
# 1) 配音（Kokoro 男声）
tools/tts/venv/bin/python build/narrate_segments.py
# 2) 录音室音频已在 raw/p{1..5}_aud.wav；人声段→ probe/vocal_analysis.json（已生成）
# 3) build：master.wav + footage_track + index.html（内置展示段对齐闸门）
tools/tts/venv/bin/python build/full_build.py
# 4) 渲染 + mux（HF 压平动态，必须后期 mux master.wav）
npx --yes hyperframes@0.6.69 render --output renders/full_raw.mp4 --sdr -w 2
ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/guojing-underrated-top5.mp4
```

`SAMPLE=1` 只出 intro+#5+outro 样片；`HTML_ONLY=1` 跳过音频重建只改 HTML。

## 选源 / 事实核实

见 `SOURCES.md`。要点：郭静抒情曲多无自有官方MV或为男主角情侣片 → 4 首解耦（录音室音轨 + 她其他**无男主**官方MV画面救场），仅《不药而愈》耦合（雨窗独唱同窗）。全部官方源，480p 老 MV 用户已确认可接受。

## 产物

- 成片：`renders/guojing-underrated-top5.mp4`（mux 后为准）
- 封面首帧可作缩略图（郭静《知道》MV 正脸特写）
- `renders/`、`raw/`、`*.wav`、`clips*/` 等已 gitignore
