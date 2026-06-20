# Sources — 容祖儿最难的5首歌

Cookie files checked:
- YouTube: `sandbox/www.youtube.com_cookies.txt`
- B站: `sandbox/www.bilibili.com_cookies.txt`

Selection rule (CONVENTIONS 硬约束): both YouTube and B站 searched for every song. Joey Yung's official MVs (英皇娱乐 EEG / 容祖兒 Joey Yung channels) are all SD (≤640x480, old uploads). B站 has 1080p Live/4K-修复 versions. Decision per song weighed: cleanliness (no watermark/burned-lyrics) > singer close-up 占比 > resolution. Every candidate was frame-checked with **output-side seek** (input-seek is unreliable for these codecs — see naying notes).

Countdown order is 5→1; ranking revealed only in the outro.

## 5. 《痛爱》  → B站 Pretty Crazy Live (1080p)
- YouTube: `qkT4Mxmm92g` 英皇娱乐 Official MV (600x480) — emotional close-ups BUT burned lyrics move around (top/middle), + non-Joey detail shots (faucet/feet). Rejected.
- B站 chosen: `BV1Z54y1Y7x2` 音乐私藏馆 「Pretty Crazy 红馆」(1080p stereo) — sharp close-up singing in feathered dress.
- Trap: the concert DVD shows wardrobe-credit overlay ("Joey Yung in Paco Rabanne from Joyce") + "HOME USE ONLY" watermark **only on the costume-reveal wide shot ~88–95s**. Close-ups are clean.
- Window: source `00:01:36-00:02:40` (ss=96, past the credit moment, close-up-dominant). crop `1920:866:0:0` (remove bottom karaoke subtitle).

## 4. 《16号爱人》  → B站 音乐私藏馆 Live (1080p)
- Official MV `3wkfKUEga2A` (英皇娱乐, 600x480) = pure **drama** (male lead, courtyard scenery, no singing of Joey). Unusable for a vocal showcase.
- TMElive 粤有味 `BV1A34y1R7vc` (1080p) = beautiful close-up singing BUT a huge persistent "TMElive 腾讯音乐超现场" logo spanning y≈50–160 over her head, + bilibili logo + bottom subtitle. Can't crop cleanly. Rejected.
- Concert YY (`Vly4XfWH9H4` / `BV12A41157dP`) = artistic lyric-overlay plastered across the frame + 66E.CC watermark. Rejected.
- B站 chosen: `BV1dK4y1W7m9` 音乐私藏馆 (1080p stereo) — singing close-ups + crowd sing-along (thematically fits "K房热唱曲"). Multi-cam (cuts every 2–4s).
- Traps: "EEG 英皇娱乐" channel logo (top-left, y≈82–140) appears on wide shots; bottom karaoke subtitle.
- Window: source `00:01:20-00:02:24` (ss=80). crop `1920:790:0:160` (removes EEG logo + bottom subtitle, full-width letterbox).

## 3. 《搜神记》  → YouTube official MV (480p)
- YouTube chosen: `XNJJOjaCfbw` 英皇娱乐 Official MV (600x480) — stylish sepia art-deco MV, continuous Joey singing close-ups (best subject framing of all candidates).
- B站 Live `BV16VckzqEgA` 香港乐坛Live王 (1080p) = multi-cam wide concert (Joey small) + bottom subtitle. Worse framing than the MV.
- Window: source `00:02:12-00:03:16` (ss=132, continuous close-ups, no drama cutaway). crop `600:398:0:0` (remove bottom burned lyrics).

## 2. 《心淡》  → YouTube official MV (480p)
- B站 蓝光原盘 Live `BV1hy4y1E7r5` (1080p, clean) and 飞冰半糖 4K (`BV1gQ4y127Qw`, crowd + UP watermark) — both heavy multi-cam (wide/crowd, Joey small), no sustained close-up. Rejected for showcase.
- YouTube chosen: `E4jPiazznkY` 英皇娱乐 Official MV (600x480) — dark, moody, consistent Joey emotional close-ups (fits the song's "心死" mood). Lyrics at bottom (croppable).
- Window: source `00:01:32-00:02:36` (ss=92). crop `600:400:0:14` + pre-brighten `eq=brightness=0.10:saturation=1.12:contrast=1.06` (vfill BR only affects the blurred bg). Music boosted ×1.4 (loudnorm left it −18 dB).

## 1. 《破相》  → YouTube official MV (480p)
- YouTube chosen: `S9oonBJeoRE` 容祖兒 Joey Yung Official MV (640x480) — dramatic red-hair close-ups in a high-key white room, clean (intro title card top-left only at the very start; chosen window is past it).
- B站 Live `BV1bx4y1j7CB` 香港乐坛Live王 (1080p) = stunning but distant full-body red-gown wide shot (Joey small). Close-ups of the MV win for the #1 climax.
- Window: source `00:02:28-00:03:32` (ss=128, all continuous red-hair close-ups). crop `640:446:0:16` (trim thin top/bottom letterbox bars; her face is at frame-left, so no side crop).

## Notes
- All footage clips are 64s (block = narration + breathing + 38s showcase ≈ 58–60s, + margin); the loud chorus lands at clip-time ≈20–58s.
- Female narration: `zf_xiaoyi` (brief requires 女声). Mandarin narration over Cantonese songs (standard). "16号" spoken as "十六号"; English album name dropped from speech (Kokoro 中英混读 weak).
- Fixed outro CTA appended per CONVENTIONS (last spoken line); outro carries no second vote-ask (防双 CTA).
