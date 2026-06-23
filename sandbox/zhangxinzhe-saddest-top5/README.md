# 张信哲最苦的5首歌

本项目生成竖屏 1080×1920 本地测试成片，标题为“张信哲最苦的5首歌”。

## 结构

- 揭晓顺序：05《信仰》→ 04《用情》→ 03《别怕我伤心》→ 02《爱如潮水》→ 01《过火》
- 旁白：开头、每首转场、作品 outro、固定 CTA
- 源：优先官方 MV / 官方 MV 修复；详见 `SOURCES.md`
- 音频：`master.wav` 后期 mux，成片以 mux 后 MP4 为准

## 复现

```bash
tools/tts/venv/bin/python build/narrate_segments.py
python3 build/full_build.py
bash build/render_parts.sh
```

最终输出：`renders/zhangxinzhe-saddest-top5.mp4`
