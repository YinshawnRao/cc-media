# Design — 王菲最难的5首歌

## Direction

- 竖屏 1080x1920。
- 气质：冷、空、悬浮、带一点世纪末舞台和寓言感；不要综艺花字。
- 节奏：倒数 5 -> 1，每首先用女性旁白讲难点，再给连续代表段；第一名更克制、更高级，不做大红大紫的爆炸收尾。

## Palette

- Background: `#07080d`
- Panel: `rgba(7,8,13,.72)`
- Text: `#f8f4ed`
- Muted text: `#c9c0b8`
- Cold silver: `#bac6d7`
- Moon gold: `#d8b56a`
- Faye red: `#b83f4a`
- Deep teal: `#102d31`

## Type

- 中文标题偏电影海报感，厚重但不要俗艳。
- 正文和标签使用高可读系统中文字体 fallback。
- 排名数字要大，稳定，不随歌词/画面跳动。

## Motion

- Primary transition: blur crossfade / slow reveal feeling.
- Entrance rhythm: rank -> song title -> difficulty tag -> note.
- Full-music 段让 footage 自身承担情绪，不做快闪蒙太奇。

## Avoid

- No platform watermark, URL, internal path, prompt text, or project-meta text in final frames.
- No aggressive vertical crop; old MV resolution低也优先保完整画面。
- No generic purple-blue gradient/orb look.
