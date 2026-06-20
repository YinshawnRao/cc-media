# fangdatong-underrated-top5

竖屏 1080×1920 音乐解说盘点 ·「方大同最被低估的5首歌」· 倒数 5→1 · 女声旁白（zf_xiaoyi）· ≈5:04。

榜单（1→5）：1《Take Me》· 2《Orange Moon》· 3《黑洞里》· 4《暖》· 5《Over》。
开头不揭名次（封面 + 作品描述），片尾列完整榜单。英文歌名旁白不念、由屏幕卡片承载；中文歌名旁白可念。

## 复现
1. `build/narrate_segments.py` — 女声旁白 wav（Kokoro zf_xiaoyi）→ `audio/`、`narration.json`。
2. 素材下载（B站，见 `SOURCES.md` 的 bvid）→ `raw/`；AV1 源转 H.264 代理 → `proxy/`。
3. `build/make_verts.sh` — 切窗口 + delogo 水印 + crop 烧词 + letterbox → `clips/vert_*.mp4`（各 58s，干净）。封面/片头背景 `clips/vert_cover.mp4`。
4. `build/full_build.py` — 建 `master.wav`（逐段 床→swell→展示，`loudnorm=I=-14`）+ 生成 `index.html`。
5. `build/render_full.sh` — `npx hyperframes@0.6.47 render --sdr -w1` + 重试循环（本机 GPU 截帧随机崩）→ `renders/full_raw.mp4`。
6. mux 后期音轨：`ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/fangdatong-underrated-top5.mp4`。

## 关键决策
- 五首皆冷门曲，**无干净官方剧情 MV**，全用 Live；四首同出 2011「15」香港演唱会，《暖》出 2008「Wonderland」。
- B站「修复号」源画质高但带 UP 主水印 / 华纳 DVD 烧词与版权角标 → 逐源 delogo + crop，逐帧验证成片无残留。
- 详见 `SOURCES.md`、设计基调 `design.md`。

成片：`renders/fangdatong-underrated-top5.mp4`（mux 后为准）。可丢弃中间物：`raw/ proxy/ probes/ qa/ renders/work-*`。
</content>
