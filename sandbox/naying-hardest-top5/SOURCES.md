# Sources — 那英最难的5首歌

Cookie files checked:

- YouTube: `sandbox/www.youtube.com_cookies.txt`
- B站: `sandbox/www.bilibili.com_cookies.txt`

Selection rule: both YouTube and B站 were searched for every song. Prefer official source, clean image, stereo audio, usable continuous chorus, and no burned-in platform/UP watermark. Short probes were downloaded where needed, then frame-checked before final clipping. When no clean MV existed, final composition uses a bottom mask to hide burned lyrics.

## 5. 《不管有多苦》

- YouTube candidates:
  - `https://www.youtube.com/watch?v=MglsYNVAYEw` | 4:32 | Timeless Music | official完整版MV | 648x480, stereo Opus | large KTV lyrics
  - `https://www.youtube.com/watch?v=bucpYtqXnpQ` | 4:29 | Hi-Def Music | 1080P lossless-style upload | mostly static singer photo, rejected as non-dynamic footage
- B站 candidates:
  - `https://www.bilibili.com/video/BV1J4VBzxExv` | 4:25 | 1080P60 DVD/Karaoke, CD音轨 | stereo AAC | large KTV lyrics
  - `https://www.bilibili.com/video/BV1GWHLzBE6E` | 华纳音乐中国 | 640x480 official upload
  - `https://www.bilibili.com/video/BV18L4y1e7Hw` | 4K修复 Live'02 | stereo AAC | TV logo + B站 watermark + bottom lyric, rejected
- Final choice: B站 `BV1J4VBzxExv`.
- Reason: best dynamic 1080P stereo source found; all usable MV versions carry KTV lyrics, so final HTML uses bottom masking during this section.
- Clip window: source `00:02:00-00:03:03`, output `raw/p5_buguan_bi.mp4`, vfill crop `1920:1080:0:0`, final mask enabled.

## 4. 《出卖》

- YouTube candidate: `https://www.youtube.com/watch?v=6RT_Fpy1__s` | 4:20 | Timeless Music | official完整版MV | 1600x1080, stereo Opus
- B站 candidates:
  - `https://www.bilibili.com/video/BV1BTADzhEL6` | 4:19 | 原版4K修复版 | 1920x1080 H.264, stereo AAC
  - `https://www.bilibili.com/video/BV1G7411t75X` | official完整版MV mirror
  - `https://www.bilibili.com/video/BV1LiVBzJEwJ` | DVD Karaoke 1080P60, CD音轨
- Final choice: B站 `BV1BTADzhEL6`.
- Reason: sharper 1080P repair, stereo audio, no platform watermark in probe; bottom lyrics removed by full-width crop.
- Clip window: source `00:02:05-00:03:08`, output `raw/p4_chumai_bi.mp4`, crop `1920:900:0:0`.

## 3. 《白天不懂夜的黑》

- YouTube candidate: `https://www.youtube.com/watch?v=KheDK8lO0Qc` | 3:48 | 福茂唱片 | 官方版MV | 640x480, stereo Opus | clean, small bottom subtitle in some frames
- B站 candidates:
  - `https://www.bilibili.com/video/BV1eL411R7jc` | 2160P60 LD采集 | 1440x1080 H.264, stereo AAC | top-right UP watermark + large lyrics
  - `https://www.bilibili.com/video/BV1ja5h6XETZ` | 官方版MV mirror | 640x480 | top-right B站/channel watermark
  - `https://www.bilibili.com/video/BV1N522BpE6b` | Live pure version | rejected for version mismatch
- Final choice: YouTube official `KheDK8lO0Qc`.
- Reason: lower resolution but cleanest official source; B站 HD candidates contain visible watermark and larger lyrics. Final HTML uses a bottom mask for the small subtitle area.
- Clip window: source `00:01:20-00:02:23`, output `raw/p3_baitian_yt.webm`, crop `640:480:0:0`, final mask enabled.

## 2. 《默》

- YouTube candidate: `https://www.youtube.com/watch?v=XJVuKRMogfE` | 5:07 | 1080P film theme MV | 1920x1072, stereo Opus
- B站 candidates:
  - `https://www.bilibili.com/video/BV1babSz1EcL` | 4K60 AI高清修复 | 1920x1080 AV1, stereo AAC | clean probe
  - `https://www.bilibili.com/video/BV1ms411m74x` | film theme MV
  - `https://www.bilibili.com/video/BV1mt421K7E6` | 4K60/SQ with subtitles, rejected for subtitle risk
- Final choice: B站 `BV1babSz1EcL`.
- Reason: clean 4K/60 stereo source, no platform/UP watermark; corrected to the first chorus around “我被爱判处终身孤寂”. Bottom source subtitles are removed by the vertical crop.
- Clip window: source `00:00:36-00:01:39`, output `raw/p2_mo_bi.mp4`, crop `3840:1640:0:180`.

## 1. 《征服》

- YouTube candidate: `https://www.youtube.com/watch?v=jrLil3-x_9Y` | 5:02 | Timeless Music | official完整版MV | 1456x1080, stereo Opus | large KTV lyrics
- B站 candidates:
  - `https://www.bilibili.com/video/BV1Uxu9zqEEE` | 华纳官方发布4K修复版 | 1920x1080 AV1, stereo AAC | large KTV lyrics
  - `https://www.bilibili.com/video/BV11MJrzoE65` | 4K原版MV
  - `https://www.bilibili.com/video/BV1X4411B76y` | MV mirror
- Final choice: B站 `BV1Uxu9zqEEE`.
- Reason: YouTube and B站 official-style versions both carry KTV lyrics; B站 repair has the better picture and stereo audio. Final HTML masks the lyric region during this section.
- Clip window: source `00:02:18-00:03:21`, output `raw/p1_zhengfu_bi.mp4`, vfill crop `1920:1080:0:0`, final mask enabled.
