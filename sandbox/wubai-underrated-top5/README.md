# wubai-underrated-top5 — 伍佰最被低估的5首歌

竖屏 1080×1920 倒数盘点（5→1），女声解说，约 4:54。悬念片头不剧透名次，片尾列完整榜单。

倒数顺序：第5 来不及 → 第4 飞在风中的小雨 → 第3 没人爱的女孩 → 第2 亲爱的，你喝醉了 → 第1 破碎的收音机。

## 复现
```bash
# 1) 配音（女声 zf_xiaoyi）
tools/tts/venv/bin/python build/narrate_segments.py
# 2) 切片+竖屏化+救场曲mux录音室音频 → clips/vert_*.mp4
python3 build/prep_clips.py
# 3) 构建 master.wav + index.html（按实际段长对齐时间轴）
python3 build/full_build.py
# 4) 渲染（单worker+重试避GPU崩, 强制SDR）
npx hyperframes render --output renders/full_raw.mp4 --sdr -w 1
# 5) 后期mux（HyperFrames会压平音频动态，必须用预混master覆盖）
ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/wubai-underrated-top5.mp4
```

成片以 mux 后 `renders/wubai-underrated-top5.mp4` 为准。选源与坑见 `SOURCES.md`，设计见 `design.md`。

## 关键决策
- 第3《没人爱的女孩》、第1《破碎的收音机》全网无干净本人影像 → 用户选「演唱会HD画面救场」：录音室原版音频 + 1999~2000真世界官方Live 伍佰特写（画面与音频解耦的蒙太奇救场）。详见 SOURCES.md。
- 第2 zuile MV 切片音轨偏移2.6s → 整段重编码 a/v 对齐后再用。
