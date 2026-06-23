# 华语乐坛到底有多少首《暧昧》？

小红书竖屏音乐盘点 / 同名歌情绪时间线。

## Brief

- 主题：同样叫《暧昧》，不同年代唱的是完全不同的关系。
- 规格：1080x1920，中文女性旁白，前 3 秒制造评论欲。
- 顺序：开场彩蛋 黄莺莺《情雪》；第 4 首 侯湘婷《暧昧》；第 3 首 薛之谦《暧昧》；第 2 首 杨丞琳《暧昧》；第 1 首 王菲《暧昧》。
- 口径：黄莺莺《情雪》不是同名正选，只作为王菲《暧昧》的旋律源头彩蛋。
- 展示：每首必须保留完整副歌或最具代表性的连续核心片段，副歌期间不压旁白。
- 输出：最终以 `renders/aimei-evolution.mp4` 为准，必须由 HyperFrames 画面 + 预混 `master.wav` 后期 mux 生成。

## Repo Constraints

- 每条素材必须同时查 YouTube + B站，并在 `SOURCES.md` 记录候选和取舍。
- Cookie 只读仓库根目录：`www.youtube.com_cookies.txt`、`www.bilibili.com_cookies.txt`。
- 竖屏化默认 letterbox 保原比例，只有为裁平台水印/烧字时才做全宽横带 crop。
- 成片最后一句旁白必须追加固定 CTA：
  `你最想为哪一首投票？评论区告诉我。记得点赞、收藏、关注我，下一期，可能就盘到你单曲循环过的那一首。`

## Planned Artifacts

- `design.md`：视觉系统。
- `.hyperframes/expanded-prompt.md`：按 HyperFrames 要求展开的制作拆解。
- `SOURCES.md`：YouTube + B站候选和最终选择。
- `narration.json`：旁白分段和时间轴。
- `audio/voice/*.wav`：本地 Kokoro 女声旁白。
- `audio/master.wav`：最终预混音轨。
- `index.html`：HyperFrames 竖屏 composition。
- `renders/aimei-evolution.mp4`：mux 后最终成片。

## QA Gates

- `npm run check` 或等价 `npx hyperframes lint/validate/inspect` 无 error。
- `ffmpeg silencedetect=n=-35dB:d=1` 检查无异常长静音；段间自然短停需人工确认合理。
- `ffmpeg volumedetect` 抽测各首 full-music 段响度接近。
- 抽帧 contact sheet 逐帧看：无平台/UP 主水印、网址、路径、提示词；歌名歌手无误；黄莺莺不写成《暧昧》。
