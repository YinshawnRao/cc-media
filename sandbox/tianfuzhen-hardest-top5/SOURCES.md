# Sources — 田馥甄最难的5首歌

Cookie files to check before source work:

- YouTube: `sandbox/www.youtube.com_cookies.txt`
- B站: `sandbox/www.bilibili.com_cookies.txt`

Selection rule: search both YouTube and B站 for every song. Prefer official source, clean image, stereo audio, usable continuous chorus, and no burned-in platform/UP watermark. Download probes for both sides where needed, frame-check them, then record the final clip window and crop here.

## 5. 《矛盾》

- YouTube candidate: `https://www.youtube.com/watch?v=gJhvVMQYWUs` | 4:48 | 華研國際 | Official MV HD | 1080p probe, stereo Opus, HIM logo + lower lyric line.
- B站 candidate: `https://www.bilibili.com/video/BV1P1R5BnERn` | 4:48 | 甄爱SHE | 4K修复 / Hi-Res | 1080p H.264 probe, stereo FLAC, top-left B站/uploader mark + lower lyric line.
- Final choice: B站 `BV1P1R5BnERn`.
- Reason: better audio and sharper encoding than YouTube; final crop removes both the top-left uploader/platform mark and the lower lyric line.
- Clip window: source `00:02:10-00:03:12`, output `raw/p5_maodun_bi.mp4`.
- Crop: `1920:540:0:170`, output `clips/vert_maodun.mp4`.

## 4. 《悬日》

- YouTube candidate: `https://www.youtube.com/watch?v=Nf1C1fSJG_8` | 5:23 | Hebe Tien official channel | Official MV | 1080p probe, stereo Opus, built-in black layout + lower lyric line.
- B站 candidate: `https://www.bilibili.com/video/BV1qp4y1v7Rn` | 5:24 | 大家的音乐机 | 官方MV | 1080p H.264 probe, stereo AAC, visually matches YouTube.
- Final choice: B站 `BV1qp4y1v7Rn`.
- Reason: same clean MV image as YouTube but stronger H.264/AAC stream; final bottom crop removes the small lower lyric line.
- Clip window: source `00:02:22-00:03:22`, output `raw/p4_xuanri_bi.mp4`.
- Crop: `1920:760:0:0`, output `clips/vert_xuanri.mp4`.

## 3. 《魔鬼中的天使》

- YouTube candidate: `https://www.youtube.com/watch?v=na_xv5iFt2Y` | 4:14 | 華研國際 | Official MV | 712x480 probe, stereo Opus, lower lyric line.
- B站 candidates:
  - `https://www.bilibili.com/video/BV11ACYBrEwG` | 4:13 | 甄爱SHE | 4K修复 / 歌词重制.
  - `https://www.bilibili.com/video/BV135411T7y1` | 4:17 | 原画质官方无水印MV | 1080p H.264 probe, stereo AAC, top-right B站/uploader mark.
- Final choice: B站 `BV135411T7y1`.
- Reason: YouTube official is only 480p; B站 clean candidate is much sharper and stereo. Final top crop removes the B站/uploader mark.
- Clip window: source `00:01:52-00:02:52`, output `raw/p3_mogui_bi.mp4`.
- Crop: `1920:820:0:160`, output `clips/vert_mogui.mp4`.

## 2. 《你就不要想起我》

- YouTube candidate: `https://www.youtube.com/watch?v=GsKbnsUN2RE` | 5:18 | 華研國際 | Official MV HD | 1080p probe, stereo Opus, HIM logo + lower lyric line.
- B站 candidates:
  - `https://www.bilibili.com/video/BV1xvEs6cE3z` | 5:18 | 4K臻藏 MV mirror | 1080p H.264 probe, stereo AAC, visually same source.
  - `https://www.bilibili.com/video/BV1jE421w7qk` | 39:14 | 4K60 long/live compilation.
- Final choice: YouTube `GsKbnsUN2RE`.
- Reason: B站 mirror adds no visual advantage in the sampled window and has weaker audio; YouTube is official with stronger stereo Opus. Final crop removes HIM logo and lyrics.
- Clip window: source `00:02:46-00:03:46`, output `raw/p2_buyao_yt.mp4`.
- Crop: `1920:640:0:150`, output `clips/vert_buyao.mp4`.

## 1. 《讽刺的情书》

- YouTube candidate: `https://www.youtube.com/watch?v=o2zUZmUmwUg` | 5:01 | Hebe Tien official channel | Official MV | 1080p probe, stereo Opus, lower lyric line.
- B站 candidates:
  - `https://www.bilibili.com/video/BV1VxAaziEnq` | 5:01 | 4K官方MV mirror | 1080p AV1 probe, weak stereo AAC, visually same source.
  - `https://www.bilibili.com/video/BV1Hi4y1u7am` | 5:01 | 大家的音乐机 | 官方MV.
  - `https://www.bilibili.com/video/BV1zA411N7cR` | 5:00 | 太合音乐 | 官方MV.
- Final choice: YouTube `o2zUZmUmwUg`.
- Reason: B站 sampled mirror is visually the same and has much weaker audio; YouTube official keeps stronger stereo Opus. Final crop removes bottom lyrics.
- Clip window: source `00:02:25-00:03:25`, output `raw/p1_fengci_yt.mp4`.
- Crop: `1920:760:0:0`, output `clips/vert_fengci.mp4`.
