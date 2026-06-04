# 《孙楠〈拯救〉Live完成度TOP5》素材来源记录

本项目只做本地测试样片，不对外发布、不商用。若后续发布，需要按平台和节目版权另行做授权评估。

## 最终采用素材

| 段落 | 版本 | 采用源 | 本地文件 | 选择理由 |
| --- | --- | --- | --- | --- |
| TOP5 | 《中国之星》版 | B站：<https://www.bilibili.com/video/BV1Ds4y127wG> | `raw/top5_chinastar.mp4` | 1080p，节目纯净度和音频质量可用，适合呈现竞演编曲层次。 |
| TOP4 | 2002第四届中韩歌会 | B站：<https://www.bilibili.com/video/BV1cg4y167xm> | `raw/top4_korea2002.mp4` | 明确对应第四届中韩歌会，画面虽有年代感但声音穿透力突出。 |
| TOP3 | 2003现场版 | B站：<https://www.bilibili.com/video/BV1wEMDzQEB5> | `raw/top3_changchun2003.mp4` | 2003长春演唱会修复版，清晰度和音频质量优于多数搬运，避免与第四届中韩歌会重复。 |
| TOP2 | 《歌手2024》第四期直播版 | B站：<https://www.bilibili.com/video/BV1J1421C75g> | `raw/top2_singer2024.mp4` | 节目纯净版，1080p，适合呈现直播竞演压力和55岁现场状态。 |
| TOP1 | 第五届中韩歌会原Key版 | B站：<https://www.bilibili.com/video/BV1QJ411d7Hg> | `raw/top1_korea5_originalkey.mp4` | 明确标注第五届中韩歌会原Key，版本指向最准确；画质低于现代节目但音频可用。 |

## 双平台检索结论

按仓库规范，对每条素材同时查找了 YouTube 和 B站。B站对这几版历史现场的命中更完整，尤其是第四届、第五届中韩歌会和2003现场；YouTube 检索到的结果多为非目标版本、片段/循环搬运或节目合集，不优先采用。

检索到但未采用的 YouTube 方向包括：

- MangoTV / 《歌手2024》相关循环或节目内容：<https://www.youtube.com/watch?v=HriKEaMDlXg>
- 四川卫视《围炉音乐会》版：<https://www.youtube.com/watch?v=n8MU7oO6LHU>
- 《全能星战》等非目标版本：<https://www.youtube.com/watch?v=3OwSJQsrs4o>
- 其它泛标题 `Zheng Jiu Live` / `拯救 Live` 结果，版本对应关系不如最终 B站源清晰。

## 成片处理说明

- 竖屏画面由 FFmpeg 预处理为 `clips/*.mp4`，优先保留演唱者和舞台主体。
- 个别历史源存在台标、烧录字幕或平台标识，已尽量通过裁切、遮罩和深色舞台框降低干扰。
- 配音使用本地 Kokoro 中文 TTS `zm_yunxi`；最终音轨为 `master.wav`，再后期 mux 到 MP4，避免 HyperFrames 直接渲染压平动态。
- 排名表达为本期按演唱完成度、现场状态与社区讨论综合判断，不作为绝对权威结论。

## 2026-06-03 副歌入口修订

本次按“每段正式展示入口正好进入副歌”重新对齐素材窗口。旁白阶段允许保留副歌前铺垫，进入 full-volume 展示段时落在以下原片时间点：

| 段落 | 原片副歌入口 | 竖屏素材起点 | 展示段时长 |
| --- | ---: | ---: | ---: |
| TOP5《中国之星》版 | 240.0s | 226.575s | 45.0s |
| TOP4 2002第四届中韩歌会 | 126.0s | 112.425s | 45.0s |
| TOP3 2003现场版 | 120.0s | 105.525s | 45.0s |
| TOP2《歌手2024》直播版 | 243.0s | 224.25s | 45.0s |
| TOP1 第五届中韩歌会原Key版 | 238.0s | 219.475s | 35.0s |

TOP1 原始素材总长约 273.1s，展示段已尽量保留到可用片尾；其他版本展示段均拉长为连续副歌段。
