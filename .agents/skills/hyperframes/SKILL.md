---
name: hyperframes
description: Author or edit cc-media HyperFrames HTML compositions. Use for timing, video layout, overlays and seekable animation; repository Qwen, sourcing and final QA remain in the production Runbook.
---

# cc-media HyperFrames authoring

Read the repository [Runbook](../../../tools/video/README.md) for production and [CONVENTIONS](../../../CONVENTIONS.md) for editorial defaults. This local skill takes precedence over same-name global workflow examples in cc-media; it does not require a second design approval or reduce a video brief to preview-only delivery.

## Work from the actual project

Read the relevant HTML, timeline, design and package pin. A short design note is enough for a new piece; prompt expansion is optional internal planning. Use the requested style, choose missing details, and continue to the authorized deliverable. Only ask for required missing input or an explicitly requested review stage.

New projects use hyperframes@0.6.69; existing projects retain their pin. Confirm unfamiliar APIs against that version. Do not update skills or renderer incidentally. Font files must be offline: prefer project WOFF2 and relative @font-face; don't rely on font-name auto-fetch.

## Composition contract

- Root metadata: data-composition-id, data-start=0, data-duration, data-width/data-height. Give the visible root a real CSS size.
- Timed elements: class=clip, unique id, data-start/data-duration/data-track-index. Track index is scheduling; z-index controls visual stacking. Avoid unintended overlap on one track.
- Register a synchronously constructed paused timeline as window.__timelines[id]. Use finite, seek-safe effects, not wall-clock timers or asynchronous construction.
- Video is muted/playsinline; audio is independent. Do not control media play/pause/currentTime from animation callbacks. Precut footage when necessary for the pinned renderer.
- Avoid a timed wrapper around a timed video. Animate a wrapper for geometry. Long footage-heavy pieces usually benefit from one concatenated footage_track; multiple videos are permitted when verified for the project.
- On exits use deterministic timeline state; verify seeking and ensure later tweens cannot resurrect hidden elements. Fixed-version warnings need investigation, not blanket suppression.

```html
<div id="film" data-composition-id="film" data-start="0" data-duration="8" data-width="1080" data-height="1920" style="position:relative;width:1080px;height:1920px;overflow:hidden">
  <div id="cover" class="clip" data-start="0" data-duration="8" data-track-index="1">本期主题</div>
</div>
<script>
const tl = gsap.timeline({paused:true});
tl.set('#cover', {opacity:1}, 0);
window.__timelines = window.__timelines || {};
window.__timelines.film = tl;
</script>
```

Load the project's local/pinned GSAP dependency before this script. This minimal contract is not a complete design or a promise that later-version APIs work on 0.6.69.

## Visual decisions

First frame must work as a cover: readable immediately. Entrances, exits, hard cuts, fades and static holds are choices, not universal requirements. Build or inspect key layout states before expensive render; flex, grid, absolute positioning and deliberate semantic line breaks are all valid.

Follow [visual choices for each piece](../../../CONVENTIONS.md#字幕与视觉) for content-based styling, reuse boundaries and a lightweight comparison with recent covers. No element count, easing quota, banned-font list or mandatory ambient motion. Preserve clear identity, legibility, framing, natural line breaks and subject visibility. See optional [typography](references/typography.md), [composition](references/video-composition.md) and [style ideas](house-style.md) only when useful.

## Media and verification

Narration uses repository Qwen through tools/tts/narrate.py with the project selection. ASR uses central offline_asr/vocal_segments/QA. Do not call built-in TTS or choose another provider. Add narration captions only on explicit request.

Use [hyperframes-cli](../hyperframes-cli/SKILL.md) for lint/preview/render; preview and snapshots are internal checks unless requested as the deliverable. Render raw and final under renders/, post-mux master.wav, then run the applicable project/publishing/final gates.

## Technical references, on demand

- GSAP: [gsap](../gsap/SKILL.md); other adapters only for the runtime actually used.
- Seek behavior: [motion-principles](references/motion-principles.md).
- Transitions: [transitions](references/transitions.md) and per-effect catalog.
- Captions: [captions](references/captions.md), only when requested.
- Audio reactive: [audio-reactive](references/audio-reactive.md).
- Optional internal planning: [prompt-expansion](references/prompt-expansion.md).
