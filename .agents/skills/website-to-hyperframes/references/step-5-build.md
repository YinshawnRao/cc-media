# Build the requested composition

Use [beat-builder-guide](beat-builder-guide.md) for implementation traps and the repository [HyperFrames skill](../../hyperframes/SKILL.md) for the composition contract. Design/brief, real assets and actual audio determine the timeline. A storyboard is an aid, not a separate approval gate; update it if an implementation choice changes the design.

Choose a single composition, stacked scenes or supported sub-compositions for the project. Hard cuts, CSS fades and verified shader transitions are alternatives; HyperShader is not mandatory. Real product screenshots are valid material when the brief calls for a site tour.

When using sub-compositions, schedule hosts at the intended global data-start, use matching host/child IDs and durations, and test boundaries. Scene containers that share the frame can use absolute positioning with the requested canvas size. Do not apply every upstream example to the project's older renderer pin without checking support.

Freeze actual fonts into the project and load them with relative @font-face declarations. No runtime font fetch or assumption that the renderer downloads a font by family name.

If SFX are useful, choose local assets, synchronize their timing with the actual timeline and include them in the final mix. Do not copy an entire asset directory or add a fixed SFX quota. User-requested captions need real aligned text; otherwise omit them. Narration generation and transcription use the central repository tools.

Inspect cover and scene boundaries, lint and render with the pinned CLI/resource wrapper, mux master.wav, and complete the applicable repository QA and publishing copy. See [Runbook](../../../../tools/video/README.md).
