# 徐怀钰最被低估的5首歌

目标：1080x1920 竖屏倒数盘点，排名按用户指定从 05 到 01 展开，女声旁白覆盖开头、歌曲转场和结尾。

当前状态：工程已搭好，前四首素材、裁切、旁白脚本和时间线脚手架已准备；第五首《不吵不闹》未找到可确认的徐怀钰音视频源，且公开资料更倾向证明该曲属于温岚《蓝色雨》，不是徐怀钰《Bad Girl》。不能交付最终成片。

## 排名

| 名次 | 歌曲 | 当前状态 |
| --- | --- | --- |
| 05 | 不吵不闹 | 阻塞：未找到可确认的徐怀钰版本；公开资料将该曲归到温岚《蓝色雨》；`raw/p5_badgirl_yt.mp4` 只是徐怀钰《Bad Girl》占位素材，不能用于最终交付。 |
| 04 | 等不及 | YouTube 官方 MV 已下载并裁切。 |
| 03 | 乱了 | YouTube 官方 MV 已下载并裁切；B站修复版候选下载慢，已记录。 |
| 02 | 友情卡片 | YouTube 官方 MV 已下载并裁切。 |
| 01 | 温习 | YouTube 官方 MV 已下载并裁切。 |

## 关键文件

- `SOURCES.md`：双平台候选、取舍和第五首阻塞记录。
- `CANDIDATE_REPLACEMENTS.md`：第五首替换候选和可确认的《Bad Girl》相关曲目线索。
- `build/narrate_segments.py`：女声旁白文案生成脚本。
- `build/full_build.py`：生成 `master.wav`、切片和 HyperFrames `index.html` 的脚本；当前有保护，不允许在第五首源未确认时生成最终时间线。
- `clips/vert_p*.mp4`：已完成的竖屏素材。
- `probe/*.jpg`：原始素材和竖屏素材抽帧检查图。
- `probe/vocal_analysis.json`：每首歌的人声段检测结果。

## 继续方式

确认第五首后：

1. 如果仍坚持《不吵不闹》，需要先提供可靠来源证明它是徐怀钰版本；否则从 `CANDIDATE_REPLACEMENTS.md` 里确认一个真实徐怀钰曲目替换第五首。
2. 下载并竖屏化正确素材，替换 `clips/vert_p5_badgirl.mp4` 或改配置指向新文件。
3. 更新 `build/narrate_segments.py` 的第五首旁白和片尾榜单。
4. 更新 `build/full_build.py` 里第五首 `clip`、`meta`、`ch_off` 和 `P5_SOURCE_CONFIRMED`。
5. 重新生成旁白和时间线：

```bash
../../tools/tts/venv/bin/python build/narrate_segments.py
python3 build/full_build.py
```

6. HyperFrames 渲染后必须用 `master.wav` 后期 mux：

```bash
npx hyperframes lint
npx hyperframes inspect --samples 12
npx hyperframes render --output renders/full_raw.mp4 --sdr
ffmpeg -v error -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/xuhuaiyu-underrated-top5.mp4 -y
```

## 未完成 QA

最终成片尚未渲染，因此还没有最终抽帧、`silencedetect`、展示段 `volumedetect` 和 mux 后成片检查。已有素材抽帧显示前四首裁切后未见平台水印、网址、路径、提示词泄漏。
