# 徐怀钰最难的5首歌 - 素材来源记录

检查日期：2026-06-07

Cookie 状态：
- YouTube: `sandbox/www.youtube.com_cookies.txt` 可用，`yt-dlp` 登录态探测为 `LOGGED_IN=true`。
- B站：`sandbox/www.bilibili.com_cookies.txt` 可用，接口登录态探测为 `isLogin=true`。

## 双平台候选与取舍

| 排名 | 歌曲 | YouTube 候选 | B站候选 | 最终选择 | 取舍原因 |
| --- | --- | --- | --- | --- | --- |
| 05 | 《妙妙妙》 | `34hd2867q8s`，官方 MV，640x480 | `BV1r54y1e7fU`，1080P 修复 MV | B站 `BV1r54y1e7fU` | B站清晰度更高，画面干净，适合竖屏裁切。 |
| 04 | 《心中的遗憾》 | `Sa9Nq-jzzR8`，1440x1080 | `BV1jfE7zrEPj`，超清 4K 修复 MV | B站 `BV1jfE7zrEPj` | YouTube 候选有烧词；B站源经横带 crop 后干净。 |
| 03 | 《分飞》 | `LJ1_NNl700s`，官方 MV，高分辨率 | `BV1Nt4y167vy`，4K 修复 | YouTube `LJ1_NNl700s` | YouTube 官方源更稳，裁切后无明显歌词/水印干扰。 |
| 02 | 《Call Me》 | `j5gqFMwUV9s`，官方 MV，640x480 | `BV1gh4y147d5`，1080P 修复 MV | B站 `BV1gh4y147d5` | B站画质明显更好，主体更适合竖屏展示。 |
| 01 | 《飞起来》 | `mV5YweJzb48`，官方 MV，1440x1080 | `BV1dg4y1B7cg`，1080P 修复 | YouTube `mV5YweJzb48` | YouTube 官方源画面质量和稳定性更好。 |

## 最终剪辑窗口

| 排名 | 歌曲 | 原始文件 | 窗口 | 竖屏处理 |
| --- | --- | --- | --- | --- |
| 05 | 《妙妙妙》 | `raw/p5_miaomiao_bi.mp4` | `00:00:25-00:01:13` | `tools/video/vfill.sh`，crop `1280:780:0:0` |
| 04 | 《心中的遗憾》 | `raw/p4_yihan_bi.mp4` | `00:01:09-00:01:59` | `tools/video/vfill.sh`，crop `1920:880:0:170` |
| 03 | 《分飞》 | `raw/p3_fenfei_yt.mp4` | `00:00:50-00:01:38` | `tools/video/vfill.sh`，crop `1440:800:0:0` |
| 02 | 《Call Me》 | `raw/p2_callme_bi.mp4` | `00:00:42-00:01:30` | `tools/video/vfill.sh`，crop `1920:1080:0:0` |
| 01 | 《飞起来》 | `raw/p1_feilai_yt.mp4` | `00:00:35-00:01:29` | `tools/video/vfill.sh`，crop `1440:900:0:0` |

## QA 证据

- 素材对比图：`qa/probe_compare.jpg`
- 最终素材抽帧：`qa/final_clip_contact.jpg`
- 最终成片 20 帧总览：`qa/final_frames/contact_20.jpg`
- 最终成片 9 帧大图：`qa/final_frames/contact_9.jpg`
- `qa/yihan_bi_check2.jpg` 用于确认《心中的遗憾》替换为 B站裁切源后无明显烧词/UP 主水印。

最终抽帧未发现平台水印、网址、路径、提示词泄漏；片头未提前列出完整排名，片尾完整回顾排名。
