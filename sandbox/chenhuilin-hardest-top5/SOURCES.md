# Sources — 陈慧琳最难的5首歌

Cookie files checked:
- YouTube: `sandbox/www.youtube.com_cookies.txt`
- B站: `sandbox/www.bilibili.com_cookies.txt`

选源规则：每首都在 YouTube + B站两边搜候选，按清晰度 / 画面干净度（无烧词·台标·平台/UP水印）/ 立体声 / 可用连续副歌综合选。下载 probe 抽帧验证「是真动态 MV、不是静态专辑图」后再定窗。烧死歌词一律**全宽裁掉**（裁到歌词顶边以上），双人/多人/舞群一律 **letterbox 保原比例不放大**。

> ⚠️ 重要发现：官方频道「Kelly Chen 陳慧琳」上传的 **《失忆周末》《不如跳舞》是静态专辑图配音轨（整轨同一帧），不可用作 footage**；其《花花宇宙》《大日子》《谁愿放手》才是真动态 MV。
> ⚠️ B站「时光音乐阁」4K修复版（花花宇宙/大日子）带**间歇出现的 `bilibili 时光音乐阁` 顶右水印**，全宽裁不掉（间歇且在画面内），弃用；改用无水印的 weazegigi 1080P修复 / YT 官方源。

揭晓顺序：难度倒数 第5 → 第1（开头不剧透排名，片尾再列）。

## 5.《谁愿放手》（慢歌控制）
- YouTube：
  - `https://www.youtube.com/watch?v=Gt7eHAD6lwA` | 3:13 | Kelly Chen 陳慧琳（官方）| 640x480 stereo | 动态 MV，柔焦面部特写 | 底部烧死 KTV 歌词，**无平台/UP水印、无台标** → **选用**
- B站：
  - `BV1Woj1zfENq` | o小壞蛋 | 1920x1080 TVB版 | UP水印 + bilibili水印 + TVB台标 + 底部烧词 → 弃（太脏）
  - `BV1dDJbzzE3E` | 樱花色季节 | DVD MTV Karaoke 1080P60 | 大卡拉OK烧词 → 弃
  - `BV1J34y1C7WL` | AK老黄瓜 | 4K Live | AK老黄瓜移动水印 → 弃
- Final：YT 官方 `Gt7eHAD6lwA`。源切窗 96.2–156.2（展示副歌 116–154，情感最终副歌段），vfill crop `640:296:0:0`（裁掉底部烧词），letterbox。

## 4.《大日子》（喜庆快歌）
- YouTube：
  - `https://www.youtube.com/watch?v=fb-pFRwI1i4` | 4:23 | Kelly Chen 陳慧琳（官方）| 640x480 stereo | **干净动态 MV**（仅开头标题卡），无烧词无水印 → **选用**
- B站：
  - `BV17Y4y1D7o4` | 时光音乐阁 | 4K(2880x2160) Hires | 间歇 `bilibili 时光音乐阁` 顶右水印 + 底部烧词 → 弃（水印间歇在画面内裁不净）
  - `BV1JrJbz2EKN` | 樱花色季节 | DVD Karaoke | 烧词 → 弃
  - `BV1pr4y1G7nY` | 高视影坛 | 2008 演唱会 Live 4K | 版本不符（要棚拍 MV）→ 弃
- Final：YT 官方 `fb-pFRwI1i4`。源切窗 96.8–156.8（展示 116–154，红衣特写+跳舞副歌），无 crop（4:3 全幅干净），letterbox。SD 但全程干净，优于带水印 4K。

## 3.《不如跳舞》（国语舞曲，林夕词·雷颂德曲）
- YouTube：
  - `https://www.youtube.com/watch?v=JrCT-HokLG4` | 3:12 | Kelly Chen 陳慧琳（官方）| 1080x1080 | **静态专辑图**「飛吧 FLYING KELLY」配音轨 → 弃（非动态）
- B站：
  - `BV1p8Lu6BEvD` | 樱花色季节 | 1920x1080 官方 MV | 动态暗黑概念片，`上華 WHAT'S MUSIC` 厂牌 logo 顶左 + 底部烧词 → **选用**
  - `BV1rD4y1Q7YK` | 时光音乐阁 | 1440x1080 1080P修复 | `Liangion` UP水印顶左 + 偏暗 → 弃
- Final：B站 `BV1p8Lu6BEvD`。该曲官方 MV 本身就是暗调投影概念片，清晰本人镜头稀疏；选 84–122 段（红光下本人跳舞最清晰）。源切窗 64.47–124.47，vfill crop `1920:600:0:80`（裁顶部 上華 logo + 底部烧词），letterbox（画幅偏窄，源限制）。

## 2.《失忆周末》（密集咬字快歌）
- YouTube：
  - `https://www.youtube.com/watch?v=kSb7F9L15XA` | 3:11 | Kelly Chen 陳慧琳（官方）| 1080x1080 | **静态专辑图**配音轨 → 弃（非动态）
  - `https://www.youtube.com/watch?v=AxConCXyHR8` | 3:11 | 637 TWS | 960x720 | 动态棚拍 MV（蓝调舞台，背景 SAMSUNG LED 系 MV 固有布景）| 底部 2 行烧死 KTV 歌词 + 顶左小 logo → **选用**
- B站：
  - `BV1kv411379g` | AlfredSE | 1440x1080 修复 | 同 MV（Samsung 舞台版），底右烧词 → 备选
  - `BV1fCJbz5Em2` | 樱花色季节 | DVD Karaoke | 烧词 → 弃
- Final：YT `AxConCXyHR8`。源切窗 56.65–116.65（展示 76–114，密集副歌），vfill crop `960:345:0:40`（裁顶 logo + 底部 2 行烧词），letterbox（画幅偏窄，源限制）。背景 Samsung LED 属 MV 原始布景，非平台水印。

## 1.《花花宇宙》（压轴，电音舞曲女王代表作）
- YouTube：
  - `https://www.youtube.com/watch?v=WK9qq2k2_SM` | 3:51 | Kelly Chen 陳慧琳（官方）| 640x480 | 干净动态 MV，但仅 SD → 备选
- B站：
  - `BV1uG41177um` | weazegigi | 1080P修复 1920x1080(4:3 pillarbox) | **全程干净：无水印、无烧死歌词** → **选用**
  - `BV1jJ411h7bU` | 时光音乐阁 | 4K(3780x2160) | 间歇 `bilibili 时光音乐阁` 顶右水印 + 底部烧词 → 弃
  - `BV1bC5B6tEg8` | Vermilionazure | 4K | `Vermilionazure bilibili` 顶右水印 + 底部乱码字 → 弃
- Final：B站 `BV1uG41177um`（weazegigi 1080P修复）。源切窗 78.0–138.0（展示 98–136，本人 solo 特写 + 群舞），vfill crop `1440:1080:240:0`（去 pillarbox 黑边取干净 4:3 内容），letterbox。压轴选了**无水印的干净源**而非带水印 4K。

## 备注
- 这五首均为 2000–2001 年港台舞曲/慢歌，官方干净源普遍 SD/标清；4K「修复版」几乎都带平台/UP/修复者水印或烧词。按「干净度优先于分辨率」取舍，最终 huahua/buru 用 1080P，shiyi 用 960x720，darizi/shuiyuan 用 640x480 官方源。
- 所有 footage 竖屏化均 **letterbox 保原比例**（舞群/多人/暗调宽机位禁止竖裁放大）。
- footage 窗 == 音乐窗（同源同区间）→ 口型天然同步；展示段每首连续 38s 副歌。
