# 徐良最被低估的5首歌

本目录是一期本地测试短视频项目，产物不用于对外发布或商用。

## 生成步骤

```bash
tools/tts/venv/bin/python sandbox/xuliang-underrated-top5/build/narrate_segments.py
tools/tts/venv/bin/python sandbox/xuliang-underrated-top5/build/prep_footage.py
tools/tts/venv/bin/python sandbox/xuliang-underrated-top5/build/full_build.py
cd sandbox/xuliang-underrated-top5/hf
npx --yes hyperframes@0.6.69 lint
npx --yes hyperframes@0.6.69 inspect
npx --yes hyperframes@0.6.69 render --output ../renders/full_raw.mp4
cd ../../..
ffmpeg -y -i sandbox/xuliang-underrated-top5/renders/full_raw.mp4 -i sandbox/xuliang-underrated-top5/master.wav -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 192k -shortest sandbox/xuliang-underrated-top5/renders/xuliang-underrated-top5.mp4
```

## 关键文件

- `SOURCES.md` - 双平台素材检索和最终取舍。
- `build/song_config.py` - 榜单、片段、裁切、时间窗口的单一配置。
- `build/narrate_segments.py` - 旁白生成。
- `build/prep_footage.py` - 竖屏片段和歌曲音频窗口预处理。
- `build/full_build.py` - 预混音频、HyperFrames HTML 和渲染配置生成。
