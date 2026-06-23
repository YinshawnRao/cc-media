# 王菲最苦的5首歌

竖屏短视频项目，画幅 1080x1920，倒数揭晓 5 到 1。

## 排名

1. 05 《暧昧》
2. 04 《邮差》
3. 03 《棋子》
4. 02 《笑忘书》
5. 01 《暗涌》

## 结构

- 片头：12.266s，封面底片来自《暧昧》MV 段。
- 单曲段：每首先旁白，音乐作为低音量床；旁白结束后进入 full-music 展示段。
- 片尾：榜单复盘 + 固定 CTA。
- 最终音频：以 `master.wav` 为准，HyperFrames 渲染后再用 FFmpeg mux 覆盖音轨。

关键时间见 `timeline.json`：

| 排名 | 歌曲 | 段落起点 | full-music 起点 | 段落终点 |
| --- | --- | ---: | ---: | ---: |
| 05 | 暧昧 | 12.266 | 27.291 | 82.218 |
| 04 | 邮差 | 82.218 | 97.218 | 131.131 |
| 03 | 棋子 | 131.131 | 145.906 | 181.890 |
| 02 | 笑忘书 | 181.890 | 196.665 | 238.644 |
| 01 | 暗涌 | 238.644 | 254.044 | 295.963 |

## 复现命令

在仓库根目录执行：

```bash
cd sandbox/wangfei-saddest-top5
../../tools/tts/venv/bin/python build/narrate_segments.py
../../tools/tts/venv/bin/python build/make_clips.py
../../tools/tts/venv/bin/python build/full_build.py
/Users/yinshawnrao/.npm-cache/_npx/9034813775a58c19/node_modules/.bin/hyperframes lint
bash build/render.sh
```

最终成片路径：

```text
sandbox/wangfei-saddest-top5/renders/wangfei-saddest-top5.mp4
```
