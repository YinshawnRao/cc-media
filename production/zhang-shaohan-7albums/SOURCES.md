# 张韶涵前7张专辑·素材源 — 已定稿（含抽帧验证 + crop 策略）

## 关键事实（probe 阶段抽帧验证后确认）
**6 / 7 首歌曲的 MV master 自带烧死繁体歌词条**（约 y=920-1060，140px 高），这是 2004-2012 年福茂/华研发行版的常态。不是修复 UP 加的。
唯一例外：#03 《保护色》（離島-Ernest 1080P重新修复 BV1qp4y1a7zX）已做 caption 清除处理。

#05 《能不能勇敢说爱》歌词为左侧竖排（x≈0-150），9:16 中心 crop 自然排除。

## 最终选择 + crop 策略

| # | 歌 | 源 | 规格 | crop（输入 1080P 源） |
|---|---|---|---|---|
| 01 | 天边 | B站 BV1344y1W7Hq (舒言星 4K修复) | 1080P AVC 30000/1001 stereo 191k | crop bottom 160 → 1920×920 |
| 02 | 浮云 | B站 BV1uY4y1V7bQ (舒言星 4K修复) | 1080P AVC 30000/1001 stereo 191k | crop bottom 160 → 1920×920 |
| 03 | 保护色 | B站 BV1qp4y1a7zX (離島-Ernest 1080P重新修复) | 1080P AVC 25fps stereo 130k | 无 crop（clean）→ 1920×1080 |
| 04 | 寻宝 | B站 BV1wb411C7j2 (台湾金曲奖吧官频) | 1080P AVC 30fps stereo 167k | crop bottom 160 → 1920×920；侧黑边可能存在，vfill 中处理 |
| 05 | 能不能勇敢说爱 | B站 BV1cb411C7oD (台湾金曲奖吧官频) | 1080P AVC 30fps stereo 167k | 左侧竖排歌词由 9:16 中心 crop 自然排除；可加 crop left 160 防中心偏 |
| 06 | 偶尔 | B站 BV1BJykYKEP5 (舒言星 4K修复) | 1080P AVC 30fps stereo 208k；**4:3 letterboxed**（左右 240px 黑边） | crop center 1440×920（240..1680 横向 + 0..920 竖向，去左右黑边和底部歌词） |
| 07 | 是我 | YouTube yLiz3PWeKU0 (本人官频 张韶涵Angela Zhang) | 1920×1080 24fps AVC stereo 129k | crop bottom 160 → 1920×920 |

## yt-dlp 命令（实战）
B站 1080P AVC stereo（30112 是 1080P 高码率 AVC；30280 是 m4a 192k）：
```bash
python3 ../../tools/video/yt_dlp_readonly.py -- \
  --download-sections "*HH:MM:SS-HH:MM:SS" \
  -f "30112+30280/30080+30280" \
  "https://www.bilibili.com/video/<BVID>" \
  -o "raw/song_<NN>.%(ext)s"
```
YouTube #07：
```bash
python3 ../../tools/video/yt_dlp_readonly.py -- \
  --download-sections "*HH:MM:SS-HH:MM:SS" \
  -f "137+140" \
  "https://www.youtube.com/watch?v=yLiz3PWeKU0" \
  -o "raw/song_07.%(ext)s"
```

## 副歌段位置（待用户耳朵确认；本草案凭 MV 时长结构粗估）
| # | 歌 | 段时长 | 副歌候选段 (HH:MM:SS) |
|---|---|---|---|
| 01 | 天边 (4:12) | 0:50 cut | 01:30 - 02:20 |
| 02 | 浮云 (4:50) | 0:55 cut | 01:50 - 02:45 |
| 03 | 保护色 (3:46) | 0:50 cut | 01:20 - 02:10 |
| 04 | 寻宝 (3:29) | 0:50 cut | 01:00 - 01:50 |
| 05 | 能不能勇敢说爱 (4:02) | 0:50 cut | 01:25 - 02:15 |
| 06 | 偶尔 (4:42) | 0:55 cut | 02:00 - 02:55 |
| 07 | 是我 (4:33) | 0:50 cut | 01:50 - 02:40 |

每段比片内"展示段时长 18-25s"留宽 25s 余量供 swell/lead 选段。
