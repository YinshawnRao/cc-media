# Sources — 薛之谦最被低估的5首歌

Cookie status:
- YouTube cookie passed local login-state check.
- B站 WBI search worked. B站 stream metadata resolved for selected live candidates, but full stream downloads repeatedly failed with curl exit 18 or were too slow for full-file download. If replacing dynamic lyric footage, retry exact short B站 sections.

Selection rule: every song was searched on both YouTube and B站. Current build favors stable official YouTube sources; B站 candidates are recorded where they are better visual candidates but not yet downloaded cleanly.

## #5 《银河少年》

- YouTube: `KUEWvjsTh6A` | 腾讯音乐发行 | 官方动态歌词版 MV | 1080p downloaded as `raw/yinhe_yt.mp4`.
- B站: `BV1Ep4y1R7QS` | 江苏卫视 | live performance | resolved 1920x1080 AVC + 182kbps audio, but m4s download failed with curl exit 18; yt-dlp direct download was too slow for full-file use.
- Current build: YouTube official dynamic lyric source. Crop removes top TME mark and bottom credit strip as much as possible.

## #4 《背过手》

- YouTube: `WoUqS_29Aq8` | 腾讯音乐发行 | 官方动态歌词版 MV | 1080p downloaded as `raw/beiguoshou_yt.mp4`.
- B站: `BV1ThD7B9EUm` | 万兽之王双场双正面超近视角 4K 纯享版 | resolved 1920x1080 AVC + 103kbps audio, but m4s download failed with curl exit 18.
- Current build: YouTube official dynamic lyric source. Visual is static, so the HyperFrames reveal/chip layer carries more rhythm.

## #3 《小孩》

- YouTube: `LRjPSCMQgCw` | 薛之謙 JokerXue | Official Music Video | 1080p downloaded as `raw/xiaohai_yt.mp4`.
- B站: `BV1C5411P7ra` | 太合音乐 | 官方 MV found in search.
- Current build: YouTube official MV. Clean dynamic MV, no platform watermark; small artistic text is part of MV.

## #2 《等我回家》

- YouTube: `EsCcXP0jIhg` | 腾讯音乐发行 | 官方动态歌词版 MV | 1080p downloaded as `raw/deng_yt.mp4`.
- B站: `BV13x41167ZZ` | 王栎鑫对唱 live | resolved 960x540 AVC + 146kbps audio, but m4s download failed with curl exit 18.
- Current build: YouTube official dynamic lyric source. Crop removes top TME mark.

## #1 《违背的青春》

- YouTube: `0BEl49cm5A0` | 薛之謙 JokerXue | Official Music Video | 1080p downloaded as `raw/weibei_yt.mp4`.
- B站: `BV1iU4y1a7ta` | 太合音乐 | 官方 MV found in search.
- Current build: YouTube official MV. Dynamic band/drama footage; bottom subtitles are removed by safe full-width crop.

## Known Tradeoff

The current stable build uses official dynamic lyric sources for #5/#4/#2 because B站 live downloads failed. These are official and musically correct, but less visually rich than live footage. The replacement path is to download only short B站 sections after final time windows are locked.
