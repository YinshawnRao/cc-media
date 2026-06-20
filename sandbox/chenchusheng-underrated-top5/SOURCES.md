# 陈楚生最被低估的5首歌 — 选源记录

规则：每首同时查 YouTube + B站。最终按清晰度、画面干净度、音频质量、动态画面可用性和是否连续唱段综合选择。

## 候选与初选

### 第5名《先这样吧》

- YouTube: `https://www.youtube.com/watch?v=uwl6ySNzm_A` | 4:09 | C-Pop Library | `陈楚生 Chen Chusheng & SPY.C - 先这样吧 (Take It Easy) | 侦探C`
- B站: `BV18L411r7eW` | 4:42 | 陈楚生 | `【陈楚生放映室】《先这样吧》MiniLive春日营业`
- B站备选: `BV15o4y1a7Ww` | 4:02 | 瓶装汤 | 20230226长沙巡演 4K
- 初选：B站陈楚生账号 MiniLive。YouTube 候选更像专辑音频/静态源，B站是动态真人演唱；需 crop 去掉左上 `陈楚生 bilibili` 和底部歌词。

### 第4名《辩证关系》

- YouTube: `https://www.youtube.com/watch?v=ANUv9DdJJko` | 3:57 | C-Pop Library | `陈楚生 Chen Chusheng & SPY. C - 辩证关系 (Love&Money) | 侦探C`
- YouTube 备选: `https://www.youtube.com/watch?v=uM2L9oS9qA4` | 3:57 | lzxy | 单曲搬运
- B站: `BV1Ug411d7TX` | 3:49 | 陈楚生音乐馆 | `陈楚生《辩证关系》——多喜欢现在的自己 就多少无可奈何在心底`
- B站备选: `BV1Px411s7dg` | 89:50 | 2017 livehouse 西安站全纪录
- 初选：B站陈楚生音乐馆单曲视频。实际抽帧确认是动态户外 Live，不是静态图；需 crop 去掉黑边和中英字幕。

### 第3名《35》

- YouTube: `https://www.youtube.com/watch?v=H_WiwCkUI5s` | 3:51 | 陈楚生 | `陈楚生 & SPY.C首支独立单曲《35》现场版MV`
- YouTube 备选: `https://www.youtube.com/watch?v=xwR3OlQ-zYE` | 3:29 | lzxy | 《侦探C》MV
- B站: `BV1QG4y1e7pr` | 3:51 | 陈楚生音乐馆 | `陈楚生《35》官方MV`
- B站备选: `BV1bs411s71f` | 3:51 | 搬运超清 MV
- 初选：YouTube 陈楚生官方频道 1080p。画面为黑白现场版 MV，动态和清晰度最好；需 crop 去底部歌名/Logo。

### 第2名《追风筝的孩子》

- YouTube: `https://www.youtube.com/watch?v=Uh-AIabODdc` | 4:16 | ccs19810725 | 2011新专辑预听
- YouTube 备选: `https://www.youtube.com/watch?v=BPU88CYCEtw` | 5:58 | lzxy | 七分之一音乐会 Live
- B站: `BV1jY411c7bo` | 5:58 | 陈楚生音乐馆 | `陈楚生《追风筝的孩子》七分之一音乐会`
- B站备选: `BV1ta411f7TL` | 4:42 | 陈楚生音乐馆 | 2011围炉音乐会
- 初选：B站七分之一音乐会。YouTube 搜索前列有预听音频，B站候选是动态 Live；720p 下载中断，降至 480p 成功，音频 321kbps。

### 第1名《一个人唱情歌》

- YouTube: `https://www.youtube.com/watch?v=sTard_naFdQ` | 3:50 | 陈楚生 - Topic | Topic 音频
- YouTube 备选: `https://www.youtube.com/watch?v=5RH7eBxBAvA` | 3:58 | Jomia1130 | Sina 录制
- B站: `BV12d4y1T7nT` | 4:17 | 陈楚生音乐馆 | `陈楚生《一个人唱情歌》官方MV`
- B站备选: `BV138411z7Sq` | 3:59 | 瓶装汤 | 20230826北京“棱”演唱会
- 初选：B站官方 MV。YouTube 官方 Topic 是静态音频，B站有动态官方 MV；1080p 下载中断，720p 成功。

## 已下载初选源

| 歌曲 | 文件 | 规格 | 说明 |
|---|---|---|---|
| 先这样吧 | `raw/xianzheyangba_bili_minilive.mp4` | 1280x720, 25fps | MiniLive，左上水印和底部歌词需 crop |
| 辩证关系 | `raw/bianzhengguanxi_bili_musicguan.mp4` | 1440x720, 30fps | 动态户外 Live，黑边和字幕需 crop |
| 35 | `raw/35_yt_official.mp4` | 1920x1080, 29.97fps | 官方频道现场版 MV，底部歌名/Logo需 crop |
| 追风筝的孩子 | `raw/zhuifengzheng_bili_live.mp4` | 852x480, 25fps | Live，低清但音频 321kbps，需裁黑边/字幕 |
| 一个人唱情歌 | `raw/yigeren_bili_official.mp4` | 1276x720, 30fps | 官方 MV，底部歌词需 crop |

## 已验证窗口

| 歌曲 | 源文件 | 预切窗口 | 竖屏 crop | 展示说明 |
|---|---|---:|---|---|
| 先这样吧 | `raw/xianzheyangba_bili_minilive.mp4` | 01:45 起 74s | `1280:560:0:60` | 去掉左上 `陈楚生 bilibili` 与底部歌词；舞台屏幕内歌词仍属于源画面 |
| 辩证关系 | `raw/bianzhengguanxi_bili_musicguan.mp4` | 02:08 起 74s | `960:520:240:40` | 中裁放大人物，去黑边/字幕，主体未被裁 |
| 35 | `raw/35_yt_official.mp4` | 00:45 起 74s | `1920:880:0:0` | 1080p 黑白现场版 MV，裁掉底部歌名/Logo |
| 追风筝的孩子 | `raw/zhuifengzheng_bili_live.mp4` | 02:30 起 76s | `852:330:0:45` | 裁掉黑边/字幕；源为 480p，但音频码率高且连续演唱 |
| 一个人唱情歌 | `raw/yigeren_bili_official.mp4` | 01:10 起 78s | `1276:600:0:0` | 裁掉底部歌词，保留官方 MV 动态画面 |
