# 李克勤最难的5首歌 — Design Notes

## Direction

- Format: vertical short-form music ranking, 1080x1920, countdown from 05 to 01.
- Mood: refined Hong Kong concert hall, classical-piano precision, late-night Cantonese ballad emotion.
- Visual metaphor: black stage, gold score lines, burgundy velvet, piano-key cuts, one bright accent for the hardest rank.

## Palette

- Stage black: `#07070a`
- Deep burgundy: `#2a0812`
- Warm gold: `#d7a85c`
- Pale lyric: `#f7efe2`
- Muted text: `#cfc2ad`
- Rank-one accent: `#f05a7d`

## Typography

- Main title: Chinese serif / song-title register. Prefer `Noto Serif SC` if available.
- UI labels and notes: clean Chinese sans. Prefer `Noto Sans SC`.
- Numbers: tabular, heavy, high contrast.

## Motion

- Rhythm: cover hold -> five repeated song beats -> final list -> CTA.
- Primary transition language: warm fade and slight push, no flashy glitch.
- Each song beat uses a large rank card during narration, then a compact label during the full-music showcase.

## Content Rules

- Order must be 05 -> 01 on screen and in narration.
- Female narration throughout intro, every song transition, outro, and fixed CTA.
- Each showcase should be a continuous sung section, not a fast montage.
- Use official MV whenever feasible; if an official MV is too low-quality or non-performative, select the cleaner YouTube/B站 candidate and document the tradeoff in `SOURCES.md`.
