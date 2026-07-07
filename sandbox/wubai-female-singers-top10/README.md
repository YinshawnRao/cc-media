# 伍佰给女歌手写的歌 TOP10

竖屏 1080×1920 音乐盘点，倒数 10→1。主题：摇滚浪子伍佰，把最细腻的一面写进了别人（女声）的歌里。
封面/片头/片尾主角 = 词曲作者**伍佰本人**（幕后创作者盘点）。

## 榜单（揭晓序 10→1）
10 黄小琥《突然的自我》· 9 郁可唯《你不要我了吗》· 8 杨乃文《一个人》· 7 刘若英《最初的地方》·
6 万芳《夜照亮了夜》· 5 那英《我不是天使》· 4 王菲《单行道》· 3 莫文蔚《坚强的理由》·
2 苏慧伦《被动》· 1 王心凌《我会好好的》

## 结构 / 工具
- 复用柯南 TOP10 模板（单一 `footage_track` + `silent.m4a` 占位 + 后期 mux master.wav）。
- sync（官方MV/Live 音画同源）：p1 p2 p3 p8 p9；decouple（官方录音室音频 + 本人现场/同期 b-roll）：p4 p5 p6 p7 p10。
- 选源细节见 `SOURCES.md`；旁白 `build/narrate_segments.py`；合成 `build/full_build.py`；渲染 `build/render_loop.sh`。

## 构建
```bash
tools/tts/venv/bin/python build/narrate_segments.py     # 旁白（已生成）
python3 build/full_build.py                              # footage 切段 + master.wav + 对齐闸门 + index.html + footage_track
MINDUR=482 bash build/render_loop.sh                     # 渲染（单轨重试循环）
# mux：
ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/wubai-female-singers-top10.mp4
```
增量：`HTML_ONLY=1` 只重生 index.html；`AUDIO_ONLY=1` 只重建 master.wav。

## 结尾
作品 outro（十声同一个伍佰）→ 固定引流 CTA（仓库级硬约束，逐字）。
