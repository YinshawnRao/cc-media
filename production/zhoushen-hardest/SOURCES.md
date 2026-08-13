# 周深最难的5首歌 — 成片归档与复现说明

**成片**：`zhoushen-hardest.mp4`（竖屏 1080×1920，约 2:46，h264+aac）
**形式**：难度盘点，倒数 5→1（最难压轴）。极光天籁配色（冰青→紫→金），男声旁白 `zm_yunxi`。
## 揭晓顺序与素材来源

切片：`yt-dlp <URL> --cookies <ck> --download-sections "*<起>-<止>" -f "bv*[height<=1080]+ba/b"`
竖屏：`tools/video/vfill.sh <in> clips/<out>.mp4 <crop>`（裁台标/烧字 + 模糊填充）
展示段取该首副歌/高潮的**周深特写**，把片段结尾 trim 到特写帧（展示=片段末 ~6s）。

| # | 歌 | 来源（YouTube id / 版本） | 取用段(原片) | vfill crop | 备注 |
|---|----|--------------------------|-------------|-----------|------|
| 片头/片尾底 | — | `qSp6fl3BLm4`《少管我》2024微博音乐盛典纯享版 | 00:00–00:30 暗调开场 | 864:930:528:0 | `vert_intro`，片尾复用做开合呼应 |
| 05 | 孤独的牧羊人 | `iRpre_VU1wM` 声入人心首席版 | 01:30–02:30 | 864:1000:528:0 | 暗调/紫调，特写多 |
| 04 | 达拉崩吧 | `XHedu3KcPP0` 歌手·当打之年 纯享 | 01:50–02:55 | 864:960:528:0 | 蓝亮装，能量感 |
| 03 | 人是_ | `QCoyJgYZvwA` 时光音乐会2 首秀 | 02:30–03:35 | **864:820:528:0** | 时光烧字在 y≈840–920，此 crop 裁净 |
| 02 | 光亮 | `wNrQi_dzNLw` 官方《紫禁城》纯享 MV | 03:10–04:10 | 864:860:528:0 | 换官方MV避开时光中部烧字；周深红衣+紫禁城 |
| 01 | 少管我 | `qSp6fl3BLm4` 2024微博音乐盛典纯享版 | 03:06–03:35 | 864:930:528:0 | 压轴，金色「公认天花板」角标 |

- **片尾低床音乐**：`outro_music.wav` 取自 `eRXgdmB3tNM`（时光音乐会2《光亮》纯享）00:00–00:17.5，仅作旁白下的低音量器乐床（画面是 `vert_intro` 暗调底，无需对口型）。
- 旁白逐字稿见 `build/narration.json`。

## 复现步骤

1. 重下源切片（上表 URL+时间码，需有效 cookie）。
2. 配音：`tools/tts/venv/bin/python build/narrate_segments.py`（男声 zm_yunxi）→ `audio/*.wav`。
   - 已归档 `audio/`，可跳过。
3. 竖屏化：按上表 crop 跑 `vfill.sh`，得 `clips/vert_*.mp4`。已归档。
   - **坑**：《少管我》《光亮》源是 webm，从 `-ss 0` 切会丢尾部音频→展示段音乐断。修法：先整段转 mp4，或输出端 seek 抽 wav（`shao_music.wav`/`guang_music.wav` 即此法产物，已归档）。详见 CONVENTIONS「老素材实战补充」。
4. 合成 + 音频：在一个 `npx hyperframes init` 项目里放 `clips/`、`audio/`，跑 `build/full_build.py` → 生成 `index.html` + `master.wav`。
5. 渲染 + mux（HyperFrames 会压平音频动态，必须后期 mux）：
   ```
   npx hyperframes render --output full_raw.mp4
   ffmpeg -i full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest zhoushen-hardest.mp4
   ```
   - `master.wav`（终版预混）已归档，可直接 mux。

## QA 基线（成片已达标）

- 五首副歌均值 −14.7~−15.9dB（差<1.2dB）；旁白段 ~−24dB（ducking）；无 >1s 静音。
- 画面无水印/网址/烧死歌词/路径；倒数 5→1，#1 金色「公认天花板」角标。
