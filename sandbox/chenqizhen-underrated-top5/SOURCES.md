# 陈绮贞最被低估的5首歌 — 选源记录

规则：每首同时查 YouTube + B站。最终优先选择官方 MV / 官方上传，若 B站修复版画质更高但带平台/UP 主水印、烧死字幕或非官方重调色，默认退回干净官方源。

## 当前结论

本期五首在 YouTube 均找到官方 MV 或官方上传源；B站也都有候选。初选全用 YouTube 官方源，理由是无平台水印、来源清晰、音画更可控。后续下载后会抽帧确认是否有烧死字幕/片头片尾水印。

## 候选

### 第5名《距离》

- YouTube: `https://www.youtube.com/watch?v=vGIgU9Xaawg` | 3:52 | 添翼音樂 TEAM EAR MUSIC | `陳綺貞 Cheer Chen 【距離 Distance】 Official Music Video`
- YouTube 备选: `https://www.youtube.com/watch?v=a08Ovz8vqA0` | 3:32 | 陳綺貞 cheerego com | 太阳巡回演唱会 Live
- B站: `BV1NG411t72q` | 3:53 | 666111777 | 4K修复 MV
- B站备选: `BV18i4y1E7CJ` | 3:53 | 驰放音乐分享 | Official Music Video MV
- 初选：YouTube 官方 MV。B站修复版待抽帧，如含修复水印/上传者标识则不用。

### 第4名《太聪明》

- YouTube: `https://www.youtube.com/watch?v=33rdx577PxY` | 4:35 | 滾石唱片 ROCK RECORDS | Official Music Video
- YouTube 备选: `https://www.youtube.com/watch?v=aCdi3C5L8ww` | 6:09 | 老邦菜 | 4K修复 Live
- B站: `BV1sDx1eoEMw` | 4:19 | 香港乐坛Live王 | 4K60FPS Live
- B站备选: `BV1Um4y1q7ER` | 6:10 | 超爱大可乐 | 4K修复 Live
- 初选：YouTube 滚石官方 MV。Live 版画质可能高，但本期优先官方 MV 和音画干净度。

### 第3名《躺在你的衣柜》

- YouTube: `https://www.youtube.com/watch?v=BPNXyVzJjtw` | 5:03 | 滾石唱片 ROCK RECORDS | Official Music Video
- YouTube 备选: `https://www.youtube.com/watch?v=2MTCYtab-RY` | 5:04 | 2013 Live
- B站: `BV1jP4y1K7Cw` | 5:03 | 不问上下问逻辑 | MV
- B站备选: `BV1Gh411u7kC` | 4:57 | 2011 夏季练习曲现场版
- 初选调整：用 YouTube 2013 Live。官方 MV 的长人声段落在片尾黑底字幕，画面不适合展示；2013 Live 是稳定单主体演唱，原画面右下有 `yoyo` 水印，最终采用中间竖裁 `760:960:580:0` 去掉水印并保留主体。

### 第2名《80%完美的日子》

- YouTube: `https://www.youtube.com/watch?v=h3Rdw_NOQ3s` | 4:36 | 添翼音樂 TEAM EAR MUSIC | Official Music Video
- YouTube 备选: `https://www.youtube.com/watch?v=sjIE3g9AS-c` | 4:41 | 2011 贡寮国际海洋音乐祭
- B站: `BV1pW411B76A` | 4:36 | 莫呼洛迦 | Official Music Video
- B站备选: `BV1hmxEzWEEo` | 3:12 | 音乐房子_live | 广州超级草莓 Live
- 初选：YouTube 添翼官方 HD MV。

### 第1名《腐朽》

- YouTube: `https://www.youtube.com/watch?v=Pw9jk8eAg54` | 4:08 | 添翼音樂 TEAM EAR MUSIC | Official Music Video
- YouTube 备选: `https://www.youtube.com/watch?v=Fnd_UJn6XlA` | 4:13 | 添翼音樂 TEAM EAR MUSIC | 太阳巡回演唱会 Live
- B站: `BV1G14y1E7Rq` | 3:59 | 音乐筱禄君 | 4K重温经典
- B站备选: `BV1sRcPe1Epg` | 4:08 | pioneerunicorn | 4K修复官方 MV，重新调色自制字幕版
- 初选：YouTube 添翼官方 HD MV。B站 4K修复标题含“自制字幕版”，若有烧死字幕则不适合成片。

## 待验证

- 下载 5 条 YouTube 官方源 + 《躺在你的衣柜》YouTube 2013 Live 备选。
- `ffprobe` 记录分辨率、音轨声道。
- 抽 1s / 中段 / 副歌附近帧确认：无平台水印、无网址、无明显烧死字幕。
- 选每首 55-65s 连续展示窗口，确保旁白后 full-music 段正在唱。

## 已验证窗口

| 歌曲 | 源 | 窗口 | crop | 说明 |
|---|---|---:|---|---|
| 距离 | YouTube 官方 MV | 01:05 起 64s | `1440:900:0:0` | full-music 对齐 83.9–119.6s 长人声段，裁底部歌词 |
| 太聪明 | YouTube 滚石官方 MV | 02:33 起 64s | `640:400:0:0` | full-music 对齐 171.8–195.9s 人声段，裁底部歌词 |
| 躺在你的衣柜 | YouTube 2013 Live | 02:51.5 起 64s | `760:960:580:0` | 单主体稳定竖裁，裁掉右下 `yoyo` 水印 |
| 80%完美的日子 | YouTube 添翼官方 MV | 00:57 起 64s | `1920:1080:0:0` | 官方 MV 无明显水印；连续唱段较短，展示段收至 25s |
| 腐朽 | YouTube 添翼官方 MV | 02:13 起 64s | `1920:1080:0:0` | full-music 对齐 154.7–186.7s 长人声段 |
