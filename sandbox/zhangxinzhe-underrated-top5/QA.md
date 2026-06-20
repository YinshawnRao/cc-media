# QA — 张信哲最被低估的5首歌

## 结构检查

- `npx --yes hyperframes@0.6.69 lint`
  - 0 errors。
  - warnings：轨道元素较密；CJK 字体提示。渲染时 HyperFrames 已缓存并注入 `Noto Sans SC` / `Noto Serif SC`。
- `npx --yes hyperframes@0.6.69 validate`
  - No console errors。
  - 145 text elements pass WCAG AA。
- `npx --yes hyperframes@0.6.69 inspect --samples 12`
  - 0 layout issues。

## 渲染产物

- Raw render：`renders/full_raw.mp4`
  - H.264 1080×1920 30fps + AAC。
  - duration `295.921029s`。
- Final mux：`renders/zhangxinzhe-underrated-top5.mp4`
  - H.264 1080×1920 30fps + AAC。
  - duration `295.539000s`。
  - audio from `master.wav`。

## 画面 QA

- 关键帧总览：`qa/contact.jpg`。
- 抽帧未见平台水印、UP 主水印、网址、路径或提示词。
- #1 B站修复源因左上“拾光映画馆”水印排除，最终使用 YouTube 官方低清源。
- #3 可能 MV 候选因 B站/频道标识和大歌词排除，最终使用 2006 Live 并 crop 底部烧字。

## 音频 QA

`silencedetect=n=-35dB:d=1.5` 未报 >1.5s 静音。

展示段 `volumedetect`：

| 段落 | mean volume | max volume |
| --- | ---: | ---: |
| #5 空出来的时间刚好拿来寂寞 | -14.3 dB | -3.4 dB |
| #4 你应该飞的 | -14.8 dB | -0.4 dB |
| #3 说谎 | -15.7 dB | -5.2 dB |
| #2 下一个永远 | -13.7 dB | -2.0 dB |
| #1 心情卡片 | -15.5 dB | -0.4 dB |
