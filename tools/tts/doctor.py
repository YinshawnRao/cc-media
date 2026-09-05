#!/usr/bin/env python3
"""Check the pinned Qwen runtime/model and the voice assets in requested scope."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import wave
from pathlib import Path

from model_provenance import (
    ProvenanceError,
    create_full_hash_receipt,
    first_model_directory,
    manifest_path,
    validate_receipt,
)
from narrate import resolve_runtime
from text_normalizer import PronunciationPolicy, normalize_tts_text
from voice_registry import VoiceRegistry, file_sha256


TTS_ROOT = Path(__file__).resolve().parent
VERSION_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+!-]{0,63}")


class VoiceScopeError(ValueError):
    """One fixed, non-sensitive voice-selector failure category."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


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
    version = completed.stdout.strip()
    if VERSION_RE.fullmatch(version) is None:
        raise ProvenanceError("mlx-audio returned an invalid version token")
    return version


def error_kind(exc: BaseException) -> str:
    """Return a stable diagnostic class without exposing exception text."""

    if isinstance(exc, subprocess.TimeoutExpired):
        return "timeout"
    if isinstance(exc, json.JSONDecodeError):
        return "invalid-json"
    if isinstance(exc, wave.Error):
        return "invalid-wav"
    if isinstance(exc, ProvenanceError):
        return "provenance"
    if isinstance(exc, OSError):
        return "io"
    if isinstance(exc, (KeyError, TypeError, ValueError)):
        return "invalid-config"
    if isinstance(exc, SystemExit):
        return "runtime-unavailable"
    return "unexpected"


def voices_for_scope(
    registry: VoiceRegistry,
    *,
    selector: str | None,
    full_library: bool,
) -> tuple[list[dict], dict, str]:
    """Return the voice assets that this doctor invocation must validate."""

    if selector is None or full_library:
        preflight_voice = registry.by_id(registry.preflight_id)
        if preflight_voice is None:
            raise ValueError(f"preflight voice is not enabled: {registry.preflight_id}")
        if full_library:
            return registry.voices, preflight_voice, "full-library"
        return [preflight_voice], preflight_voice, "preflight"

    voice, _ = registry.exact_selector(selector)
    if voice is None:
        raise VoiceScopeError("unknown-selector")
    qwen_engine = registry.config["qwen_base"]["engine"]
    if voice.get("engine") != qwen_engine:
        raise VoiceScopeError("legacy-engine")
    return [voice], voice, "selected"


def validate_voice_assets(
    voices: list[dict],
    *,
    voices_root: Path,
) -> tuple[int, list[str]]:
    """Validate exact reference assets for the selected doctor scope."""

    errors: list[str] = []
    verified_voice_count = 0
    for voice in voices:
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
            errors.append(
                f"cannot validate reference {voice_id} [{error_kind(exc)}]"
            )
    return verified_voice_count, errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--full-model-hash",
        action="store_true",
        help="SHA-256 every model file (about 2 GB of reads)",
    )
    voice_scope = parser.add_mutually_exclusive_group()
    voice_scope.add_argument(
        "--voice",
        metavar="ID_OR_NAME",
        help="exact enabled Qwen voice ID/name/alias to audit instead of the preflight voice",
    )
    voice_scope.add_argument(
        "--full-library",
        action="store_true",
        help="audit every enabled numbered voice reference instead of one selected voice",
    )
    parser.add_argument(
        "--check-mixed-script",
        action="store_true",
        help="also load and probe the Latin/mixed-script pronunciation policy",
    )
    args = parser.parse_args(argv)
    errors: list[str] = []
    python: Path | None = None
    actual_mlx_audio_version: str | None = None

    try:
        registry = VoiceRegistry.load()
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print("TTS DOCTOR: FAIL")
        print(f"- cannot load TTS config/registry [{error_kind(exc)}]")
        return 1

    try:
        voices, selected_voice, scope = voices_for_scope(
            registry,
            selector=args.voice,
            full_library=args.full_library,
        )
    except VoiceScopeError as exc:
        print("TTS DOCTOR: FAIL")
        if exc.reason == "unknown-selector":
            print("- --voice must exactly match an enabled CV voice ID/name/alias")
        else:
            print(
                "- --voice only audits numbered Qwen voices; "
                "the selected voice uses a legacy engine"
            )
        return 1
    except (KeyError, TypeError, ValueError) as exc:
        print("TTS DOCTOR: FAIL")
        print(f"- voice scope is invalid [{error_kind(exc)}]")
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
        print(f"runtime: pinned-qwen-python mlx-audio={actual_mlx_audio_version}")
    except (OSError, subprocess.TimeoutExpired, SystemExit, ProvenanceError) as exc:
        errors.append(
            "runtime verification failed "
            f"[{error_kind(exc)}]; restore the pinned runtime and rerun doctor"
        )

    if actual_mlx_audio_version is not None:
        try:
            model = first_model_directory(registry.config, TTS_ROOT)
            if model is None:
                raise ProvenanceError("pinned Qwen Base model not found")
            source_manifest = manifest_path(registry.config, TTS_ROOT)
            print("model: pinned-qwen-base")
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
                "receipt=verified"
            )
        except (OSError, KeyError, TypeError, ProvenanceError) as exc:
            errors.append(
                "model/manifest/receipt verification failed "
                f"[{error_kind(exc)}]; restore pinned assets or rebuild the receipt"
            )

    verified_voice_count, voice_errors = validate_voice_assets(
        voices,
        voices_root=TTS_ROOT / "voices",
    )
    errors.extend(voice_errors)
    print(
        f"voice-assets: {verified_voice_count}/{len(voices)} references verified "
        f"scope={scope} ids={','.join(str(voice['id']) for voice in voices)}"
    )

    if args.check_mixed_script:
        try:
            policy = PronunciationPolicy.load()
            probe = normalize_tts_text("今天重听BEYOND五首作品", policy=policy)
            if probe.normalized_text != "今天重听Beyond五首作品":
                errors.append(
                    "pronunciation normalization probe failed [unexpected-output]"
                )
            print("text-normalization: policy=loaded probe=BEYOND→Beyond")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(
                "invalid pronunciation policy "
                f"[{error_kind(exc)}]; repair the policy file and rerun doctor"
            )
    else:
        print(
            "text-normalization: SKIP "
            "(use --check-mixed-script for the optional mixed-script audit)"
        )

    if errors:
        print("TTS DOCTOR: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print(
        f"TTS DOCTOR: PASS preflight={registry.preflight_id} "
        f"selected={selected_voice['id']} scope={scope}"
    )
    return 0


def cli(argv: list[str] | None = None) -> int:
    """Run the CLI without exposing an unexpected exception payload."""

    try:
        return main(argv)
    except SystemExit:
        raise
    except Exception:
        print("TTS DOCTOR: FAIL")
        print("- unexpected doctor failure [unexpected]; inspect pinned local assets")
        return 1


if __name__ == "__main__":
    raise SystemExit(cli())
