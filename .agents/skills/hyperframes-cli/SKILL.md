---
name: hyperframes-cli
description: Run the pinned cc-media HyperFrames CLI for scaffolding, lint, preview, rendering and diagnostics with the repository resource wrapper.
---

# cc-media HyperFrames CLI

Production sequence and current paths: [Runbook](../../../tools/video/README.md). New projects pin hyperframes@0.6.69; existing projects use their own package scripts/lockfile. No floating npx/latest or incidental upgrade. Feature descriptions in other skills are not proof of support in this pin.

From repository root:

```bash
npx --yes hyperframes@0.6.69 init sandbox/<slug> --non-interactive --example blank
```

From a new project directory:

```bash
npx --yes hyperframes@0.6.69 lint
npx --yes hyperframes@0.6.69 inspect
npx --yes hyperframes@0.6.69 preview
python3 ../../tools/video/resource_budget.py hyperframes -- npx --yes hyperframes@0.6.69 render --output renders/full_raw.mp4 --sdr
npx --yes hyperframes@0.6.69 doctor
```

The resource wrapper injects the worker budget; explicit supported worker settings remain validated by it. Other project nesting requires the correct repository-root path to the same wrapper. Raw render is an intermediate; video briefs continue through master.wav mux and final QA.

Use --help from the pinned version before relying on unfamiliar flags, validate/layout behavior, quality presets or newer registry features. Run relevant lint/layout checks, inspect actual keyframes and fix material problems; do not silently suppress errors. Resolve warnings according to the actual issue and project.

Fonts must be available offline, not merely named in CSS. Use design.md and local files to verify fonts. Keep preview URLs distinct from source links; don't start a preview just to satisfy a reporting template. User-requested samples may stop at preview; ordinary completed-video tasks do not.

TTS/ASR: [media adapter](../hyperframes-media/SKILL.md). Troubleshooting and resource mechanics: [operations](../../../tools/video/operations.md). Never initiate a skills/renderer update as automatic repair.
