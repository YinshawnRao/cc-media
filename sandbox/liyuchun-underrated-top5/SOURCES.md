# 素材来源与取舍

## 总原则

按仓库约束，每首同时查 YouTube 与 B站候选，优先官方 MV / 工作室 / 官方频道素材；若无稳定 MV，则选歌手出镜更清楚、声音更稳定的 live。最终源均使用根目录 `all_cookies.txt` 获取或校验，不在 `sandbox/` 复制 cookie。

## 第 5 名：《小宇宙》

- YouTube 候选：`BSkvnloYRYQ` / `6sun2W0tybQ`，Topic/音频类，1080x1080，偏静态；`LzgHwL_gmKo`、`_ClhANjZn0k`、`uee5zmj1-2Q` 为演唱会现场，最高 360p/480p。
- B站候选：`BV1fW411G7KB`，演唱会现场，1920x1080，立体声；`BV16W411u7CA`、`BV1QK411M7Dm` 为长 MV 合集。
- 取舍：最终选 `BV1fW411G7KB?p=1`。它不是官方 MV，但歌手出镜明确、1080p、立体声；用全宽横带 crop 去掉电视台台标和底部歌词。
- 本地文件：`raw/p5_xiaoyuzhou_bili_live.mp4` -> `clips/vert_xiaoyuzhou.mp4`。

## 第 4 名：《冷暖》

- YouTube 候选：`VWsRO_DxrAw`，官方版超清，1280x720，立体声。
- B站候选：`BV1Aa4y1s7Zi`，Official 官方 MV，1920x1080，立体声；`BV1HZ4y1V7Nh` 为 Channel[V] 转存。
- 取舍：最终选 B站 `BV1Aa4y1s7Zi`，分辨率更高，画面与 YouTube 版本一致且未见额外平台水印。
- 本地文件：`raw/p4_lengnuan_bili.mp4` -> `clips/vert_lengnuan.mp4`。

## 第 3 名：《似火年华》

- YouTube 候选：`1RcB-3ggW0k`，官方 MV，1280x720，立体声。
- B站候选：`BV1ZE411T7TW`，MV 转存，最高 1280x528；`BV1WG4y1u76W` 为 4K 修复双曲合集。
- 取舍：最终选 YouTube `1RcB-3ggW0k`。B站首个候选纵向分辨率更低，合集不如单曲 MV 稳定；YouTube 官方 MV 更适合作为独立素材。
- 本地文件：`raw/p3_sihuo_yt.mp4` -> `clips/vert_sihuo.mp4`。

## 第 2 名：《一而再再而三地喜欢你》

- YouTube 候选：`TlasiCK2t_Q`，LiYuChun Channel 2020 四川卫视跨年 live，854x480，立体声；`Yq4Pgg3XG5A` 为央视端午晚会现场。
- B站候选：`BV1x5411s7W6`，定制音乐短片，1920x1080，立体声，但主要是剧情素材且有 QQ 音乐标识；`BV1U4411B7ag`，李宇春疯狂工作室 live，1920x1080，立体声。
- 取舍：最终选 B站 `BV1U4411B7ag`。它比 YouTube live 清晰，比 QQ 音乐短片更聚焦李宇春本人，适合“温柔细腻”这首的展示段。
- 本地文件：`raw/p2_yierzai_bili_live.mp4` -> `clips/vert_yierzai.mp4`。

## 第 1 名：《西门少年》

- YouTube 候选：`-g3kp8yXeT8`，LiYuChun Channel Official MV，1280x720，立体声。
- B站候选：`BV1Bs411W7kx`，李宇春疯狂工作室 MV，1920x1080，立体声；`BV1Yh411n7Kv` 为蓝光转存。
- 取舍：最终选 B站 `BV1Bs411W7kx`。与 YouTube 官方 MV 画面一致，分辨率更高且无额外平台水印。
- 本地文件：`raw/p1_ximenshaonian_bili.mp4` -> `clips/vert_ximenshaonian.mp4`。

## 竖屏处理

所有最终素材使用 `tools/video/vfill.sh` 做 1080x1920 竖屏填充。策略为全宽横带 crop + 模糊背景，优先保留横版 MV / live 的完整构图。《小宇宙》额外裁掉源顶部电视台台标和底部歌词。
