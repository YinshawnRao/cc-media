# 素材来源与取舍

## 总原则

按仓库约束，每首都查 YouTube 与 B站候选，优先级为：清晰度、画面干净度、立体声、版本质量、是否能切出连续可用段。最终下载和校验均使用仓库根目录 `all_cookies.txt`，没有在 `sandbox/` 下复制 cookie。

## 第 5 名：《爱深过做人》

- YouTube 候选：`mVWs1zwJUjI`，AMusic Official Channel，`衛蘭 Janice - 愛深過做人 Official MV [Serving You] - 官方完整版`，640x480，立体声。
- B站候选：`BV1ep4y147SF`，标题为 `※CC字幕※ 衛蘭 - 愛深過做人 (Official Video)`；另有卫兰官方 MV 合集 `BV1Zx411L7n4`。
- 取舍：YouTube 为 AMusic 官方 MV，来源最稳；B站候选主要为搬运/合集。最终选 YouTube 官方 MV。画面本身为老 MV 小画幅嵌入式构图，竖屏时保守裁切，不强行放大。
- 本地文件：`raw/p5_aishenguozuoren.mp4` -> `clips/vert_aishenguozuoren.mp4`。

## 第 4 名：《他不惯被爱》

- YouTube 候选：`vdQwelLMh0U`，AMusic Official Channel，`衛蘭 Janice - 他不慣被愛 Official MV [Imagine] - 官方完整版`，1280x720，立体声。
- B站候选：`BV1bx411i7Ks`，标题为 `他不惯被爱 - 卫兰 音乐 MV 【1080P】【粤语】`；另有搬运 `BV1es411o7Ez` 与 MV 合集。
- 取舍：YouTube AMusic 官方 MV 清晰度、来源和音频更可靠。最终选 YouTube 官方 MV。
- 本地文件：`raw/p4_tabuguanbeiai.mp4` -> `clips/vert_tabuguanbeiai.mp4`。

## 第 3 名：《爱没有假如》

- YouTube 候选：`XpUlHSPopOI`，AMusic Official Channel，`衛蘭 Janice - 愛沒有假如 Official MV [Imagine] - 官方完整版`，600x480，立体声。
- B站候选：`BV1Rd4y157ru`，标题为 `衛蘭 Janice - 愛沒有假如 Official MV`；另有 Live 与 MV 合集。
- 取舍：YouTube AMusic 官方 MV 与 B站搬运内容接近，最终选 YouTube 官方 MV，音视频完整且无平台水印。
- 本地文件：`raw/p3_aimyoujiashe.mp4` -> `clips/vert_aimyoujiashe.mp4`。

## 第 2 名：《杂技》

- YouTube 候选：`5sYkIDYNz1Y`，AMusic Official Channel，`衛蘭 - 雜技 MV`，600x480，立体声。
- B站候选：`BV1TYwmeCEZf`，amusic_official，`卫兰 - 杂技 MV`；另有 KTV 和 4K live 候选。
- 取舍：YouTube 和 B站都有 AMusic/官方向 MV。最终选 YouTube AMusic 官方 MV；底部白色歌词带通过全宽裁切去掉。
- 本地文件：`raw/p2_zaji.mp4` -> `clips/vert_zaji.mp4`。

## 第 1 名：《如水》

- YouTube 候选：`pB3Ih4_1N7o`，Janice Vidal衛蘭，官方歌词版，1920x1080；`3U6M8Ryk63w`，Janice Vidal衛蘭，1080x1080 静态封面；`q7iUOPZKVbU` / `PIcLKratt7M`，第三方 320x240/314x240 MV 或图片向上传。
- B站候选：`BV1qd4y1P7SU`，1080P KTV 修复版，画质高但大面积烧死卡拉 OK 歌词；`BV15NMpzoEm1`，4K60 live，实下 1080P，真实歌手舞台画面，底部小字幕可裁；另有官方 MV 合集 `BV1Zx411L7n4`。
- 取舍：官方 YouTube 候选为静态封面或歌词版，不适合展示段；低清 YouTube MV 候选主要是静态图片 slideshow；B站 KTV 画质高但大字歌词侵入画面。最终选 B站 live 候选 `BV15NMpzoEm1`，牺牲“官方 MV”优先级，换取动态真人演唱、清晰度和干净画面；底部字幕通过 `1920:900:0:0` 全宽裁切移除。
- 本地文件：`raw/p1_rushui_bili_live.mp4` -> `clips/vert_rushui.mp4`。

## 竖屏处理

全部使用 `tools/video/vfill.sh` 做 1080x1920 竖屏填充。裁切策略以全宽 letterbox 为主，只裁掉黑边、底部歌词带或字幕带，不做激进竖向放大。
