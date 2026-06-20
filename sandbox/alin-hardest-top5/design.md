# Design — 黄丽玲 A-Lin 最难的5首歌

## Direction

- 竖屏 1080x1920。
- 气质：暗色舞台、成熟情歌、电影感，不做综艺花字。
- 节奏：倒数 5 -> 1，每首先讲难点，再给连续代表段；越靠近第一名，红色强调越强。

## Palette

- Background: `#07080c`
- Panel: `rgba(7,8,12,.70)`
- Text: `#f8f3ee`
- Muted text: `#cfc4bb`
- Gold accent: `#d9a35f`
- Red accent: `#d84a4a`
- Deep wine: `#4b1620`

## Type

- Display/serif mood: use a cinematic serif if available.
- UI/body: system sans fallback is acceptable for Chinese rendering in this sandbox.
- Numbers and ranks should be large, stable, and easy to scan on mobile.

## Motion

- Primary transitions: soft blur/crossfade feeling, not hard jump cuts.
- Entrance rhythm: rank first, song title second, difficulty tag third.
- Keep the footage visible during outro; do not fade to black before CTA.

## Avoid

- No platform watermark, URL, internal path, prompt text, or project-meta text in the final frame.
- No aggressive vertical crop that cuts the singer/actors in half.
- No decorative purple-blue generic gradient look.
