# 张信哲最难的5首歌 — 成片归档与复现说明

**成片**：`renders/zhangxinzhe-hardest.mp4`（竖屏 1080×1920，约 5:09，h264 + aac 立体声）
**形式**：难度盘点，倒数 5→1（最难压轴）。情歌王子风：墨蓝底 + 香槟金 + 衬线歌名，**女声旁白 `zf_xiaoyi`**。
**封面**：张信哲蓝台正脸特写（信仰 CCTV 源帧）+ 标题"最难的5首歌"+ 作品描述，**不剧透排名**（按 brief）。片尾口播 + 画面**完整难度榜 01–05**。
**用途**：本地测试，未发布。发布前需另行评估 YouTube / B站源素材授权。

## 揭晓顺序与素材来源（双平台对照后选源；官方MV普遍带烧死卡拉OK歌词 → 全部改用更干净的 Live/直拍）

> ⚠️ 关键选源结论：张信哲千禧前后**官方MV几乎都是卡拉OK烧词版**（过火/太想爱你 YT+B站官方源均双行黄白烧词；信仰官方MV是儿童演员叙事+平台logo+底字幕）。
> 对"连续≥25s 本人唱副歌"的展示段硬规则不可用 → 全部改用**干净 Live / 4K修复演唱会 / 竖屏直拍**（live 也更能证明"难度"）。

| # | 歌 | 来源(B站/YT) | 档位 | 切窗(原片) | 竖屏处理 | 副歌(vert内偏移→展示) |
|---|----|------|------|-----------|---------|------|
| 封面/intro/outro 底 | 信仰 | B站 `BV1hGndz5EVb` 央视频(CCTV)音乐盛典 | 官方Live | intro底取 00:05–00:50 前奏段 | 居中4:3裁(1150:863:385:52) | — |
| 05 | 过火 | B站 `BV1TAreByE96` 福州2026.1.11拼盘演唱会近距离 | 竖屏直拍 | 00:40–02:10 | 裁顶105px去UP水印+等比满竖屏 | ch_off=38→SHOW 30s |
| 04 | 爱如潮水 | B站 `BV1iy4y117qo` 演唱会4K修复 | 官方Live(4K修复) | 00:50–02:35 | letterbox 全幅(干净) | ch_off=28→SHOW 31s；音量×0.85拉齐 |
| 03 | 太想爱你 | B站 `BV1S5411E7X7` 爱情蒲公英演唱会4K修复 | 官方Live(4K修复) | 01:10–02:50 | letterbox 全幅(干净) | ch_off=25→SHOW 36s |
| 02 | 宽容 | B站 `BV1vxGv6xEfe` 奥克兰未来式演唱会 | 官方Live | 01:20–02:40 | letterbox，裁底75px去 mike6liu 水印 | ch_off=43→SHOW 28s |
| 01 | 信仰 | B站 `BV1hGndz5EVb` 央视频(CCTV)音乐盛典 | 官方Live(CCTV) | 02:30前段(主源切 00:55–02:05) | 居中4:3裁(去顶央视logo/底字幕/右下赞助) | ch_off=32→SHOW 33s |

### 选源放弃记录（避免重走弯路）
- **过火/太想爱你 官方MV（YT `SrD36rogSjc` / `hG4-xzaDv40`，B站 4K修复同源）**：双行黄白卡拉OK烧词贯穿，裁不净（上行到画面中部）→ 弃，改 Live。
- **信仰**：官方MV(YT `QoPxzsqGodk`)=儿童演员叙事+平台logo+底字幕；梦响盛典 gala(`BV1QF43zKEH4`)=大量舞群/合唱团/**观众反应**切镜；4K修复(`BV1XTPEzNE9M`)=绿色"金典"赞助LED牌；自贡4K直拍(`BV1DpLm6oEq1`)=676低清+顶UP水印+底烧词+录制App水印。→ 最终选 **CCTV央视频**（1080p清晰、特写为主、仅角落logo/字幕可居中裁掉；多机位观众反应镜头对煽情压轴加分）。
- **宽容 Live'07(`BV14y4y1W7SN`)**：交响乐现场，大量乐队/全景空镜，无≥25s连续特写 → 改奥克兰(粉装连续紧特写)。
- **过火 沈阳直拍(`BV1Lf7X6sEGd`)**：竖屏1080×1920但含 fixed"MTN"+顶UP双水印 → 改福州近距离(仅顶UP水印，可裁)。

## 复现步骤
1. 下源切片：见上表 `yt-dlp <url> --cookies <ck> --download-sections "*<起>-<止>" -f "bv*[width<=1080]+ba/b"`（竖屏直拍按 width 选，否则 height>1080 会回退低清）。
2. 竖屏化：`bash build/process_clips.sh`（过火=裁顶delogo满竖屏；信仰=居中4:3裁；其余letterbox）。intro底另切 信仰CCTV 00:05–00:50 → vert_introbed。
3. 配音（女声 zf_xiaoyi）：`tools/tts/venv/bin/python build/narrate_segments.py` → `audio/*.wav`（旁白稿见脚本，已按 brief 润色，不含英文/音名）。
4. 合成：`python3 build/full_build.py`（建 clips_seg + master.wav + index.html；副歌时间码由 whisper small 转写定位，见 build 内 songs 表 ch_off）。
5. 渲染（本机GPU随机崩 + 总长>240s/≥7video 必崩 → 切两段）：`bash build/render_parts.sh`
   - `ZX_PART=A/B python3 build/full_build.py` 生成 partA(intro+#5+#4)/partB(#3+#2+#1+outro) → render --sdr -w1 重试 → concat → mux master.wav。

## QA 基线（成片已达标）
- 五首副歌 −15.1~−16.0dB（差 0.9dB）；无 >1s 整片静音；旁白段 ~−20dB（ducking 明显）。
- 画面无水印/网址/烧死歌词/平台logo/路径/meta 文案（逐源裁净 + 居中裁掉角落logo）；倒数 05→01，#1 金色「公认天花板」；片尾完整榜单 01–05。
- 每首连续副歌展示：过火30s / 爱如潮水31s / 太想爱你36s / 宽容28s / 信仰33s（均 ≥25s，footage窗==音乐窗保口型）。
- 女声旁白：intro / 每首转场 / outro 全为 zf_xiaoyi。

## 仍需人工耳/眼定夺
- 各首所选副歌段是否"最具代表性高光"（我按歌曲结构+whisper定位，未必是你心里的最佳段）。
- 太想爱你为多机位 Live，展示段含特写↔中景交替（源固有节奏，非蒙太奇）；信仰压轴含少量观众反应镜头。
- 源清晰度：信仰/太想/爱如潮水/宽容为 Live letterbox（画幅没满，符合"保原比例不裁人"硬规则）。
