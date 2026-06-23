# 周杰伦最苦的5首歌（竖屏盘点 1080×1920）

倒数盘点：05《世界末日》→ 04《不能说的秘密》→ 03《黑色毛衣》→ 02《轨迹》→ 01《搁浅》。
男声旁白 `zm_yunxi`，冷调电影感设计，约 4:33。成片：`renders/zhoujielun-saddest-top5.mp4`。

## 复现
```bash
# 1) 配音（Kokoro，男声）
tools/tts/venv/bin/python build/narrate_segments.py
# 2) 竖屏化素材（已生成 clips/vert_*.mp4；世界末日先 eq 提亮再 vfill）
#    crop 见 SOURCES.md
# 3) 构建音轨 master.wav + HTML（含 partA/partB 拆分）
python3 build/full_build.py
# 4) 渲染两段 + concat + 后期 mux 真音轨
bash build/render_parts.sh
```

## 关键结构
- `build/full_build.py` — 主构建：逐段 床→swell→展示 混音（逐首 loudnorm=-14 对齐 ~-15dB，`alimiter=level=disabled` 防压平 fade/ducking），生成 master.wav + index.html + partA/partB。倒数顺序、各首 `show_start/show/crop/tag/note`、`MGAIN` 都在顶部 `SONGS`。
- `build/narrate_segments.py` — 8 段旁白（intro / 5 首 / outro / 固定 CTA）。
- `build/render_parts.sh` — `-w1` + 重试渲染（本机 GPU 截帧随机崩），`--sdr` 强制 SDR，后期用 master.wav 覆盖音轨。

## 设计
- 冷调电影感：墨蓝底 `#06080d` + 银蓝强调 `#b9d0ea`，压轴 #1 用暖金 `#ffd27a`。衬线大标题 + 无衬线信息层。
- 封面：周杰伦《不能说的秘密》海边特写（真人、居中、无对白字幕），标题居上半屏。
- 展示段：每首一段连续副歌（26–32s），footage 窗 == 音乐窗（口型同步），letterbox 保原比例。
- 片头钩子精简（封面→钩子→过渡，~21s 进第一首），作品 outro 只升华不带投票问句，**固定引流 CTA 为全片最后一句**。

## 源与限制
见 `SOURCES.md`。五首全部 YouTube 官方频道「周杰倫 Jay Chou」官方 MV（480p/1080p 标清，brief 接受）；千禧官方 MV 自带卡拉OK歌词——四首底部歌词已 letterbox 裁净，《世界末日》（2001 范特西演唱会官方影像）中部歌词裁不掉、保留为源限制；《轨迹》官方 MV 为《寻找周杰伦》电影画面无本人，按 brief 官方 MV 优先 + 主题契合保留。B站 4K 修复版普遍带 UP 水印，全部弃用。
