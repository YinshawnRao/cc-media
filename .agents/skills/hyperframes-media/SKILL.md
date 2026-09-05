---
name: hyperframes-media
description: Route cc-media narration to the central Qwen TTS scripts and transcription to the fixed local ASR tools; use optional background-removal reference when an actual cutout is needed.
---

# cc-media media adapter

Current narration is **Qwen3-TTS**, via tools/tts/narrate.py using the registered, previously produced reference voices. Do not use HyperFrames built-in TTS, KPipeline, a provider picker, or automatic Kokoro fallback. Follow [Qwen README](../../../tools/tts/README.md) only when generating new narration.

Reuse a project's voice-selection.json for every narrated segment. Resolve once and run doctor for the selected voice, not an additional unused preflight voice. Existing WAVs retain their recorded configuration. No narration means no TTS setup.

Transcription and vocal analysis use tools/video/offline_asr.py, vocal_segments.py or prepare_final_qa.py so runtime/model identity and resource budgets stay consistent. Use the actual language; do not run bare whisper or install another model from generic examples. Timestamp transcripts are evidence, not automatic permission to add captions. Captions require the user's request.

Mix with the repository FFmpeg resource entrypoint, preserve music/voice dynamics, post-mux master.wav, and inspect the final AAC audio. For the complete flow see [video Runbook](../../../tools/video/README.md).

For subject cutouts, consult [background removal](references/background-removal.md) only when needed. Verify that the current renderer/tool version supports the referenced operation; keep preprocessing separate from the Qwen/ASR pipeline.
