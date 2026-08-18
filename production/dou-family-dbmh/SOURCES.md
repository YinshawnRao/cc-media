# SOURCES — dou-family-dbmh

成片：《一家三口，同唱一首歌：窦唯、王菲、窦靖童与 Don't Break My Heart》  
4:49 / 1080×1920 / 30 fps / H.264 + AAC

## 三条源素材

| 章节 | 用途 | 平台 | URL / ID | 时长 | 分辨率 / 编码 |
|---|---|---|---|---|---|
| Ch1 窦唯·原点 | 黑豹乐队官方 MV | YouTube | `WLUbs0rCQlI` | 5:09 (309s) | 640×480 AV1 + Opus stereo（90s 老 MV 上限） |
| Ch2 王菲·回声 | 1999 唱游大世界 日本武道馆 | B站 | `BV1PG411d71n` | 4:14 (254s) | 1920×1080 AV1 + AAC stereo（4K 流为 mono，故选 1080P） |
| Ch3 窦靖童·接住 | 《歌手 2026》舞台纯享 | YouTube | `T-HqusHa9eY` | 4:26 (266s) | 1920×1080 AV1 + Opus stereo |

## yt-dlp 重新下载命令

```bash
# 窦唯
python3 ../../tools/video/yt_dlp_readonly.py -- \
  -f "bv*[height<=1080]+ba/b[height<=1080]" --merge-output-format mp4 \
  -o "raw/douwei_heibao.%(ext)s" \
  "https://www.youtube.com/watch?v=WLUbs0rCQlI"

# 王菲（B站，需 bilibili cookie）
python3 ../../tools/video/yt_dlp_readonly.py -- \
  -f "bv*[height<=1080]+ba/b[height<=1080]" --merge-output-format mp4 \
  -o "raw/faye_budokan.%(ext)s" \
  "https://www.bilibili.com/video/BV1PG411d71n/"

# 窦靖童
python3 ../../tools/video/yt_dlp_readonly.py -- \
  -f "bv*[height<=1080]+ba/b[height<=1080]" --merge-output-format mp4 \
  -o "raw/jingtong_singer2026.%(ext)s" \
  "https://www.youtube.com/watch?v=T-HqusHa9eY"
```

## 竖屏 vfill 参数（crop W:H:X:Y｜brightness｜saturation）

| 源 | crop | BR | SAT | 备注 |
|---|---|---|---|---|
| `douwei_heibao.mp4` | `384:400:128:0` | -0.18 | 1.08 | 640×480 老 MV，顶对齐裁掉底部繁体歌词条 |
| `faye_budokan.mp4` | `1280:900:320:0` | -0.32 | 1.04 | 1080P，顶对齐裁掉底部"pioneerunicorn"水印 + 烧死中英歌词 |
| `jingtong_singer2026.mp4` | `1280:900:320:90` | -0.30 | 1.04 | 1080P，中心 4:5 crop 切掉右上"芒果TV 会员尊享" + 左上 logo + 底部烧死歌词 |

```bash
bash tools/video/vfill.sh raw/douwei_heibao.mp4    clips/vert_douwei_full.mp4    "384:400:128:0"   "-0.18" "1.08"
bash tools/video/vfill.sh raw/faye_budokan.mp4     clips/vert_faye_full.mp4      "1280:900:320:0"  "-0.32" "1.04"
bash tools/video/vfill.sh raw/jingtong_singer2026.mp4 clips/vert_jingtong_full.mp4 "1280:900:320:90" "-0.30" "1.04"
```

## Sub-clip 切片表（成片实际用窗口）

| 用途 | 源 vert | 起点 (s) | 时长 (s) | 终点 (s) |
|---|---|---|---|---|
| cold open – dw_open | vert_douwei | 135 | 4 | 139 |
| cold open – fw_open | vert_faye | 100 | 4 | 104 |
| cold open – jt_open | vert_jingtong | 215 | 4 | 219 |
| ch1 主 footage – dw_main | vert_douwei | 125 | 50 | 175 |
| ch2 主 footage – fw_main | vert_faye | 85 | 60 | 145 |
| ch3 主 footage – jt_main | vert_jingtong | 195 | 50 | 245 |
| three-up – dw_three | vert_douwei | 130 | 43 | 173 |
| three-up – fw_three | vert_faye | 86 | 43 | 129 |
| three-up – jt_three | vert_jingtong | 195 | 43 | 238 |

切片命令（stream copy，秒级）：
```bash
ffmpeg -y -ss <START> -i clips/vert_<NAME>_full.mp4 -t <DUR> -c copy clips/clip_<USE>.mp4
```

## Cover 静帧定位

| 卡片 | 源 | 时间码 | crop |
|---|---|---|---|
| 窦唯（暗红黑金调） | `raw/douwei_heibao.mp4` | **t=135**（band performance 长发侧脸唱）| `640:420:0:0` |
| 王菲（冷白蓝灰调，最大）| `raw/faye_budokan.mp4` | **t=165**（闭眼侧脸入歌） | `1280:900:320:0` |
| 窦靖童（蓝紫雾白调） | `raw/jingtong_singer2026.mp4` | **t=237**（嘴贴麦特写） | `1280:900:320:90` |

> **AV1 输入侧 seek 不准**——抽 cover 帧必须用 output-side seek：  
> `ffmpeg -i raw.mp4 -ss <T> -frames:v 1 -q:v 2 out.jpg`（`-ss` 放 `-i` 之后）。

## 时间线总览（V5 终版）

| 段 | t 起 | t 止 | 时长 | 内容 |
|---|---|---|---|---|
| cover | 0 | 5.5 | 5.5s | 三时代卡片 + 时间线 SVG path 绘制 + 主标题 |
| open3 | 5.5 | 15.5 | 10s | 冷开场三连切 + 1.9s 三人冻结 |
| title | 15.5 | 29.5 | 14s | 年份带 + "一首歌 / 三个人 / 三段回声" |
| ch1 | 29.5 | 76.5 | 47s | 窦唯主章 |
| trans1 | 76.5 | 89.5 | 13s | "几年后，它换了一个声音继续往前。" |
| ch2 | 89.5 | 143.5 | 54s | 王菲主章 |
| trans2 | 143.5 | 156.5 | 13s | "再后来，女儿也唱起了这首歌。" |
| ch3 | 156.5 | 203.5 | 47s | 窦靖童主章 |
| three | 203.5 | 246.5 | 43s | 三人同屏 + 接力 |
| outro | 246.5 | 276.5 | 30s | 三段 footage crossfade montage + hero |
| cta | 276.5 | 289.5 | 13s | "你最喜欢，哪一个版本？" + 素材出处 |
