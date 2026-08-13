# 素材来源与双平台取舍

本项目按同一首曲目同时检索 YouTube 与 B站，再按版本真实性、画面清洁度、清晰度、立体声和现场表现综合取舍。

| 排名 | 曲目 | YouTube 候选 | B站候选 | 最终采用与理由 |
| --- | --- | --- | --- | --- |
| 05 | Mister Magic — Grover Washington Jr. | [1981 现场实演](https://www.youtube.com/watch?v=BwC0jHD46vo)，1440×1080，立体声；官方 Topic 仅静态封面 | [同场现场候选](https://www.bilibili.com/video/BV1cp4y1Q7La)，480×360 | 采用 YouTube 现场 `p5_mister_magic_yt.mp4`。非官方上传是本期唯一来源例外；它是真实歌手/真实现场，画面与声音明显优于 B站候选，也比官方静态封面更适合作为视频。窗口 748.7–872.0s，避开约 873s 后演职员表。 |
| 04 | Forever in Love — Kenny G | [Kenny G 官方 MV](https://www.youtube.com/watch?v=OOO4ROO_sPM)，640×480 | [Sony Music China 官方上传](https://www.bilibili.com/video/BV1cJ411x7gh)，640×480，视频码率更高 | 采用 B站官方 `p4_forever_in_love_bili.mp4`。窗口 104.8–170.3s；经画面复核主动避开后段不适合本期叙事的亲密剧情镜头。 |
| 03 | Lily Was Here — David A. Stewart & Candy Dulfer | [Dave Stewart 官方 MV](https://www.youtube.com/watch?v=ypbjIwbTR8c)，640×480 | [Sony Music China 官方上传](https://www.bilibili.com/video/BV14T4y1K7Dw)，768×576 | 采用 B站官方 `p3_lily_was_here_bili.mp4`，分辨率和码率更好。窗口 183.9–258.4s，直到乐曲自然衰减。 |
| 02 | Going Home — Kenny G | [Kenny G 官方 MV](https://www.youtube.com/watch?v=HhKQccJRamU)，1440×1080，立体声 | [B站候选](https://www.bilibili.com/video/BV1us411e7zJ)，640×480 | 采用 YouTube 官方 `p2_going_home_yt.mp4`，清晰度显著更高。窗口 294.0–382.0s，在演奏结束后、黑场前收口。 |
| 01 | Songbird — Kenny G | [Kenny G 官方 MV](https://www.youtube.com/watch?v=QN2RnjFHmNY)，官方但视频码率较低 | [Sony Music China 官方上传](https://www.bilibili.com/video/BV13J411s7Wh)，640×480，H.264 码率更高 | 采用 B站官方 `p1_songbird_bili.mp4`。窗口 145.6–242.0s，在片尾淡黑前自然收束。 |

## 画面复核证据

- `probe/p1_*` 至 `probe/p5_*`：源素材、最终窗口与尾部接触表。
- `probe/p4_window_alt_sheet.jpg`：第四名替代窗口的专门复核。
- `probe/instrumental_analysis.json`：RMS、onset 与安静边界分析。
- `probe/instrumental_plan.json`：最终窗口、源时码、连续音乐时长、视觉证据和分析文件哈希绑定。

所有最终窗口均未发现平台/UP 主水印、网址、路径、提示词或烧录旁白字幕。
