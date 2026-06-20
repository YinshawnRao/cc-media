# Sources — 李健最难的5首歌

Cookie files checked:

- YouTube: `sandbox/www.youtube.com_cookies.txt`
- B站: `sandbox/www.bilibili.com_cookies.txt`

Selection rule: both YouTube and B站 were searched for every song. Prefer official/performance-matching source, clean image, stereo audio, usable continuous singing section, and no platform/UP watermark. B站 search succeeded, but several B站 download probes hit stalled/partial stream pulls, so final clips use verified YouTube sources unless noted.

## 5. 《美若黎明》

- YouTube candidates:
  - `https://www.youtube.com/watch?v=3WWwbiCWmuw` | 4:31 | 李健 Li Jian 的小力豆豆 | official MV | 854x476 H.264, stereo Opus | clean probe
  - `https://www.youtube.com/watch?v=qKUTwCo4_C0` | 4:28 | 浙江卫视官方 live version
- B站 candidates:
  - `BV1GS4y1Z7Q4` | 4:42 | Live 4K | concert source
  - `BV1Js411d71z` | 4:33 | MV mirror
  - `BV1aD4y1i7UH` | 4:37 | 咪咕音乐官方 MV | parsed as 1280x720 H.264 + stereo AAC, but stream pull failed before probe completion
- Final choice: YouTube `3WWwbiCWmuw`.
- Reason: official MV, clean frame probes, stereo audio. Lower resolution than some B站 candidates, but no successful cleaner B站 probe was obtained.
- Clip window: source `00:01:35-00:02:55`, output `clips/vert_meiruo.mp4`, crop `854:476:0:0`.

## 4. 《传奇》

- YouTube candidates:
  - `https://www.youtube.com/watch?v=BUKCNoOh9MY` | 4:03 | 中国音乐电视 | CCTV live | 1920x1080 stereo | rejected for CCTV logo, vertical title, and burned subtitles
  - `https://www.youtube.com/watch?v=cOpINZd3NGE` | 4:49 | MV upload | 426x240 stereo | rejected for very low resolution and embedded bottom text
  - `https://www.youtube.com/watch?v=gEMIchfIQ7Q` | 4:55 | 李健 official lyrics version | 1920x1080 stereo | rejected as lyric video with large center lyrics
  - `https://www.youtube.com/watch?v=EWQj5nX_YwU` | 23:06 | 2017 live collection | 1280x720 H.264, stereo Opus | cleanest usable Li Jian performance probe
- B站 candidates:
  - `BV1NX6JY6EpN` | 4:02 | live
  - `BV1eh411C7VU` | 4:47 | 1080P live
  - `BV1va4y177Po` | 4:50 | MV | parsed as 720x576 H.264 + stereo AAC, but stream pull failed
- Final choice: YouTube `EWQj5nX_YwU`.
- Reason: Li Jian himself, live performance, stereo, no platform/UP watermark in probe. Avoids CCTV/source subtitles from the other candidates.
- Clip window: source `00:00:45-00:02:20`, output `clips/vert_chuanqi.mp4`, crop `1280:720:0:0`.

## 3. 《向往》

- YouTube candidates:
  - `https://www.youtube.com/watch?v=EToukUQUcYM` | 3:47 | 李健LIJIAN_OFFICIAL | official MV | 1920x1080 AV1, stereo Opus | clean except bottom lyrics
  - `https://www.youtube.com/watch?v=biZFBJOSFUw` | 3:57 | official live
  - `https://www.youtube.com/watch?v=B9_AP4K96_Q` | 4:00 | official audio/MV-style upload
- B站 candidates:
  - `BV1TV4y1M7DE` | 4:19 | live现场
  - `BV1a5411L7Ak` | 3:58 | 浙江卫视 official
  - `BV1Ys411f7ax` | 3:46 | official MV mirror
- Final choice: YouTube `EToukUQUcYM`.
- Reason: official MV, 1080P stereo, stable downloaded probe. Bottom lyrics removed with full-width crop.
- Clip window: source `00:01:10-00:02:30`, output `clips/vert_xiangwang.mp4`, crop `1920:960:0:0`.

## 2. 《假如爱有天意》

- YouTube candidates:
  - `https://www.youtube.com/watch?v=g53FlS0U9wE` | 5:04 | 芒果TV音乐 | 我是歌手3 official pure version | 1920x1080 AV1, stereo Opus | sponsor mark + bottom subtitles
  - `https://www.youtube.com/watch?v=eqGbI0My6MQ` | 5:07 | 浙江卫视 2024 pure version
  - `https://www.youtube.com/watch?v=CyHkB_WkHKE` | 4:13 | 李健&郎朗 piano version
- B站 candidates:
  - `BV1ajB7YzE89` | 6:04 | 4K repair
  - `BV1u6421g7xC` | 4:13 | 李健工作室 piano version
  - `BV1JY411J7Eh` | 10:04 | 1080P karaoke
- Final choice: YouTube `g53FlS0U9wE`.
- Reason: best match to the brief's 我是歌手3 context, stereo official source. B站 4K repair could not be successfully probe-downloaded in this run. The final crop uses a tighter single-singer frame to remove bottom lyrics and side sponsor screens; the composition keeps a right-side difficulty badge as an additional mask.
- Clip window: source `00:02:25-00:03:55`, output `clips/vert_tianyi.mp4`, crop `720:560:600:220` plus right-side badge mask.

## 1. 《贝加尔湖畔》

- YouTube candidates:
  - `https://www.youtube.com/watch?v=G6ZS7ho5PXM` | 5:18 | 芒果TV音乐 | 我是歌手3 official pure version | 1280x720 AV1, stereo Opus | sponsor mark + bottom subtitles
  - `https://www.youtube.com/watch?v=H-rgDwMgnE0` | 4:54 | 我是歌手巡回演唱会 official
  - `https://www.youtube.com/watch?v=9huJLg3-TW8` | 4:41 | 合唱纯享
- B站 candidates:
  - `BV19sUyY5EDA` | 5:52 | 4K repair
  - `BV1NT4y1x7BY` | 9:58 | 我是歌手3 episode clip
  - `BV1wr4y1d78V` | 109:05 | 李健歌手合集
- Final choice: YouTube `G6ZS7ho5PXM`.
- Reason: official 我是歌手3 performance matching the brief, stereo audio and stable probe. B站 4K repair could not be successfully probe-downloaded in this run. The final crop removes bottom lyrics; the remaining red sponsor text is part of the stage LED backdrop, and masking it would cover the singer.
- Clip window: source `00:01:50-00:03:20`, output `clips/vert_baikal.mp4`, crop `1280:500:0:50`.
