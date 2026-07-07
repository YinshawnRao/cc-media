# 告五人最被低估的5首歌

竖屏 1080×1920 音乐盘点（倒数 05→01），约 4:26。男声旁白 zm_yunxi。

## 揭晓顺序
05《爱在夏天》(2018) → 04《夜里无星》(2021) → 03《同样一个你》(2020) → 02《带你飞》(2023) → 01《你要不要吃哈密瓜》(2021)

## 成片
`renders/gaowuren-underrated-top5.mp4`（mux 后为准）

## 复现
```bash
# 1. 旁白（已生成 audio/*.wav）
tools/tts/venv/bin/python build/narrate_segments.py
# 2. 竖屏化 clips（窗口化 vfill，源窗+裁切见 SOURCES.md / build 注释）
#    clips_raw/*.mp4 为各源窗口预切；clips/vert_*.mp4 为 letterbox 竖屏
#    哈密瓜/intro 源偏暗 → 先 eq=brightness=0.11:saturation=1.10:contrast=1.06 再 vfill
# 3. 人声段（闸门基准；用全曲检测平移到窗口本地时间，比短窗 per-clip 更稳）
#    probe/vocal_analysis.json
# 4. build（master.wav + index.html + partA/B；内置 showcase_align 闸门）
tools/tts/venv/bin/python build/full_build.py
# 5. 分段渲染 + concat + mux（规避多 video protocolTimeout）
bash build/render_parts.sh
```

## 关键决策
- 选源全部官方（详见 SOURCES.md）；多为剧情/动画 MV，仅《哈密瓜》用官方 Live MV（乐团本人）。
- 三人乐团 → 展示段一律 letterbox 保原比例。
- 封面用《哈密瓜》Live MV 乐团帧（用户确认）。
- 烧死歌词逐首二分抽帧定位、全宽裁净。
- showcase_align 闸门 5/5 OK；副歌响度 -14~-16dB 一致，旁白段 ducking 至 -23~-24dB。

## 待用户耳验
`qa/showcase_mp3/*.mp3` — 各首展示段 26s 试听，确认副歌是否选对（《夜里无星》《爱在夏天》全曲/短窗人声检测有分歧，重点听这两首）。
