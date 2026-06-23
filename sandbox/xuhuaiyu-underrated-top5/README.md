# 徐怀钰最被低估的5首歌

目标：1080x1920 竖屏倒数盘点，排名按用户指定从 05 到 01 展开，女声旁白覆盖开头、歌曲转场和结尾。

当前状态：第五首已按用户要求从误归属的《不吵不闹》替换为《我不要》。五首素材均已完成双平台候选记录，其中《我不要》选用 B站 1080P 修复 MV 源，完成竖屏裁切，并已按反馈把展示段重对齐到原片约 73.7s 的副歌核心。

## 排名

| 名次 | 歌曲 | 当前状态 |
| --- | --- | --- |
| 05 | 我不要 | B站 1080P 修复 MV 已下载并裁切；展示段覆盖原片约 73.7-105.7s；YouTube 滚石官方 MV 已确认存在但当前 cookie 失效，无法下载。 |
| 04 | 等不及 | YouTube 官方 MV 已下载并裁切。 |
| 03 | 乱了 | YouTube 官方 MV 已下载并裁切；B站修复版候选下载慢，已记录。 |
| 02 | 友情卡片 | YouTube 官方 MV 已下载并裁切。 |
| 01 | 温习 | YouTube 官方 MV 已下载并裁切。 |

## 关键文件

- `SOURCES.md`：双平台候选、取舍和第五首替换记录。
- `CANDIDATE_REPLACEMENTS.md`：历史阻塞与替换决策记录。
- `build/narrate_segments.py`：女声旁白文案生成脚本。
- `build/full_build.py`：生成 `master.wav`、切片和 HyperFrames `index.html` 的脚本；当前有保护，不允许在第五首源未确认时生成最终时间线。
- `clips/vert_p*.mp4`：已完成的竖屏素材；第 5 首当前使用 `clips/vert_p5_wobuyao.mp4`。
- `probe/*.jpg`：原始素材和竖屏素材抽帧检查图。
- `probe/vocal_analysis.json`：每首歌的人声段检测结果。

## 继续方式

重新生成旁白和时间线：

```bash
../../tools/tts/venv/bin/python build/narrate_segments.py
python3 build/full_build.py
```

HyperFrames 渲染后必须用 `master.wav` 后期 mux：

```bash
npx hyperframes lint
npx hyperframes inspect --samples 12
npx hyperframes render --output renders/full_raw.mp4 --sdr
ffmpeg -v error -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/xuhuaiyu-underrated-top5.mp4 -y
```

## 未完成 QA

最终成片尚未渲染，因此还没有最终抽帧、`silencedetect`、展示段 `volumedetect` 和 mux 后成片检查。已有素材抽帧显示五首裁切后未见平台水印、网址、路径、提示词泄漏。
