# 容祖儿最难的5首歌 — Design

## Format

- Vertical short-form video, `1080x1920`, 30fps.
- Countdown order: 5 -> 1 (难度由低到高揭晓，压轴第一名)。
- Female narration (`zf_xiaoyi`) — brief 明确要求女声。
- Opening must NOT reveal the ranking list (brief: 留悬念). Cover = title + premise only.
- Each song section: female narration -> short breathing beat -> continuous chorus/showcase (>=~25s, SHOW=38s).
- Ending reveals the full ranking summary, then the fixed CTA (last line, per CONVENTIONS).

## Visual Identity (inherits naying-hardest-top5 template, warm-gold accent)

- Mood: restrained, emotional, vocal-analysis oriented. 容祖儿 = 广东歌天后, 情绪克制系难歌。
- Background: real MV/Live footage, letterboxed (default), only full-width crops to remove burned lyrics/logo bands.
- Palette:
  - base: `#08070a`
  - panel/scrim: `rgba(5,5,8,.68)`
  - text: `#f8f3ec`
  - accent (gold): `#d6b16a`
  - danger accent for rank 1 (破相): `#c7333f`
- Type: system CJK stack, heavy display weights.
- Motion: clean slides, marker-line reveals.

## Composition Rules

- Cover: title + premise + technique chips, NO list of five songs.
- Song cards: large countdown number + 《歌名》 + 难点 tag + note line.
- Showcase sections keep only a small top-left rank tag so footage breathes.
- lyricMask: bottom opaque panel for sources whose burned lyrics can't be fully cropped.
- Final summary lists: 1 破相, 2 心淡, 3 搜神记, 4 16号爱人, 5 痛爱.

## Sources (both YT + B站 searched; see SOURCES.md)

- 5 痛爱: B站 Pretty Crazy Live BV1Z54y1Y7x2 (1080p closeup, ss=99, crop=1920:866:0:0). DVD credit/HOME-USE-ONLY only on 88–95s costume wide → window starts past it.
- 4 16号爱人: B站 音乐私藏馆 Live BV1dK4y1W7m9 (1080p, ss=80, crop=1920:790:0:160). Official MV is drama (no singing); TMElive logo un-croppable. EEG logo + subtitle cropped; crowd shots fit K-song theme.
- 3 搜神记: YouTube official MV XNJJOjaCfbw (480p, ss=132, crop=600:398:0:0, continuous sepia closeups).
- 2 心淡: YouTube official MV E4jPiazznkY (480p, ss=84, crop=600:400:0:14, eq brighten). Live versions too multi-cam/wide.
- 1 破相: YouTube official MV S9oonBJeoRE (480p, ss=128, crop=640:446:0:16, red-hair closeups, climax).

Authoritative source record: see SOURCES.md.
