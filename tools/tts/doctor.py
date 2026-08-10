#!/usr/bin/env python3
"""Check the fail-closed default CV002 runtime, model and voice assets."""

from __future__ import annotations

import argparse
import json
import subprocess
import wave
from pathlib import Path

from model_provenance import (
    ProvenanceError,
    create_full_hash_receipt,
    first_model_directory,
    manifest_path,
    receipt_path,
    validate_receipt,
)
from narrate import resolve_runtime
from text_normalizer import PronunciationPolicy, normalize_tts_text
from voice_registry import VoiceRegistry, file_sha256


TTS_ROOT = Path(__file__).resolve().parent


def probe_mlx_audio_version(python: Path) -> str:
    probe = (
        "import importlib.metadata as m; "
        "print(m.version('mlx-audio'), end='')"
    )
    completed = subprocess.run(
        [str(python), "-c", probe], capture_output=True, text=True, timeout=10
    )
    if completed.returncode != 0 or not completed.stdout.strip():
        raise ProvenanceError("cannot read mlx-audio distribution version")
    return completed.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--full-model-hash",
        action="store_true",
        help="SHA-256 every model file (about 2 GB of reads)",
    )
    args = parser.parse_args()
    errors: list[str] = []
    python: Path | None = None
    actual_mlx_audio_version: str | None = None

    try:
        registry = VoiceRegistry.load()
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print("TTS DOCTOR: FAIL")
        print(f"- cannot load TTS config/registry: {exc}")
        return 1

    try:
        python = resolve_runtime(registry.config, registry.config["qwen_base"]["engine"])
        actual_mlx_audio_version = probe_mlx_audio_version(python)
        expected_version = registry.config["qwen_base"]["mlx_audio_version"]
        if actual_mlx_audio_version != expected_version:
            raise ProvenanceError(
                "mlx-audio version mismatch: "
                f"expected {expected_version}, got {actual_mlx_audio_version}"
            )
        print(f"runtime: {python}  mlx-audio={actual_mlx_audio_version}")
    except (OSError, subprocess.TimeoutExpired, SystemExit, ProvenanceError) as exc:
        errors.append(str(exc))

    if actual_mlx_audio_version is not None:
        try:
            model = first_model_directory(registry.config, TTS_ROOT)
            if model is None:
                raise ProvenanceError("pinned Qwen Base model not found")
            source_manifest = manifest_path(registry.config, TTS_ROOT)
            verification_receipt = receipt_path(registry.config, TTS_ROOT)
            print(f"model: {model}")
            if args.full_model_hash:
                create_full_hash_receipt(
                    model_root=model,
                    manifest_file=source_manifest,
                    qwen=registry.config["qwen_base"],
                    mlx_audio_version=actual_mlx_audio_version,
                    tts_root=TTS_ROOT,
                )
            validation = validate_receipt(
                model_root=model,
                manifest_file=source_manifest,
                qwen=registry.config["qwen_base"],
                mlx_audio_version=actual_mlx_audio_version,
                tts_root=TTS_ROOT,
            )
            print(
                "model-verification: "
                f"files={validation['model_file_count']} "
                f"bytes={validation['model_total_bytes']} "
                f"full_tree_hash={validation['full_tree_hash_verified']} "
                f"receipt={verification_receipt}"
            )
        except (OSError, KeyError, TypeError, ProvenanceError) as exc:
            errors.append(str(exc))

    voices_root = TTS_ROOT / "voices"
    verified_voice_count = 0
    for voice in registry.voices:
        voice_id = str(voice.get("id", "<unknown>"))
        try:
            reference = voices_root / voice["reference_audio"]
            if not reference.is_file():
                errors.append(f"missing reference: {voice_id}")
                continue
            if file_sha256(reference) != voice["reference_sha256"]:
                errors.append(f"reference SHA mismatch: {voice_id}")
                continue
            with wave.open(str(reference), "rb") as handle:
                if handle.getnchannels() != 1 or handle.getframerate() != 24000:
                    errors.append(f"invalid reference WAV format: {voice_id}")
                    continue
            verified_voice_count += 1
        except (OSError, KeyError, TypeError, wave.Error) as exc:
            errors.append(f"cannot validate reference {voice_id}: {exc}")
    print(
        f"voice-assets: {verified_voice_count}/{len(registry.voices)} "
        "references verified"
    )

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
