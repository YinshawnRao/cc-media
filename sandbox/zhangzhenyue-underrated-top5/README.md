# 张震岳最被低估的5首歌

竖屏 1080×1920 音乐盘点，倒数 05→01（#1=《破吉他》压轴），男声旁白 `zm_yunxi`。
全 5 首为滚石官方 MV、本人出镜、**耦合**（footage 与音轨同源同窗 → 口型同步）。

## 榜单（倒数揭晓）
- 05 《梅雨季》— 跟着感觉走 · 2025（爵士遗珠）
- 04 《两手空空》— 我想要的感觉 · 2011
- 03 《很难》— OK · 2007
- 02 《路口》— OK · 2007
- 01 《破吉他》— 我是海雅谷慕 · 2013（压轴）

## 复现
```bash
# 1. 下载官方 MV（YT 媒体 403 → player_client=tv）见 SOURCES.md 各 id，存 raw/<key>.mp4
# 2. 竖屏 letterbox（裁烧词）→ clips/vert_<key>.mp4（梅雨季额外轻提亮）
# 3. 人声段 → probe/vocal_analysis.json（vert_ keys，源时间基准）
# 4. 旁白
tools/tts/venv/bin/python build/narrate_segments.py
# 5. 构建 master.wav + index.html（耦合，showcase_align 闸门强制）
tools/tts/venv/bin/python build/full_build.py        # SAMPLE=1 只出 intro+#5+outro
# 6. 渲染 + mux（--sdr 必加；HF 压平动态 → 后期 mux master.wav）
npx hyperframes@0.6.69 render --output renders/full_raw.mp4 --sdr
ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/zhangzhenyue-underrated-top5.mp4
```

## 关键设计
- **动态封面**（硬约束）：第一首出场=#5《梅雨季》。intro footage 取自 vert_p5_meiyu 的 T0=170 起，与 #5 footage 帧首尾相接 → 封面切第一首画面不剪。封面第 0 帧=src170 暖光侧脸。
- **耦合 mseek 对齐**：footage 与 music 都从 `mseek=ch_off−full_start_local` 切，口型同步。
- **烧词处理**：5 条官方 MV 全带烧死歌词 → vfill 阶段按各自 crop 全宽裁掉横带。
- 暖色调（深暖底 + 琥珀金 accent），呼应张震岳 roots/海边/夜景气质。

详见 `SOURCES.md`（选源、事实核实、逐首取舍、弃用候选）。
