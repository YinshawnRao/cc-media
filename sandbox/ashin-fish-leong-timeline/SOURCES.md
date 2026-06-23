# Sources — 阿信 x 梁静茹时间线

本项目按仓库硬约束对每首都查了 YouTube + B站。YouTube flat search 能拿到官方候选 URL，但当前 `sandbox/www.youtube.com_cookies.txt` 被 YouTube 判定失效，直接取视频信息/下载时报 `Sign in to confirm you’re not a bot`。因此本轮成片素材实际使用 B站可下载源，并抽帧/crop 去除平台/UP 主水印、修复标和烧死歌词。

## 片头人像

- 阿信：Wikimedia Commons portrait, `https://upload.wikimedia.org/wikipedia/commons/2/2d/%E4%BA%94%E6%9C%88%E5%A4%A9-%E9%98%BF%E4%BF%A1_%285247928809%29.jpg`
- 梁静茹：Wikimedia Commons portrait, `https://upload.wikimedia.org/wikipedia/commons/8/83/Fish_Leong_20220215.jpg`
- 用途：仅作为片头两张唱片/相册卡的人像层，成片画面不显示来源 URL、文件路径或提示词。

## 01 彩虹

- YouTube: `HnnXkxlyuM8` | 梁靜茹 Fish Leong【彩虹 Rainbow】Official Music Video | https://www.youtube.com/watch?v=HnnXkxlyuM8
- B站候选:
  - `BV1hKhSznEbA` | 彩虹 - 梁静茹【官方MV】DVD MTV Karaoke 1080P 60FPS(CD音轨)
  - `BV1J94y1i7go` | 梁静茹 彩虹 MV 4K 2160P AI修复 音频替换
- 选择: `BV1hKhSznEbA`。1080p H.264、立体声，官方 MV 风格更贴 brief；最终 crop `1920:760:0:130` 去掉歌词残留。

## 02 Beautiful

- YouTube: `A00HC71vMLo` | 梁靜茹 Fish Leong【Beautiful】Official Music Video | https://www.youtube.com/watch?v=A00HC71vMLo
- B站候选:
  - `BV1Tf4y157gw` | Beautiful MV - 梁静茹
  - `BV1URvZBeEB6` | 梁靜茹【Beautiful】原版4K修复版
- 选择: `BV1URvZBeEB6`。1080p H.264、立体声，画面更清晰；最终 crop `1920:760:0:130` 去掉歌词残留。

## 03 听不到

- YouTube: `tRjxa1LuPx0` | 梁靜茹 Fish Leong【聽不到 Can't Hear】Official Music Video | https://www.youtube.com/watch?v=tRjxa1LuPx0
- B站候选:
  - `BV11h411Z7JH` | 梁静茹-听不到（超清4K修复）
  - `BV1ruVXzPEW8` | 【4K修复】梁静茹 - 听不到 MV Hi-Res 2160P 歌词重制
- 选择: `BV11h411Z7JH`。1080p H.264、立体声，候选窗口主体和情绪稳定；最终 crop `1920:820:0:100`。

## 04 燕尾蝶

- YouTube: `KAn2ejVJlE0` | 梁靜茹 Fish Leong【燕尾蝶 Wings of Love】Official Music Video | https://www.youtube.com/watch?v=KAn2ejVJlE0
- B站候选:
  - `BV1qG411w7xU` | 【4K修复 | 独家】梁静茹《燕尾蝶》MV 阿信创作经典摇滚
  - `BV1XsA3z1EQH` | 【4K修复】梁静茹《燕尾蝶》MV 五月天阿信作词作曲
- 选择: `BV1qG411w7xU`。画面质量高；初始顶部标题和底部歌词残留，最终 crop `1920:560:0:220` 清理。

## 05 纯真

- YouTube: `W1bxheRcR70` | 梁靜茹 Fish Leong【純真 Innocence】Official Music Video | https://www.youtube.com/watch?v=W1bxheRcR70
- B站候选:
  - `BV1qC411V7b4` | 梁靜茹 Fish Leong【純真 Innocence】Official Music Video
  - `BV1UcivBKEWS` | 梁静茹【纯真】原版4K修复版
- 选择: `BV1qC411V7b4`。官方 MV 候选优先，源为 926x720 但版本更稳；最终 crop `926:440:0:110` 去掉歌词残留。

## 06 丝路

- YouTube: `LwaZVMERWdQ` | 梁靜茹 Fish Leong【絲路 Silkroad of Love】Official Music Video | https://www.youtube.com/watch?v=LwaZVMERWdQ
- B站候选:
  - `BV1GZ4y137KN` | 梁静茹-丝路_MV（超清4k修复）
  - `BV1QvSbBREJv` | 【SeedVR2-顶级4K修复】Fish 梁静茹 - 丝路 MV 2160P Hi-Res
- 选择: `BV1GZ4y137KN`。1080p H.264、立体声，窗口有较完整大歌段；最终 crop `1920:740:0:150`。

## 07 可乐戒指

- YouTube: `acodaNLe3EY` | 可樂戒指 | https://www.youtube.com/watch?v=acodaNLe3EY
- B站候选:
  - `BV1UwsEeDEMY` | 梁静茹《可乐戒指》MV，1920x1080，60帧，经典歌曲高清修复
  - `BV1uV4y187ic` | 梁静茹-《可乐戒指》1080P高清修复版
  - `BV1fh411b7ZU` | 《可乐戒指》-梁静茹，还有比这更甜的吗？
- 选择: `BV1uV4y187ic`。首个候选带 B站/UP 主顶标，备用源码率更高；最终 crop `1920:780:0:150` 去掉平台/UP 主标和底部歌词。

## 下载与限制

- B站下载脚本: `python3 tools/video/bili_dl.py <bvid> <out.mp4> --max-h 1080`
- YouTube 下载限制: 当前 cookie 失效，非 flat 视频信息读取会被 YouTube 反爬阻断。若后续恢复 cookie，可优先复核官方 YouTube MV 源是否比 B站修复源更干净。
