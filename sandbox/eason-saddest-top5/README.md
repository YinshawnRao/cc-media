# 陈奕迅最苦的5首歌

竖屏 1080x1920 倒数盘点，揭晓顺序：⑤葡萄成熟时 → ④最佳损友 → ③人来人往 → ②明年今日 → ①富士山下。

## 复现

```bash
../../tools/tts/venv/bin/python build/narrate_segments.py
bash build/clips.sh
../../tools/tts/venv/bin/python build/full_build.py
/Users/yinshawnrao/.npm-cache/_npx/9034813775a58c19/node_modules/.bin/hyperframes lint
bash build/render.sh
```

最终成片：`renders/eason-saddest-top5.mp4`。音轨为后期 mux 的 `master.wav`。

## QA

见 `QA.md`。当前官方 HyperFrames 成片已完成：
- 1080x1920 H.264 + AAC stereo。
- 时长 293.292s。
- `silencedetect=n=-35dB:d=1` 无 >1s 静音。
- 五首展示段响度均衡，均为连续演唱展示。
