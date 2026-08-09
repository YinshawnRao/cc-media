#!/usr/bin/env python3
"""Create fair-listening derivatives at a shared loudness target.

Raw model outputs remain untouched. These copies are only for A/B listening.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = EXPERIMENT_ROOT / "outputs"
TARGET_I = -18.0
TARGET_TP = -1.5
TARGET_LRA = 11.0


def normalize(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    # Trim only the two outer edges. A positive stop_periods value can mistake
    # an intentional in-sentence pause for EOF, so trim the tail by reversing,
    # applying the same start-only operation, and reversing back.
    edge_trim = "silenceremove=start_periods=1:start_duration=0.05:start_threshold=-55dB"
    audio_filter = (
        f"{edge_trim},areverse,{edge_trim},areverse,"
        f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}"
    )
    completed = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(source),
            "-af",
            audio_filter,
            "-ar",
            "24000",
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            str(target),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(f"ffmpeg failed for {source}: {completed.stderr.strip()}")


def main() -> int:
    manifest = json.loads((EXPERIMENT_ROOT / "manifest.json").read_text(encoding="utf-8"))
    jobs: list[tuple[Path, Path]] = []
    for persona in manifest["personas"]:
        source_root = OUTPUT_ROOT / "qwen3-tts" / persona["id"] / "ready"
        target_root = OUTPUT_ROOT / "listen-audio" / "qwen3-tts" / persona["id"]
        for name in ("showcase.wav", "mixed_language.wav", "voice-master.wav"):
            source = source_root / name
            if source.is_file():
                jobs.append((source, target_root / name))
    for voice in manifest["kokoro_voices"]:
        source = OUTPUT_ROOT / "kokoro" / "raw" / f"{voice}.wav"
        if source.is_file():
            jobs.append((source, OUTPUT_ROOT / "listen-audio" / "kokoro" / f"{voice}.wav"))

    if not jobs:
        raise SystemExit("no generated WAV files found")
    for index, (source, target) in enumerate(jobs, 1):
        print(f"[{index}/{len(jobs)}] {target.relative_to(EXPERIMENT_ROOT)}")
        normalize(source, target)
    print(f"prepared {len(jobs)} loudness-matched listening files at {TARGET_I} LUFS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
