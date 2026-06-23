# 张雨生最被低估的5首歌（竖屏盘点 1080×1920，倒数 05→01）

榜单（用户给定，倒数揭晓）：05 永远的自由 → 04 妹妹晚安 → 03 我是风筝 → 02 渺小 → **01 河**。
男声 `zm_yunxi`，暗蓝 + 宋体基调，约 4:55。

## 关键做法（与常规盘点不同）

这 5 首**都没有真人演出 MV**（官方版本全是歌词视频/Comix 动画/静图音轨）。所以采用**解耦**：
- **音频** = 每首本曲干净录音室录音；
- **画面** = 张雨生本人**同期官方 MV** 的真实演出/特写镜头（letterbox 保原比例），跨 5 支 MV 分散年代/造型。

选源细节、双平台核查、年份修正、水印/标题卡规避见 `SOURCES.md`。

## 复现

```bash
# 1) 配音（改 build/narrate_segments.py 的 BLOCKS 文案后）
tools/tts/venv/bin/python build/narrate_segments.py
# 2) 人声段检测（定位每首展示段副歌入点，已写入 raw/*_aud.vocal.json）
tools/tts/venv/bin/python ../../tools/video/vocal_segments.py raw/p?_aud.wav
# 3) 建 master.wav + index.html（解耦：footage 取 clips/vert_*.mp4，music 取 raw/*_aud.wav 切片）
python3 build/full_build.py            # SAMPLE=1 只出 intro+#5；HTML_ONLY=1 跳过音频重建
# 4) 渲染 + 后期 mux（HF 会压平动态，必须用 master.wav 覆盖音轨）
npx hyperframes lint
npx --yes hyperframes@0.6.69 render --output renders/full_raw.mp4 --sdr -w2
ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/zhangyusheng-underrated-top5.mp4
```

## 结构

每首：转场旁白（音乐床 duck）→ 消化位/swell → **展示段副歌**（音乐全量，**收在唱完整一句之后**才转场）。
片尾：作品 outro（榜单回顾 + 主题升华）→ 固定引流 CTA（`tools/video/outro_cta.py`，全片最后一句）。

成片以 mux 后的 `renders/zhangyusheng-underrated-top5.mp4` 为准。
