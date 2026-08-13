# 窦唯最难的5首歌 — 溯源与复现

成片：`douwei-hardest.mp4`（1080×1920 / H.264 30fps / AAC / 3:35 / 倒数 5→1）。

## 复现步骤
1. `build/narrate_segments.py` → 女声旁白（Kokoro `zf_xiaoyi`）到 `audio/<key>.wav`。已归档，可跳过。
2. 按下表 yt-dlp 下载各源、trim、`tools/video/vfill.sh` 竖屏化到 `clips/vert_<key>.mp4`。已归档，可跳过。
3. 在一个 `npx hyperframes init` 项目里放 `clips/`、`audio/`，跑 `build/full_build.py` → 生成 `index.html` + `master.wav`。
4. `npx hyperframes render` → 用 `master.wav` 后期 mux 覆盖音轨（铁律，HyperFrames 会压平动态）：
   ```
   ffmpeg -i full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest douwei-hardest.mp4
   ```
   `master.wav`（终版预混）已归档，可直接 mux。

## 素材出处（YouTube id + 切点 + 竖屏 crop）
下载窗口用 `--download-sections "*<起>-<止>"`，`-f "bv*[height<=1080]+ba/b"`；trim 偏移相对下载窗口起点。

| # | 歌 | YouTube id | 频道 | 下载窗口 | trim（窗口内） | 实际歌曲段 | vfill crop |
|---|----|-----------|------|---------|---------------|-----------|------------|
|05|《悲伤的梦》|`_NppdGa5EcA`|滾石 Official Live|02:20–03:40|`-ss 24 -t 55`|~02:44–03:39|`384:400:128:0`|
|04|《靠近我》|`T9P4k17TYW8`|窦唯黑豹时期|00:50–02:30|`-ss 11.5 -t 36.2` + `eq=brightness=0.10:saturation=1.12:contrast=1.06`|~01:01–01:38|`384:400:128:0`|
|03|《无地自容》|`9YxjRbs0Gsg`|滾石 Official MV|00:45–02:15|`-ss 9 -t 36.2`|~00:54–01:30|`384:400:128:0`|
|02|《Don't Break My Heart》|`WLUbs0rCQlI`|滾石 Official MV|00:40–02:00|`-ss 10 -t 35.5`|~00:50–01:25|`384:400:128:0`|
|01|《别来纠缠我》|`XpDObRqft8w`|窦唯黑豹时期（黑白）|00:40–02:00|`-ss 10 -t 39`|~00:50–01:29|`200:180:60:0`|

- 开场/片尾背景复用 05 的 `vert_beishang.mp4`。
- crop 均为**顶部对齐**以裁掉源烧死的歌词字幕；01 额外裁底去字幕带。
- **源清晰度（硬限制）**：黑豹/黑梦时期素材普遍标清；**01 仅 320×246 黑白**（全网无更高清窦唯版本）——黑白颗粒贴合"金属嘶吼"压轴。
- 被排除的 01 候选：`B14diOjSR8w`(Topic 静态)、`iBQkhFmGiPA`(歌词视频静态+NK水印)、`d62ktnR2Pvc`(上下双字幕无法裁净)、2015+ 黑豹重组现场(非窦唯演唱)。

## 设计
- 配色：暗底 `#0a0b0e` + 冰蓝 `#6fd3e8`（主）+ 血红 `#ff2e2e`（爆点/天花板）。冷硬/金属/后朋克，区别于张韶涵粉紫片。
- 配音：女声 `zf_xiaoyi`（用户指定）；逐字稿见 `build/narration.json`。
- 揭晓顺序：**倒数 5→1**，压轴《别来纠缠我》带红色"公认天花板"角标。
- 文案铁规：成片内不得出现描述视频自身机制的 meta 文案（如"倒数开始/从第5名"——已按用户要求剔除）。

## 关键时间常量（`build/full_build.py`）
`LEAD=0.3 / DIG(swell)=1.4 / SHOW=17.0 / GAP_A=1.35 / 旁白床 BED_N=0.14 / 钩子床 BED_I=0.08`；逐首 `loudnorm=I=-14:TP=-1.0:LRA=11` 统一响度。

## QA 结果
lint 0 error；无 >1s 静音；五首副歌 -18.0~-19.0dB 一致；逐段抽帧确认排名/文案正确、画面无水印/字幕/路径泄漏。
