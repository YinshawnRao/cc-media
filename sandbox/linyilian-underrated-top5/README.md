# 林忆莲最被低估的5首歌

竖屏 1080×1920 解说盘点（倒数 5→1），女声旁白（`zf_xiaoyi`），总时长约 5:08。

## 揭晓顺序（倒数 5→1）

| 名次 | 歌曲 | 专辑 / 年份 | 角度 |
|---|---|---|---|
| 5 | 太阳系 | 《0》/ 2018 | 空灵电子里的疏离，被《沙文》《纤维》盖过的隐藏款 |
| 4 | 理由 | 《铿锵玫瑰》/ 2002 | 被同名主打压住的冷静派台遗珠 |
| 3 | 我坐在这里 | 《林忆莲's》/ 2000 | 很冷的都市孤独，克制的疏离 |
| 2 | 飞的理由 | 《人间四月天》主题曲 / 2000 | 安静的告别与重新出发 |
| 1 | 没有发生的爱情 | 《野花》/ 1991 | 概念专辑遗珠，对应昙花，"还没开始就已错过" |

- 片头：封面 + 作品描述（**不暴露排名**，留悬念）。
- 片尾：揭晓完整 5→1 榜单 + 主题升华，最后固定引流 CTA（女声）。

## 复现

```bash
# 1) 配音（Kokoro zf_xiaoyi）
tools/tts/venv/bin/python build/narrate_segments.py
# 2) 选源 + 切片 + 竖屏化  → clips/vert_*.mp4（见 SOURCES.md 的窗口与 crop）
# 3) 音轨 + 合成
python3 build/full_build.py            # → master.wav + index.html
npx hyperframes lint                   # 0 error
# 4) 渲染 + mux（HyperFrames 会压平音频动态，必须后期 mux master.wav）
npx hyperframes render --output renders/full_raw.mp4 --sdr -w1
ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/linyilian-underrated-top5.mp4
```

## 选源要点（详见 SOURCES.md）

都是深 cut，多数没有"歌手本人 + 干净 HD MV"，用了披露过的救场：
- **太阳系** = 官方艺术 MV（双重曝光 + 银河环，"空灵/宇宙感"完美对题；唯一全干净源；回响 4K live 都带 UP/平台水印被弃）。轻提对比度。
- **理由** = **同专辑《铿锵玫瑰》MV 的本人金光特写 + 《理由》本曲音频解耦**（理由官方 MV 是无本人剧情片；伍佰式同专辑救场）。
- **我坐在这里** = B站「原版4K修复」(1080p 演唱会，裁底部卡拉OK 歌词)。
- **飞的理由** = B站「飞的理由 1080p修复」(卡拉OK MV，裁底部歌词)。
- **没有发生的爱情** = SANDY IN CONCERT 2002 1080p（野花无真 MV，官方上传是专辑封面静图）；选 1:46–2:38 的无台标特写段。

## 产物

- `renders/linyilian-underrated-top5.mp4` — 最终成片（mux 后）。
- `master.wav` — 预混音轨（逐首 loudnorm -14，副歌均落 ~-15dB，旁白段 ~-20.5dB）。
- `clips/vert_*.mp4` — 竖屏 letterbox 片段。`raw/` 下载窗口可丢弃。
