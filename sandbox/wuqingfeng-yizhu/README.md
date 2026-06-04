# 吴青峰 冷门遗珠 TOP5（竖屏 1080×1920，女声盘点）

倒数揭晓 #5→#1，文学/梦境基调，暗底 + 每首单一强调色。总时长 3:51。
成片：`renders/wuqingfeng-yizhu.mp4`（= `renders/full_raw.mp4` 渲染产物 + 预混 `master.wav` 后期 mux）。

## 排名与素材源（YT + B站都搜过，按清晰度/干净度/立体声选）

| # | 歌 | 选用源 | 平台 | 规格 | 展示段(raw) | 备注 |
|---|----|--------|------|------|------------|------|
| 05 | ……睡美人 | siC9KwMaVTw 官方MV | YouTube | 4K→1080 AV1 立体声 | 201–215s | 云朵/缝纫梦境MV，有他特写；底部烧字已裁 |
| 04 | 等 | BV1eu4y1q7Fo 4K Live MV | 哔哩哔哩 | 4K→1080 HEVC 立体声 | 149–163s | 无棚版MV，唯一可用现场；暖调乐队全景(多机位无长特写)，前景已提亮 |
| 03 | 译梦机 | pUW2Zwx1HNs 官方MV | YouTube | 1080 AVC 立体声 | 380–394s | 全CG梦境动画(镜像脸/拱门)；小字幕已裁 |
| 02 | 伤风 | DDiVLYGwemU 官方MV | YouTube | 2048×1152 VP9 立体声 | 256–270s | 黑色寓言(演员/废墟,非本人)；底部烧词已裁；前景轻提亮 |
| 01 | 线的记忆 | BV1cD4y1Z7aT 环球音乐(官方) | 哔哩哔哩 | 1080 AVC 立体声 321k | 203–216s | "线/光"艺术MV；穿针引线特写为压轴主图，已加对比度回拉(源偏过曝) |

- **封面真人头像**：从《……睡美人》官方MV 抓帧（约 188s 他的云中特写，干净正脸）。卫武营沙龙 Live(4K) 抽帧多为暗调乐队全景，无更优正脸；如需"现场"正脸或想换照片可替换 `raw/cover_face.png` 后重跑 `full_build.py`。
- 对照淘汰：译梦机/睡美人 4K私藏(B站,HEVC,UP水印风险)；伤风 B站HEVC(分辨率低于YT 2048)；等 仅有 Lyric Video(烧死歌词)无法当干净素材。

## 旁白
女声 `zf_xiaoyi`（用户指定），`build/narrate_segments.py`：intro + 5 首转场(按歌key) + outro。
无中段VO（展示段纯音乐）；无 meta 倒数旁注；无英文（Kokoro 不中英混读）。文案见 `narration.json`。

## 构建流水线（可复现）
1. `build/clips.sh` — 切展示段(输出端seek) + 前景调色 + `vfill.sh` 竖屏化(裁烧字/字幕/黑边) → `clips_seg/<key>.mp4` + `audio/<key>_music.wav`。
2. `build/narrate_segments.py`（venv python）→ `audio/<key>.wav` + `narration.json`。
3. `build/full_build.py` → `master.wav`（每首：raw[W−show0] 连续取做低床→swell→纯音乐展示，逐首 loudnorm I=−14；展示段口型与 footage 同步）+ `hf/index.html`（#5→#1 揭晓卡 + 每首主题色 + 真人封面）+ 拷贝资源到 `hf/`。
4. 渲染：`hf/` 内 `npx hyperframes render --sdr`，再 mux：
   ```
   ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/wuqingfeng-yizhu.mp4
   ```

## 渲染坑（本机已踩）
- HyperFrames 在本机 **GPU 截帧随机崩**（`browserGpuMode auto → hardware`，"GPU stall due to ReadPixels"），多 worker 与单 worker 都会随机在不同帧死、无 JS 报错。`--no-browser-gpu`(软件渲染) 在本机一启动截帧就崩，不可用。
- 对策：**单 worker `-w 1` 反复重试直到出完整片**（`build/retry_render.sh`，按产物时长≈231.7s 判完整）。成功率约 1/3。
- 总时长曾设 246s，>240s 时 HF 关 streaming-encode、缓冲全部帧→更易 OOM；压到 ~231s 后 `-w1` 启用 streaming。

## QA 结论
- 音频：展示段 −11.5~−13.4dB（5首一致），VO 段 ~−19dB（ducking 清晰），无 >1.2s 整片静音。
- 画面：封面真人正脸 + 金色标题；5 张揭晓大字号角标；各展示段对应素材、无水印/网址/烧死歌词残留；SDR(bt709)。
