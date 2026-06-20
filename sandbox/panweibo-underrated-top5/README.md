# 潘玮柏最被低估的5首歌 (panweibo-underrated-top5)

竖屏 1080×1920 · 5:14 · 女声盘点 · 倒数揭晓 5→1（片头不剧透，片尾揭晓榜单）。

成片：`renders/panweibo-underrated-top5.mp4`

## 排名（1→5，最被低估→次之）
1 街头诗人 · 2 跟我走吧 · 3 我们都怕痛 · 4 机会 · 5 寂屋出租

## 构建
1. `tools/tts/venv/bin/python build/narrate_segments.py`  # 女声旁白(zf_xiaoyi)+固定CTA
2. `python3 build/clips.py`                                # 切 footage(crop/letterbox/调色)+各首 music/<key>.wav
3. `python3 build/full_build.py`                           # master.wav + index.html
4. `bash build/render_full.sh`                             # 渲染(--sdr, -w1 重试)
5. `bash build/finalize.sh`                                # 预混 master.wav 后期 mux → 成片

配置单一源 `build/song_cfg.py`（clips.py 与 full_build.py 共用，防漂移）。

## footage 说明（重要）
- **B站为主**（本期 YT cookie 失效，详见 SOURCES.md）。4 首是 2003–2008 SD 原生年代，B站官方/等效源即原画质。
- 4 首同源对口型：寂屋出租 / 机会 / 我们都怕痛 / 跟我走吧 的官方 MV（footage 窗 == 音乐窗）。
  - 机会 = 1280×720 修复（天台 band 抒情摇滚，潘玮柏特写）。
  - 我们都怕痛 = 《爱无限》剧情 MV，取末段副歌潘玮柏特写；信箱内容裁净 QQ音乐角标+烧词。
- 1 首解耦：**街头诗人**（说唱专辑曲全网无官方 MV）→ 录音室音频 + 同专辑《反转地球》2007 官方 MV(1080p 修复) B-roll。
- 封面/片头/片尾底 = 《反转地球》MV @115 潘玮柏 headphones 暖调特写（首帧作封面）。
- **升级路径**：YT cookie 修好后，《我们都怕痛》(2012) 可下 YT 官方 HD MV 单独替换、一轮重渲升级。
详见 SOURCES.md / design.md。
