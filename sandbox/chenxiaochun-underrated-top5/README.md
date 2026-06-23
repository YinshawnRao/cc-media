# 陈小春最被低估的5首歌

1080×1920 竖屏倒数盘点（05→01），男声旁白 `zm_yunxi`，总长约 4:53。开头 / 每首转场 / 结尾均有配音，结尾固定引流 CTA。

## 排名（倒数揭晓）

| 名次 | 歌曲 | 专辑 · 年份 | 源 | 展示段(源 s) |
| --- | --- | --- | --- | --- |
| 05 | 不在服务区 | 独家记忆 · 2008 | B站车内剧情 MV 1080P | 105–131 |
| 04 | 风流 | Sing 十年纪念 · 2006 | YT JordanChanVEVO 官方 MV | 177–208 |
| 03 | 哑忍 | Sing 十年纪念 · 2006 | YT JordanChanVEVO 官方 MV | 180–213 |
| 02 | 下半辈子 | That's Mine · 2002 | YT JordanChanVEVO 官方 MV | 183–209 |
| 01 | 献世 | 夜生活 · 2004 | B站樱花 DVD 官方棚版 MV 1080P | 183.5–216.5 |

主题：陈小春不只是又凶又痞的"山鸡哥"，他的情歌里藏着江湖男人很少示人的卑微、脆弱与深情。

## 关键文件

- `SOURCES.md`：双平台候选、取舍、crop、展示段、专辑年份核对。
- `build/narrate_segments.py`：男声旁白（`zm_yunxi`）；固定 CTA 由 `tools/video/outro_cta.py` 导入。
- `build/full_build.py`：生成 `master.wav` + `clips_seg/*` + `index.html`。
- `clips/vert_*.mp4`：5 首竖屏 letterbox footage。
- `probe/*`：抽帧与人声检测（`vocal_analysis.json` 等）。

## 重建

```bash
../../tools/tts/venv/bin/python build/narrate_segments.py
python3 build/full_build.py
npx hyperframes lint
npx hyperframes render --output renders/full_raw.mp4 --sdr
ffmpeg -v error -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a \
  -c:v copy -c:a aac -b:a 192k -shortest renders/chenxiaochun-underrated-top5.mp4 -y
```

成片以 mux 后的 `renders/chenxiaochun-underrated-top5.mp4` 为准（HyperFrames 会压平音频动态，必须用 `master.wav` 后期 mux）。
