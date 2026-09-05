---
name: website-to-hyperframes
description: Capture a website and use its verified visuals in a cc-media video when the user explicitly asks for a website tour or website-based video. A bare link is not a video request.
---

# Website video in cc-media

Use the site's real content and assets to inform the requested video. Repository [Runbook](../../../tools/video/README.md) controls production, Qwen narration, pin, media paths and final QA; this skill does not add provider choices or mandatory approval stages.

Capture what is needed for the brief using available read-only browser/capture capabilities. Record actual asset origins and inspect the screenshots. Ask only for missing required access/input; don't change site state or publish anything as part of capture.

Write a concise design/script if useful, then build with [hyperframes](../hyperframes/SKILL.md). Choose style, beat count and format from the brief/context. Do not insert captions or generic background music by default. New narration uses [central Qwen](../../../tools/tts/README.md).

Capture implementation examples are in [step-0-capture](references/step-0-capture.md); composition techniques in [beat builder](references/beat-builder-guide.md). These are optional upstream references, not a second workflow or version-support guarantee. Confirm availability against the project pin.

Verify key visuals and audio, render and mux as requested, then complete the applicable repository gates. A completed-video brief ends with MP4 and publishing copy; preview-only handoff requires a sample/preview request. Report real limitations that affect delivery, without mandatory boilerplate sections.
