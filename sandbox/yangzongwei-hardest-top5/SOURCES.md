# Sources — 杨宗纬最难的5首歌

Cookie files checked:

- YouTube: `sandbox/www.youtube.com_cookies.txt`
- B站: `sandbox/www.bilibili.com_cookies.txt`

Selection rule: both YouTube and B站 were searched for every song. YouTube video-page extraction failed with `Sign in to confirm you’re not a bot`, so YouTube candidates are recorded from flat search metadata only; final downloadable sources use B站 candidates that were downloaded and frame-checked locally.

## 5. 《越过山丘》

- YouTube candidates:
  - `RF9PLIOrSWM` | 3:54 | 太合音乐 | 杨宗纬 Aska Yang《越过山丘》HD 高清官方完整版 MV
  - `8Uq7rZoLlBU` | 3:50 | CCTV综艺 | 2018天下有情人现场
  - `3W3-3l7TcJM` | 3:45 | SMG上海电视台 | 东方卫视中秋晚会
- B站 candidates:
  - `BV1JJ411u78h` | 3:54 | 官方完整版 MV mirror | 1280x720, stereo AAC
  - `BV1BW4y1R7C1` | 5:35 | 咪咕视频《声生不息·宝岛季》现场
  - `BV1Fq4y1V7Sf` | 141:49 | MV 合集
- Final choice: B站 `BV1JJ411u78h`.
- Reason: official MV mirror, clean enough after bottom crop, stereo audio; live candidates were less aligned with the requested MV-first direction.
- Clip window: source `126.0s-181.2s`, output `raw/clip_p5_yueguoshanqiu.mp4`, vfill crop `1280:600:0:0`.

## 4. 《凉凉》

- YouTube candidates:
  - `M7GkL--nb5M` | 3:19 | Croton | 电视剧片尾曲 MV
  - `NGoOpniJwnM` | 6:04 | 芒果TV音乐 | 歌手2017现场
  - `JEC3NFsuAgM` / `DBjzcjhdGgo` | 5:34 | 官方歌词版 MV
- B站 candidates:
  - `BV18WqYBiEg1` | 5:34 | 4K 修复无字幕版 | 1920x1080, stereo AAC
  - `BV17ZVt65E81` | 6:30 | 歌手2017现场 | 1920x1080, stereo AAC, heavy TV logo/subtitles
  - `BV1Px411G7dz` | 3:24 | 电视剧 TV/MV
- Final choice: B站 `BV18WqYBiEg1`.
- Reason: clean OST/MV visuals with no platform watermark. The 歌手现场 better shows the duet, but frame-check found persistent Hunan/Mango logo, center program logo, lower subtitles, and sponsor graphics that could not be cleanly cropped without damaging the singers.
- Clip window: source `260.35s-310.35s`, output `raw/clip_p4_liangliang.mp4`, vfill crop `1920:800:0:140`.

## 3. 《一次就好》

- YouTube candidates:
  - `GffOJ5WlHB8` | 4:23 | ONLYASKA | 夏洛特烦恼插曲完整版 MV
  - `fKuqkeNTsEs` | 4:25 | 浙江卫视 | 领跑2017现场
  - `UU0nDmyzUlI` | 4:20 | SMG上海电视台 | 东方卫视中秋晚会
- B站 candidates:
  - `BV13LYxevEfp` | 4:58 | 4K 修复 MV | 1920x1080, stereo AAC
  - `BV1CtTtzpEfh` | 4:27 | MV mirror
  - `BV1ut411D7zp` | 4:58 | 电影插曲 MV mirror
- Final choice: B站 `BV13LYxevEfp`.
- Reason: better visual clarity than generic mirrors; bottom subtitles were removed by full-width crop.
- Clip window: source `211.45s-259.45s`, output `raw/clip_p3_yicijiuhao.mp4`, vfill crop `1920:780:0:0`.

## 2. 《其实都没有》

- YouTube candidates:
  - `JWIOULj0fxE` | 4:04 | Universal Music Taiwan | Official Music Video
  - `mNhr0jQ3MYE` | 4:03 | YOUKU SHOW | 现场/综艺纯享
  - `0FD8er0G7Wg` | 1:30 | 浙江卫视 | 花絮纯享
- B站 candidates:
  - `BV1qP411N75S` | 4:04 | Official MV mirror | 1920x1080, stereo AAC
  - `BV12N411N7n3` | 4:04 | 4K 修复
  - `BV1Sx41197xn` | 39:02 | 官方现场 MV 合辑
- Final choice: B站 `BV1qP411N75S`.
- Reason: official MV mirror, clean after a tighter bottom crop; a small lower-right logo visible in the first pass was removed by final crop.
- Clip window: source `120.5s-166.5s`, output `raw/clip_p2_qishidoumeiyou.mp4`, vfill crop `1920:700:0:0`.

## 1. 《洋葱》

- YouTube candidates:
  - `78NED_I0lU0` | 5:08 | 滚石唱片 | Official Music Video
  - `TRSq3fO6pSU` | 2:01 | onlyaskacom | two-minute MV
  - `vcl3DPlFFtc` | 4:46 | Aska Yang Topic | audio/topic
- B站 candidates:
  - `BV1k3411n7Am` | 5:09 | 4K60 repair | 1920x1080, stereo AAC
  - `BV1kFE161EJS` | 5:09 | MV mirror
  - `BV1rx411P7EP` | 5:08 | 超清 MV mirror
- Final choice: B站 `BV1k3411n7Am`.
- Reason: best downloaded picture quality and stereo audio; bottom subtitles were removed by full-width crop, leaving clean close-up frames for the #1 showcase.
- Clip window: source `177.75s-233.75s`, output `raw/clip_p1_yangcong.mp4`, vfill crop `1920:870:0:0`.

## QA Notes

- Source frame-checks: `probes/sheet_*.jpg` and `probes/vert_sheet_*.jpg`.
- Final frame-checks: `qa/final_000.jpg`, `qa/final_contact_20s.jpg`, `qa/final_p*_show.jpg`, `qa/final_cta.jpg`.
- Audio: final `silencedetect=n=-35dB:d=1` returned no silence events; showcase mean volume ranged from `-15.7 dB` to `-16.1 dB`.
