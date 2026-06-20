# 蔡健雅最被低估的5首歌（倒数盘点 · 女声）

竖屏 1080×1920 音乐遗珠盘点，倒数揭晓 5→1，女声旁白 `zf_xiaoyi`。约 4:47。

## 排名（倒数揭晓 5→1）
| 名次 | 歌 | 专辑 / 年 | 画面来源 | 模式 |
|---|---|---|---|---|
| 5 | 遗书 | 我要给世界最悠长的湿吻 · 2018 | 官方 MV `HyPkStVuLXU` | 歌画同源 |
| 4 | 失乐园 | 陌生人 · 2003 | 《出走》MV 特写 + 录音室音频 | 解耦 |
| 3 | 优先权 | 双栖动物 · 2005 | 《让浪漫做主》Live 2022 + 录音室音频 | 解耦 |
| 2 | 谁 | 若你碰到他 · 2009 | 《谁》Legacy Live 2022 | 歌画同源 |
| 1 | 多米诺 | 说到爱 · 2011 | 同专辑《说到爱》MV 特写 + 录音室音频 | 解耦 |

选源全过程与坑见 `SOURCES.md`。

## 复现
```bash
# 1) 旁白（女声）
tools/tts/venv/bin/python build/narrate_segments.py
# 2) 切片+竖屏化 footage + 抽各曲音频窗（读 build/song_config.py）
tools/tts/venv/bin/python build/prep_footage.py
# 3) 合成 master.wav + HyperFrames index.html（含 leak-guard）
tools/tts/venv/bin/python build/full_build.py
# 3b) 仅重建音轨（已调好的逐首响度）
tools/tts/venv/bin/python build/build_audio.py
# 4) 渲染（画面，silent 占位音轨）+ 后期 mux 真 master.wav
cd hf && ./render_retry.sh renders/full_raw.mp4 284
ffmpeg -i renders/full_raw.mp4 -i ../master.wav -map 0:v -map 1:a \
  -c:v copy -c:a aac -b:a 192k -shortest renders/caijianya-underrated-top5.mp4
```

## 关键文件
- `build/song_config.py` — 单一配置源（每首：模式/展示窗/副歌入点/裁切/蒙太奇切点）。
- `build/full_build.py` — 音轨段 + HTML/JS（封面→揭晓卡→展示→outro→固定CTA）。
- `build/prep_footage.py` — footage letterbox/中心裁切 + 音频窗抽取。
- `raw/` 源素材、`clips/show_*.mp4` 竖屏展示片、`audio_src/*.wav` 各曲音频窗。
- `qa/showcase/sc_*.mp3` — 各首展示副歌耳审样（尤其 #4 摇滚曲）。

## 设计/混音要点
- 结构：封面(真人脸)→intro→5×(暗底揭晓卡+旁白 → 音乐 swell + 特写画面 reveal 展示副歌)→outro 总榜升华→**固定引流 CTA（全片最后一句，硬约束）**。
- 5 段展示副歌统一 −15.0~−15.2 dB；旁白段 duck ~−21 dB；全片无 >1s 静音。
- HyperFrames 渲染压平动态 → 成片以**后期 mux master.wav** 的 `renders/caijianya-underrated-top5.mp4` 为准。
- 16:9 源 letterbox 保原比例（不裁人）；优先权单主体居中场用中心裁切放大并去 UP 水印。
