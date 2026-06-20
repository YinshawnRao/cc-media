# 童安格最被低估的5首歌 — 选源记录

原则：每首同时查 YouTube 和 B站，按清晰度、画面干净度、立体声、版本质量综合选择。最终成片不保留平台水印、UP 主水印、网址、路径或提示词。

## 搜索记录摘要

| 排名 | 歌曲 | YouTube 候选 | B站候选 | 初步判断 |
| --- | --- | --- | --- | --- |
| 05 | 《整个世界只留下一盏灯》 | `Q33MapcmyAs` Angus Tung - Topic；`8sytkhwqjIU` 用户音频 | `BV1Pw411A7FC` 专辑合辑；`BV15w411L7Ce` 单曲音频 | 暂以 YouTube Topic 官方音频为保底，若 B站合辑画面干净再比较。 |
| 04 | 《水中的颜》 | `ThFNrg0jUgk` / `0P4voLOMnvQ` Angus Tung - Topic；`e-EolqoU4Jo` 用户上传 | `BV1iz4y1B79T`、`BV1YLa9e5Eti`、`BV1A5411M7b5` 用户上传；演唱会合集候选 | 暂以 YouTube Topic 官方音频为保底，B站看是否有动态/现场可用。 |
| 03 | 《陪你到天亮》 | `JGwvbGiIl5Y` UNIVERSAL MUSIC TAIWAN Official Video；`vz9gxRE2Iro` Topic | `BV1ri42127aK` 1080P 卡拉OK；`BV1mV411m79X` 环球音乐中国 | 优先比较 YouTube 官方 MV 与 B站环球/卡拉OK，选更干净的一边。 |
| 02 | 《等我一起入梦》 | `ZMUmHRe5RVE` 童安格主题；`ymtGD2plWcc` Topic；`bmrTd8dBRsc` 歌词版 | `BV116bmzaEPy` 经典MV；`BV1GS411w7Y1` LD采集 | 优先下载 B站经典MV/LD 抽帧，若有水印再退回 YouTube Topic。 |
| 01 | 《你我的爱只能擦肩而过》 | `4IOuSzSfcJk` Angus Tung - Topic；`3iwI5o0PlKY` 主题；`72lJjC_0Ydo` 歌词版 | `BV18xhxzJEbm` 经典MV；`BV1cQ4y1u78Z` 赏析；演唱会合集候选 | 优先下载 B站经典MV 抽帧，若有水印/歌词无法裁掉则退回 Topic。 |

## 最终选源

| 排名 | 歌曲 | 最终素材 | 裁切 / 处理 | 选择原因 |
| --- | --- | --- | --- | --- |
| 05 | 《整个世界只留下一盏灯》 | YouTube `Q33MapcmyAs` Angus Tung - Topic | `clips/vert_p5_lamp.mp4`，`crop=1080:1080:0:0` | B站单曲候选 `BV15w411L7Ce` 文件过大且下载预计十几分钟以上；YouTube Topic 为官方音频保底，画面为干净封面源，无平台水印。初版 231s 段落偏尾奏/背景声，已重切到 180s 起的人声演唱段。 |
| 04 | 《水中的颜》 | B站 `BV1iz4y1B79T` | `clips/vert_p4_water.mp4`，`crop=1280:560:0:55` | YouTube Topic 只有封面/音频；B站候选有动态画面。裁掉顶部黄色标识和底部歌词后可用，但画面偏暗。 |
| 03 | 《陪你到天亮》 | YouTube `JGwvbGiIl5Y` UNIVERSAL MUSIC TAIWAN Official Video | `clips/vert_p3_dawn.mp4`，`crop=654:390:0:0` | 官方 MV，画面干净度优先；底部歌词带通过裁底去掉。 |
| 02 | 《等我一起入梦》 | B站 `BV116bmzaEPy` 经典MV | `clips/vert_p2_dream.mp4`，最终 `crop=1440:610:240:130` | B站有动态 MV，优于 Topic 静态源。第一次裁切残留顶部 B站/UP 标识，重裁后抽帧确认干净。 |
| 01 | 《你我的爱只能擦肩而过》 | B站 `BV18xhxzJEbm` 经典MV | `clips/vert_p1_passby.mp4`，最终 `crop=1440:580:240:150` | B站有动态 MV，优于 Topic 静态源。第一次裁切残留顶部 B站/UP 标识，重裁后抽帧确认干净；238-250s 左右可见 MV 场景内英文招牌，不是平台/UP 主水印。 |

## 展示段窗口

| 排名 | 歌曲 | 预切片段 | source seek | full-music 起点 | 展示时长 | 人声检查 |
| --- | --- | --- | ---: | ---: | ---: | --- |
| 05 | 《整个世界只留下一盏灯》 | `clips_seg/p5_lamp.mp4` | 161.075s | 18.925s | 30s | 重切后源时间 180.0s 起进入演唱；`probe/asr/p5_show_new_180_210.txt` 与最终 MP4 的 `probe/asr/final_p5_show_fixed.txt` 均识别到“只留下一盏灯 / 让我看到的你 / 是不再委屈的眼神 / 整个世界只留下一盏灯”。 |
| 04 | 《水中的颜》 | `clips_seg/p4_water.mp4` | 187.550s | 16.650s | 25s | 重对齐后 14.93-35.22 连续人声段覆盖 full-music 起点。 |
| 03 | 《陪你到天亮》 | `clips_seg/p3_dawn.mp4` | 203.300s | 15.200s | 30s | 重对齐后 15.26-21.80 人声段覆盖 full-music 起点；后续为慢歌断句型。 |
| 02 | 《等我一起入梦》 | `clips_seg/p2_dream.mp4` | 239.950s | 18.050s | 38s | 慢歌断句型，full-music 附近有短空档，21.48s 后持续进入多段唱句。 |
| 01 | 《你我的爱只能擦肩而过》 | `clips_seg/p1_passby.mp4` | 165.425s | 18.075s | 40s | 14.35-21.55 人声段覆盖 full-music 起点，后续多段唱句延续。 |
