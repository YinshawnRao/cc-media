# 裘德最难的5首歌 — design

## Format

- Vertical short-form video, 1080 x 1920, quality-first pacing.
- Ranking reveal order: 05 -> 01. User ranking is preserved: 01 is the hardest and lands last.
- Mood: theatrical, oceanic, jazz-club strange, elegant but slightly unstable.

## Palette

- Background: `#080a0d` ink black with a blue-green tint.
- Surface: `#10161a`.
- Foreground: `#f1ece4`.
- Muted text: `#9fb0ad`.
- Accent gold: `#d7a84f`.
- Aquarium cyan: `#51b9b0`.
- Drama red: `#c94f4f`.
- Deep sea blue: `#0e3340`.

## Typography

- Song titles / big editorial title: `Noto Serif SC`, 800-900.
- UI labels / narration captions: `Noto Sans SC`, 600-800.
- Rank numbers / metadata: `JetBrains Mono`, 700-800.
- Optional English decorative line: `Cormorant Garamond`, italic, 600.

## Motion Language

- Primary transition: blur-through / focus pull, 0.45-0.65s, `power2.inOut`.
- Accent transition into #1: subtle color dip with red bloom, 0.55s.
- Entrances should feel like stage lights finding objects: glides, reveals, focus pulls, slow scale pushes.
- Background elements breathe slowly; no infinite repeats. Compute finite repeats from the composition duration.

## Visual Motifs

- Aquarium glass reflections, thin scan/ripple lines, brass tick marks, ghost typography, diagonal stage-light beams.
- Ranking cards should feel like theatrical placards, not web cards.
- Full-song showcase sections should keep the selected footage/audio readable and avoid over-covering the singer or lyrics video.

## Avoid

- No platform watermarks, URLs, file paths, prompt text, or production terms on screen.
- No "倒数开始" or other meta descriptions of the video mechanism.
- No aggressive vertical crop unless a source is single-subject and verified safe.
- No decorative purple-blue gradient theme; use ink/cyan/brass/red instead.
