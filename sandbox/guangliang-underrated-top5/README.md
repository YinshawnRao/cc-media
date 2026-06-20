# 光良最被低估的5首歌 (guangliang-underrated-top5)

竖屏 1080×1920 · 5:16 · 女声盘点 · 倒数揭晓 5→1（片头不剧透，片尾揭晓榜单）。

成片：`renders/guangliang-underrated-top5.mp4`

## 排名（1→5，最被低估→次之）
1 如果你还爱我 · 2 握你的手 · 3 期限 · 4 海边 · 5 住在遥远的星球

## 构建
1. `tools/tts/venv/bin/python build/narrate_segments.py`  # 女声旁白(zf_xiaoyi)+固定CTA
2. `python build/clips.py`                                 # 切 footage(delogo/crop/letterbox/调色)+各首 music/<key>.wav
3. `python build/full_build.py`                            # master.wav + index.html
4. `bash build/render_full.sh`                             # 渲染(--sdr, -w1 重试)
5. `bash build/finalize.sh`                                # 预混 master.wav 后期 mux → 成片

配置单一源 `build/song_cfg.py`（clips.py 与 full_build.py 共用）。

## footage 说明（重要）
- 5 首里只有《如果你还爱我》有可用本人演唱影像（滚石"官方MV" 9Kof4TwmHuA 实为致敬合辑，仅 @196-255 红衣演唱段干净）。
- 《握你的手》《期限》《海边》《住在遥远的星球》是深专辑曲，全网无 MV/Live（官方频道仅静态专辑图/歌词视频）。
- **当前版本**：因 YouTube cookie 缺认证字段、且 B站 fan 4K 普遍带中心平铺防搬运水印，rank2/4/5 复用《那些爱过的事》2016 官方巡演 Live 的光良干净特写做 B-roll + 本曲录音室音频解耦，每首调色区分（冷蓝/青/紫）。
- **升级路径**：YT cookie 修好后，下载 2016 巡演 掌心/烟火/多心 给 rank2/4/5 换上不同造型的独立画面（见 SOURCES.md）。
详见 SOURCES.md。
