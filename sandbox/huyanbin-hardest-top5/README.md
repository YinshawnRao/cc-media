# 胡彦斌最难的5首歌

竖屏 1080x1920 声乐难度盘点，按倒数揭晓顺序：05《失业情歌》 -> 04《诀别诗》 -> 03《红颜》 -> 02《月光》 -> 01《你要的全拿走》。

制作约束：
- 女性旁白 `zf_xiaoyi`，开头、每首转场、结尾均有口播。
- 每首必须 YouTube + B站双平台查源，并在 `SOURCES.md` 记录候选和取舍。
- 每首展示段按最高音/难句重新分析后选取，full-music 窗口必须有人声演唱，不使用纯背景音乐。
- 每首展示段使用连续代表段，优先保原比例 letterbox，避免把主体裁掉。
- 渲染后必须用预混 `master.wav` 后期 mux，成片以 mux 后 MP4 为准。
- 固定 CTA 作为全片最后一句旁白，由 `tools/video/outro_cta.py` 注入。

复现流程：
1. `build/narrate_segments.py` -> `audio/*.wav` + `narration.json`
2. `build/analyze_high_notes.py` -> `qa/high_note_analysis.json` + `qa/high_note_analysis.md`
3. 按 `qa/high_note_selection.md` 和 `SOURCES.md` 下载/切片/竖屏化 -> `clips/vert_*.mp4`
4. `build/full_build.py` -> `master.wav` + `index.html`
5. `npx hyperframes render --output renders/full_raw.mp4 --sdr --workers 1`
6. `ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/huyanbin-hardest-top5.mp4`

最终产物：
- `renders/huyanbin-hardest-top5.mp4`
- 1080x1920 / 30fps / 306.05s / H.264 + AAC stereo

QA 记录：
- `npx hyperframes inspect --samples 12`：0 layout issues
- `npx hyperframes lint`：0 errors；仅 GSAP Studio 写回限制和 track 过密两个非阻塞 warning
- `ffmpeg silencedetect=n=-35dB:d=1`：未检出 1 秒以上静音段
- `ffmpeg volumedetect`：mean_volume -17.2 dB，max_volume -1.1 dB
- 高音/难句选段：`qa/high_note_analysis.md`、`qa/high_note_selection.md`
- 展示窗人声覆盖检测：`qa/showcase_vocals_v2.json`
- 《月光》源/窗口复核：`qa/yueguang_live_sheet.png`、`qa/yueguang_live_crop_1920x620_y120.png`、`qa/yueguang_first_chorus_sheet.png`、`qa/final_yueguang_show_sheet.png`
- 抽帧检查：`qa/final_sheet_20s_v3_yueguang.png`、`qa/show_p5_shiye_sheet.png`、`qa/show_p4_juebieshi_sheet.png`、`qa/show_p3_hongyan_sheet.png`、`qa/show_p1_quannazou_sheet.png`
