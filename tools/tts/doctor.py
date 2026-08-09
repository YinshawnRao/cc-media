#!/usr/bin/env python3
"""Check the fail-closed default CV002 runtime, model and voice assets."""

from __future__ import annotations

import argparse
import json
import os
import wave
from pathlib import Path

from narrate import resolve_runtime
from text_normalizer import PronunciationPolicy, normalize_tts_text
from voice_registry import VoiceRegistry, file_sha256


TTS_ROOT = Path(__file__).resolve().parent


def resolve_model(config: dict) -> Path | None:
    runtime = config["runtime"]
    candidates: list[Path] = []
    for env_name in runtime["qwen_base_model_envs"]:
        value = os.environ.get(env_name)
        if value:
            path = Path(value).expanduser()
            candidates.append(path if path.is_absolute() else path.absolute())
    for value in runtime["qwen_base_model_candidates"]:
        path = Path(value)
        candidates.append(path if path.is_absolute() else (TTS_ROOT / path).resolve())
    return next(
        (path for path in candidates if path.is_dir() and (path / "config.json").is_file()),
        None,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--full-model-hash",
        action="store_true",
        help="SHA-256 every model file (about 2 GB of reads)",
    )
    args = parser.parse_args()
    registry = VoiceRegistry.load()
    errors: list[str] = []

    try:
        python = resolve_runtime(registry.config, registry.config["qwen_base"]["engine"])
        print(f"runtime: {python}")
    except SystemExit as exc:
        errors.append(str(exc))

    model = resolve_model(registry.config)
    if model is None:
        errors.append("pinned Qwen Base model not found")
    else:
        print(f"model: {model}")
        manifest_path = TTS_ROOT / registry.config["qwen_base"]["model_file_manifest"]
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for record in manifest["files"]:
            path = model / record["path"]
            if not path.is_file():
                errors.append(f"missing model file: {record['path']}")
                continue
            if path.stat().st_size != record["bytes"]:
                errors.append(f"model size mismatch: {record['path']}")
                continue
            if args.full_model_hash and file_sha256(path) != record["sha256"]:
                errors.append(f"model SHA mismatch: {record['path']}")
        print(
            f"model-manifest: files={manifest['file_count']} bytes={manifest['total_bytes']} "
            f"full_hash={args.full_model_hash}"
        )

    voices_root = TTS_ROOT / "voices"
    for voice in registry.voices:
        reference = voices_root / voice["reference_audio"]
        if not reference.is_file():
            errors.append(f"missing reference: {voice['id']}")
            continue
        if file_sha256(reference) != voice["reference_sha256"]:
            errors.append(f"reference SHA mismatch: {voice['id']}")
            continue
        with wave.open(str(reference), "rb") as handle:
            if handle.getnchannels() != 1 or handle.getframerate() != 24000:
                errors.append(f"invalid reference WAV format: {voice['id']}")
    print(f"voice-assets: {len(registry.voices)} references verified")

    try:
        policy = PronunciationPolicy.load()
        probe = normalize_tts_text("今天重听BEYOND五首作品", policy=policy)
        if probe.normalized_text != "今天重听Beyond五首作品":
            errors.append(
                "pronunciation normalization probe failed: "
                f"{probe.normalized_text!r}"
            )
        print(
            f"text-normalization: policy={policy.policy_id} "
            f"probe=BEYOND→Beyond"
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors.append(f"invalid pronunciation policy: {exc}")

    if errors:
        print("TTS DOCTOR: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print(
        f"TTS DOCTOR: PASS  default={registry.config['default_voice_id']} "
        f"name={registry.by_id(registry.default_id)['name']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
