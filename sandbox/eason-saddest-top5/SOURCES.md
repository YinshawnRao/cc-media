# 陈奕迅最苦的5首歌 — Sources

两个平台均已查：YouTube 可做 flat search，但当前 `sandbox/www.youtube.com_cookies.txt` 做完整提取时报 `Sign in to confirm you’re not a bot`，不可下载；B站 cookie 可搜索/下载，所以工作素材选 B站。

## ⑤《葡萄成熟时》

- YouTube flat candidates: `NCsVnmmNA3E | Eason Chan | 葡萄成熟時`, `M3exHtTtDOw | 陳奕迅 葡萄成熟時 MV`。
- B站候选：`BV1sE411c7Cy` 1080p 修复版；`BV1Rjx7zRELv` 环球音乐中国官方但只有 640x480/低码率且带顶部 B站水印。
- 选定：`BV1sE411c7Cy`，1080p H.264 / stereo。底部歌词通过全宽裁切 `1920:900:0:0` 去除。

## ④《最佳损友》

- YouTube flat candidates: `0fcKEN4_QoM | Eason Chan | 最佳損友`, `4hMdTZr7XOg | Eason Chan | FEAR AND DREAMS ENCORE`。
- B站候选：`BV1qS4y1S7BN` 4K修复 MV；`BV1gU4y1F7d4` 1080p 修复 MV；多条 Live。
- 选定：`BV1qS4y1S7BN`，1902x1080 H.264 / stereo，画面干净，无烧词。

## ③《人来人往》

- YouTube flat candidates: `gAotCGoKhD0 | 英皇娛樂 eeg music | Official MV`, `OgU_x7rmzqo | Eason Chan | 人來人往`。
- B站 MV 候选：`BV1ff4y1x7HQ` TVB版有翡翠台台标和卡拉OK烧词；`BV1vq4y1P7H9` 有大号歌词和 EEG logo。
- 选定：`BV1F34y177xc`，MV-style clean fallback，1920x1080 H.264 / stereo。使用 `1920:620:0:180` 裁掉 EEG/credit 带，避开大号歌词污染。

## ②《明年今日》

- YouTube flat candidates: `8NJVNkzhJM4 | 英皇娛樂 eeg music | Official MV`, `IZfy1wn3tNM | Eason Chan | FEAR AND DREAMS ENCORE`。
- B站候选：`BV1T3411T7RN` 4K60 修复 MV；`BV1kL411J749` 1080p 修复 MV；`BV1ykDoYMEXM` Hires 修复。
- 选定：`BV1T3411T7RN`，2470x1080 H.264 / stereo。底部片尾字通过 `2470:930:0:0` 规避。

## ①《富士山下》

- YouTube flat candidates: `7qeShSmmsNg | Eason Chan | 富士山下`, `vbrbuyvx2p4 | Eason Chan | 富士山下`。
- B站候选：`BV16741157nh` 4K修复版但底部字幕较多；`BV1LNsbe8ECx` Hires/双版候选，雨景 MV 画面更干净。
- 选定：`BV1LNsbe8ECx`，1920x1016 H.264 / stereo，使用 `1920:900:0:0` 保留主体并避开底部污染。

