# 谢霆锋最被低估的5首歌（竖屏盘点 1080×1920）

倒数 05→01 解说盘点，男声 `zm_yunxi`，约 5:43。成片：`renders/xietingfeng-underrated-top5.mp4`（mux 后为准）。

## 榜单（揭晓顺序 05→01）
- 05 《罗生门》— 无形的他全精选 2002（国语新曲）
- 04 《怕黑》— One Inch Closer 2005
- 03 《不散》— Listen Up 2004（谢霆锋自己作曲）
- 02 《苦海孤雏》— Reborn 2003（林夕为纪念张国荣而作词）
- 01 《潜龙勿用》— 玉蝴蝶 2001（压轴，谢霆锋自己作曲）

## 选源 / 关键决策
见 `SOURCES.md`。要点：潜龙勿用/苦海孤雏 的 B站高清重制版反而烧了台标/卡拉OK歌词，改用干净但只有 480p 的 YT
官方原档；罗生门用 B站行者隐超清版（无额外烧字，画质明显更优）；不散/怕黑 的 EEG 官方频道版本只有"歌词版"静态卡片，
非真 MV → 解耦（官方录音室音轨 + 谢霆锋本人其他官方 MV/Live 救场：不散←壞習慣、怕黑←遊樂場）。

## 复现
1. 配音：`tools/tts/venv/bin/python build/narrate_segments.py`（→ audio/*.wav）。
2. 源：`raw/` 下载 YT/B站 官方源（id 见 SOURCES.md），`raw/p{1..5}_aud.wav`=录音室音轨（耦合曲直接从官方MV抽轨，
   解耦曲从"完整版"视频抽轨）。
3. 竖屏化：`raw/trim/*.mp4`（ffmpeg 精确 -ss/-t 预切到各自 mseek/footage_seek 窗口）→ `tools/video/vfill.sh`
   letterbox 全宽直通（crop=源分辨率:0:0，五条源均确认无需裁台标/烧词）→ `clips/vert_{p1..p5,cover,outro}.mp4`。
4. 人声段：直接对 `raw/p{1..5}_aud.wav`（全长原始音轨，与 `ch_off` 同基准）跑
   `tools/video/vocal_segments.py`，输出重命名 key 为 `vert_p{n}` 存入 `probe/vocal_analysis.json`
   （因部分曲目画面/音频解耦，vocal 检测必须对准音频源的原始时间轴，不能对已裁切的 vert 片段跑）。
5. 构建：`tools/tts/venv/bin/python build/full_build.py` → 过 `showcase_align.gate`(5/5 OK) → master.wav +
   clips_seg + **footage_track.mp4（单轨）** + index.html。
6. 渲染（单 footage_track 避免 HF 多 video 帧0 协议超时，-w1 + --sdr）：
   `npx hyperframes@0.6.69 render --output renders/full_raw.mp4 --sdr -w1`
7. mux：`ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/xietingfeng-underrated-top5.mp4`

## 踩坑记录
- **yt-dlp 默认 client 403（2026-07）**：`tv downgraded player API` + `jsc:deno` 解密链路对 adaptive 流普遍 403；
  加 `--extractor-args "youtube:player_client=web,web_embedded,web_music,mweb"` 后恢复正常（含 1080p）。见 SOURCES.md。
- **B站"超清重制"不等于干净源**：本期两条 B站行者隐重制版（潜龙勿用/苦海孤雏）画质明显更高，但抽帧发现二次烧了
  `EEG` 台标或卡拉OK歌词条，画面干净度不及 YT 官方 480p 原档 → 选源时"分辨率"与"干净度"要分开验证，不能只看分辨率。
- **解耦曲的人声检测基准**：`vocal_segments.py` 必须跑在完整原始音轨（`raw/p{n}_aud.wav`）上，输出的 key 手动改名为
  `vert_p{n}` 才能对上 `showcase_align.gate()` 的查找逻辑；不能直接对已裁切的 `clips/vert_*.mp4` 跑（那样时间基准会
  变成 clip-local 而非源时间，闸门核对会全错）。
- **暗色打光角色误判**：潜龙勿用 MV 中谢霆锋本人挑染暗红发色 + 暗调打光，初次抽帧误判为女性角色，多帧+更亮时间点复核后
  确认为他本人的摇滚概念镜头。
