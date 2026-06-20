# 张信哲最被低估的5首歌 — 选源记录

原则：每首同时查 YouTube 和 B站，按清晰度、画面干净度、立体声、版本质量综合选择。最终成片不保留平台水印、UP 主水印、网址、路径或提示词。

## 最终选源

| 排名 | 歌曲 | YouTube 候选 | B站候选 | 最终选择与原因 |
| --- | --- | --- | --- | --- |
| 05 | 《空出来的时间刚好拿来寂寞》 | `qSz0rAOHSV4` 潮水音乐官方完整版 MV，1280×720，立体声 | `BV1ie4y1B7Sy` 4K修复版，1280×720 下载候选，左下有修复/频道标记 | 选 YouTube 官方 MV。B站版左下标记明显，官方版无平台/UP 水印；用 `crop=1280:430:0:75` 去掉黑边和字幕。 |
| 04 | 《你应该飞的》 | `K8PwYrOFUkU` Jeff Chang Topic 官方音频，只有静态/音频保底 | `BV1KXVPz6EHH` 官方 MV DVD Karaoke 候选，1280×720，立体声 | 选 B站 MV 候选。YouTube 只有 Topic/歌词源；B站有动态 MV。用 `crop=1160:560:60:0`，最终展示窗避开右侧片头/唱片标识。 |
| 03 | 《说谎》 | `83ifuiRG0lM` Jeff Chang Topic 官方音频；另有 KTV/歌词/用户上传 | `BV1eZ421b7dA` 2006 Live；`BV1nc411u7Su` MV候选但有 B站/频道标识和大歌词 | 选 B站 2006 Live。可能 MV 候选污染太重；Live 画面无平台水印，底部演唱会烧字用 `crop=962:590:0:0` 去掉。 |
| 02 | 《下一个永远》 | `s3KlH1WfjCs` 潮水音乐官方完整版 MV，1280×720，立体声 | `BV1LomdBBEye` 原版4K修复版，下载为 1280×720，立体声 | 选 B站修复版。画面比 YouTube 官方版更亮更满，且无底部歌词条；用全宽 `crop=1280:720:0:0`。 |
| 01 | 《心情卡片》 | `cPdCwAFJqM4` 潮水音乐官方完整版 MV，648×480，立体声 | `BV1T6VT6KEoE` SeedVR/DVD 修复版，1080×720，但左上有“拾光映画馆”水印 | 选 YouTube 官方 MV。B站修复版左上 UP 水印无法不伤主体地裁掉；官方低清但干净。用 `crop=648:340:0:0` 去掉底部歌词。 |

## 展示段窗口

| 排名 | 歌曲 | 竖屏 clip | 展示起点 | 展示时长 | 说明 |
| --- | --- | --- | ---: | ---: | --- |
| 05 | 《空出来的时间刚好拿来寂寞》 | `clips/vert_p5_kong.mp4` | 49.0s | 30s | 人声密集，人物/都市感更强，避开后段纯抽象画面。 |
| 04 | 《你应该飞的》 | `clips/vert_p4_fei.mp4` | 90.0s | 30s | 人声连续，画面无右侧标识。 |
| 03 | 《说谎》 | `clips/vert_p3_shuohuang.mp4` | 72.0s | 28s | Live 连唱段，特写和全景交替。 |
| 02 | 《下一个永远》 | `clips/vert_p2_xiayong.mp4` | 142.0s | 33s | 连续长人声段，保留电影感镜头。 |
| 01 | 《心情卡片》 | `clips/vert_p1_xinqing.mp4` | 177.5s | 32s | 连续高光段，裁后无歌词和水印。 |

## 搜索记录摘要

- YouTube 搜索命令使用 `yt-dlp --cookies sandbox/www.youtube.com_cookies.txt --flat-playlist`。
- B站搜索命令使用 `python3 tools/video/bili_search.py "<关键词>" 8`。
- B站下载使用 `python3 tools/video/bili_dl.py <bvid> <out.mp4> --max-h 720`；`BV1FQ7X6cERf` 1080P 候选曾因直链中断失败，改用同歌 `BV1KXVPz6EHH` 720P 候选。
