#!/usr/bin/env python3
"""Generate all current cc-media Kokoro Chinese voices with one fair test line."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
import wave
from pathlib import Path


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = EXPERIMENT_ROOT.parents[3]
DEFAULT_MANIFEST = EXPERIMENT_ROOT / "manifest.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def wav_info(path: Path) -> dict:
    with wave.open(str(path), "rb") as handle:
        return {
            "channels": handle.getnchannels(),
            "sample_rate_hz": handle.getframerate(),
            "sample_width_bytes": handle.getsampwidth(),
            "frames": handle.getnframes(),
            "duration_seconds": handle.getnframes() / handle.getframerate(),
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))

    python = REPO_ROOT / "tools" / "tts" / "venv" / "bin" / "python"
    narrator = REPO_ROOT / "tools" / "tts" / "narrate.py"
    if not python.is_file() or not narrator.is_file():
        raise SystemExit("current Kokoro runtime is missing; see tools/tts/README.md")

    out_root = EXPERIMENT_ROOT / "outputs" / "kokoro" / "raw"
    out_root.mkdir(parents=True, exist_ok=True)
    records = []
    text = manifest["texts"]["showcase"]
    for index, voice in enumerate(manifest["kokoro_voices"], 1):
        output = out_root / f"{voice}.wav"
        started = time.perf_counter()
        if args.force or not output.is_file():
            print(f"[{index}/{len(manifest['kokoro_voices'])}] Kokoro {voice}")
            subprocess.run(
                [
                    str(python),
                    str(narrator),
                    text,
                    "--voice",
                    voice,
                    "--speed",
                    "1.0",
                    "-o",
                    str(output),
                ],
                cwd=REPO_ROOT,
                check=True,
            )
            cache_hit = False
        else:
            print(f"[{index}/{len(manifest['kokoro_voices'])}] reuse {voice}")
            cache_hit = True
        records.append(
            {
                "voice": voice,
                "text": text,
                "output": str(output.relative_to(EXPERIMENT_ROOT)),
                "sha256": sha256(output),
                "wav": wav_info(output),
                "elapsed_seconds": time.perf_counter() - started,
                "cache_hit": cache_hit,
            }
        )

    report = {
        "schema_version": "1.0.0",
        "engine": "current cc-media Kokoro + misaki[zh]",
        "entrypoint": "tools/tts/narrate.py",
        "voices": records,
    }
    path = EXPERIMENT_ROOT / "qa" / "kokoro-generation-report.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
