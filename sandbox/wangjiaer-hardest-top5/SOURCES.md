# Sources — 王嘉尔最难的5首歌

Cookie files checked:

- YouTube: `sandbox/www.youtube.com_cookies.txt`
- B站: `sandbox/www.bilibili.com_cookies.txt`

Selection rule: search both YouTube and B站 for every song. Prefer official source, clean image, stereo/AAC audio, usable continuous representative segment, and no burned-in platform/UP watermark. Final clips are rendered through `tools/video/vfill.sh` and re-encoded to H.264/AAC.

## 5. 《Come Alive》

- YouTube candidate: `https://www.youtube.com/watch?v=WvIBitkrdL8` | Jackson Wang official channel | 4:34 | 1920x1080 AV1 + Opus
- B站 candidate: `https://www.bilibili.com/video/BV1i14y1K7ZL` | 王嘉尔 official account | 4:35 | 1920x1080 AVC + AAC
- Final choice: B站 official, because it is official, 1080p, H.264/AAC, and cleaner to process than YouTube AV1/Opus.
- Clip window: `00:01:20-00:02:25`; showcase starts at source `00:01:43.06` / clip local `23.06s`.
- Crop: `1920:900:0:120` in `tools/video/vfill.sh`; removes top B站 watermark while keeping the full-width composition.

## 4. 《LMLY》

- YouTube candidate: `https://www.youtube.com/watch?v=QIMihDOXMpY` | Jackson Wang official channel | 7:45 | 1920x816 AV1 + Opus
- B站 candidate: `https://www.bilibili.com/video/BV1oK411c7Co` | TEAMWANG嘉尔工作室 | 7:45 | 2538x1080 AVC + AAC
- Final choice: B站 TEAMWANG official-studio source, because it is 1080p ultrawide H.264/AAC and official/studio hosted.
- Clip window: `00:01:07-00:02:15`; showcase starts at source `00:01:29.60` / clip local `22.60s`.
- Crop: `2538:820:0:90` in `tools/video/vfill.sh`; removes top watermark and bottom burned English subtitles while preserving full-width layout.

## 3. 《Cruel》

- YouTube candidate: `https://www.youtube.com/watch?v=Rhy7_Y15FrI` | Jackson Wang official channel | 3:15 | 1920x1080 AV1 + Opus
- B站 candidate: `https://www.bilibili.com/video/BV17e4y1X7FU` | 王嘉尔 official account | 3:15 | 1920x1080 AVC + AAC
- Final choice: B站 official, because it is official, 1080p, H.264/AAC, and easier to process than YouTube AV1/Opus.
- Clip window: `00:01:31-00:02:31`; showcase starts at source `00:01:49.40` / clip local `18.40s`.
- Crop: `1920:900:0:120` in `tools/video/vfill.sh`; removes top B站 watermark while keeping the full-width action composition.

## 2. 《Blow》

- YouTube candidate: `https://www.youtube.com/watch?v=qCZHarOQvc4` | Jackson Wang official channel | 3:53 | 1920x1080 AV1 + Opus
- B站 candidate: `https://www.bilibili.com/video/BV13S4y1K7ij` | 王嘉尔 official account | 3:53 | 1920x1080 HEVC + AAC
- Final choice: B站 official, because it is official and AAC; HEVC was re-encoded during verticalization.
- Clip window: `00:01:28-00:02:32`; showcase starts at source `00:01:49.48` / clip local `21.48s`.
- Crop: `1920:850:0:145` in `tools/video/vfill.sh`; removes the larger top-right B站首发 watermark while keeping the full-width group composition.

## 1. 《Made Me a Man》

- YouTube candidate: `https://www.youtube.com/watch?v=vz-_ZtUh8P4` | Jackson Wang official channel | 3:55 | 1920x1080 AV1 + Opus
- B站 candidate: `https://www.bilibili.com/video/BV1uvg3zsE6F` | 王嘉尔 official account | 3:55 | 1920x1080 AV1 + AAC
- Final choice: B站 official, because it is official and AAC; AV1 was re-encoded during verticalization.
- Clip window: `00:02:03-00:03:15`; showcase starts at source `00:02:25.71` / clip local `22.71s`.
- Crop: `1920:900:0:120` in `tools/video/vfill.sh`; removes top B站 watermark while keeping the flower-field and close-up composition intact.
