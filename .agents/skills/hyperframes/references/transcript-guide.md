# Transcript use in cc-media

Read this only when a requested caption/editing task needs transcripts. ASR for production runs through tools/video/offline_asr.py, vocal_segments.py or central final QA; use the fixed toolchain and actual language. Do not switch to built-in HyperFrames transcription, an English-only default, or an external API as an automatic fallback.

Reuse a supplied transcript when appropriate. SRT/VTT usually provide phrase timing; per-word animation needs genuine word timestamps. Convert a copy to the format the pinned renderer supports, preserving the source text and time basis.

Check representative passages against the audio, especially lyrics, names, language switches, repeated tokens and implausible word spans. Instrumental gaps do not imply missing narration. Repair the source/analysis when needed; do not manufacture timestamps or silently delete words to make QA pass.

For captions, group by natural phrases and visible reading time. Clean confirmed non-speech artifacts only in the display copy. Preserve the original ASR artifact and hash-bound QA receipts unchanged. No transcript is a reason to run central ASR when required, not a reason to stop the whole video task or add unrequested subtitles.
