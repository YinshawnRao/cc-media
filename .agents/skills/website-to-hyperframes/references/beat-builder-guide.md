# Building a website-video beat

Optional technical reference; use the repository [HyperFrames contract](../../hyperframes/SKILL.md) and the actual project pin. A beat can be a static shot, captured screen, layered image, or composed animation. Choose its duration, motion and hierarchy for the message; no motion magnitude, element count or camera-move quota.

## Inputs and output

Use the brief, actual captured assets, project timeline and a short design note. Verify font-family mappings from local files; inspect assets instead of guessing their identity. Resolve ordinary missing design details within the brief and continue. Build a separate sub-composition only when it helps the project; a single composition is also valid.

## Technical checks

- Match the composition ID to its registered paused timeline, synchronously. Match its duration to the host's scheduled duration.
- For a template-based sub-composition, keep its scoped script with the template DOM, and confirm compiler behavior using the pinned version before applying newer examples.
- Asset paths follow the compiler's project-root convention; verify the rendered asset, particularly when HTML lives under compositions/.
- Inline SVG can inherit CSS colors; an SVG loaded through img cannot. Choose inline SVG or an intentional image treatment.
- Avoid animating opacity from zero to an already-zero CSS target. Use explicit fromTo/set values when initial state would otherwise be ambiguous.
- Give GSAP ownership of transforms on animated elements; avoid competing CSS and GSAP transforms or overlapping tweens that overwrite one another.
- Preserve spaces when splitting words into inline-block spans. Choose grouping from the language and reading pace.
- Derive animation state from composition time. Use seeded/precomputed variation and finite durations; don't let wall-clock timers or unseeded randomness control rendered frames.
- Test both forward playback and nonsequential seeks around scene boundaries. Check t=0 cover visibility, subject framing, font load and representative frames.

Captions require an explicit request. Audio belongs to the repository Qwen/master.wav pipeline; a beat builder does not select a second TTS provider or add music automatically. Render and final delivery follow the Runbook.
