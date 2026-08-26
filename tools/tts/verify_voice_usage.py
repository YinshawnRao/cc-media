#!/usr/bin/env python3
"""Fail-closed gate for one project's resolved voice and generated sidecars."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import stat
import subprocess
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from model_provenance import (
    PORTABLE_CLAIM_KEYS,
    ProvenanceError,
    canonical_sha256,
    manifest_path,
    model_candidates,
    validate_receipt,
)
from narrate import resolve_runtime
from qwen_contract import qwen_sidecar_contract_errors
from voice_registry import VoiceRegistry


TTS_ROOT = Path(__file__).resolve().parent
BYPASS_PATTERNS = {
    "direct Kokoro import": re.compile(r"(?:from\s+kokoro\s+import|import\s+kokoro)"),
    "direct KPipeline call": re.compile(r"\bKPipeline\s*\("),
    "hardcoded VOICE constant": re.compile(r"(?m)^\s*VOICE\s*="),
}
PORTABLE_VALIDATION_KEYS = PORTABLE_CLAIM_KEYS + (
    "portable_claim_sha256",
    "full_tree_hash_verified",
)


@dataclass(frozen=True)
class SidecarEvidence:
    """Validated sidecar data safe for higher-level project gates to consume."""

    relative_path: str
    input_text: str
    output_relative_path: str
    provenance_mode: str
    duration_seconds: float


@dataclass(frozen=True)
class VerificationResult:
    """Pure API result. Library callers never need to parse CLI output."""

    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    sidecars: tuple[SidecarEvidence, ...]
    voice_id: str | None

    @property
    def ok(self) -> bool:
        return not self.errors

    @property
    def sidecar_count(self) -> int:
        return len(self.sidecars)

    @property
    def provenance_modes(self) -> tuple[str, ...]:
        return tuple(sorted({item.provenance_mode for item in self.sidecars}))


class VoiceGateError(ValueError):
    """Raised internally for project-closure or evidence violations."""


def sidecar_input_text(value: dict) -> str | None:
    """Return the original narration text, before optional pronunciation rewriting."""

    candidate = value.get("source_text") if "source_text" in value else value.get("text")
    return candidate if isinstance(candidate, str) and candidate.strip() else None


def _project_root(value: Path) -> Path:
    absolute = Path(os.path.abspath(value))
    try:
        resolved = absolute.resolve(strict=True)
    except OSError as exc:
        raise VoiceGateError(f"cannot resolve project root: {exc}") from exc
    if resolved != absolute:
        raise VoiceGateError("project root or one of its parents must not be a symlink")
    try:
        info = absolute.lstat()
    except OSError as exc:
        raise VoiceGateError(f"cannot inspect project root: {exc}") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise VoiceGateError("project root must be a real directory, not a symlink")
    return absolute


def _closed_file(
    project: Path,
    candidate: Path,
    *,
    base: Path | None = None,
    label: str,
) -> Path:
    if candidate.is_absolute():
        lexical = Path(os.path.abspath(candidate))
    else:
        lexical = Path(os.path.abspath((base or project) / candidate))
    try:
        relative = lexical.relative_to(project)
    except ValueError as exc:
        raise VoiceGateError(f"{label} is outside the project") from exc
    cursor = project
    for index, part in enumerate(relative.parts):
        cursor = cursor / part
        try:
            info = cursor.lstat()
        except OSError as exc:
            raise VoiceGateError(f"cannot inspect {label}: {exc}") from exc
        if stat.S_ISLNK(info.st_mode):
            raise VoiceGateError(f"{label} or one of its parents must not be a symlink")
        is_last = index == len(relative.parts) - 1
        if is_last and not stat.S_ISREG(info.st_mode):
            raise VoiceGateError(f"{label} must be a regular file")
        if not is_last and not stat.S_ISDIR(info.st_mode):
            raise VoiceGateError(f"{label} parent is not a directory")
    if not relative.parts:
        raise VoiceGateError(f"{label} must name a file inside the project")
    return lexical


def _read_closed_file(path: Path, *, label: str) -> bytes:
    before = path.lstat()
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise VoiceGateError(f"cannot open {label}: {exc}") from exc
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise VoiceGateError(f"{label} must be a regular file")
        if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
            raise VoiceGateError(f"{label} changed while opening")
        with os.fdopen(descriptor, "rb") as handle:
            descriptor = -1
            raw = handle.read()
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    after = path.lstat()
    before_and_after = (
        opened.st_dev,
        opened.st_ino,
        opened.st_size,
        opened.st_mtime_ns,
        opened.st_ctime_ns,
    )
    current = (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    )
    if current != before_and_after:
        raise VoiceGateError(f"{label} changed while reading")
    return raw


def _json_object(raw: bytes, *, label: str) -> dict:
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VoiceGateError(f"{label} is not valid UTF-8 JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise VoiceGateError(f"{label} must contain a JSON object")
    return value


def _project_files(project: Path) -> tuple[list[Path], list[str]]:
    files: list[Path] = []
    errors: list[str] = []
    for current, directory_names, file_names in os.walk(project, followlinks=False):
        current_path = Path(current)
        kept: list[str] = []
        for name in directory_names:
            child = current_path / name
            try:
                info = child.lstat()
            except OSError as exc:
                errors.append(f"cannot inspect project directory {child.relative_to(project)}: {exc}")
                continue
            if stat.S_ISLNK(info.st_mode):
                errors.append(
                    f"project directory must not be a symlink: {child.relative_to(project)}"
                )
                continue
            kept.append(name)
        directory_names[:] = kept
        files.extend(current_path / name for name in file_names)
    return files, errors


def _probe_mlx_audio_version(python: Path) -> str:
    probe = "import importlib.metadata as m; print(m.version('mlx-audio'), end='')"
    try:
        completed = subprocess.run(
            [str(python), "-c", probe],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ProvenanceError(f"cannot probe mlx-audio distribution version: {exc}") from exc
    if completed.returncode != 0 or not completed.stdout.strip():
        raise ProvenanceError("cannot read mlx-audio distribution version")
    return completed.stdout.strip()


def current_qwen_model_validation(registry: VoiceRegistry) -> dict:
    """Validate this workstation's pinned Qwen model and return its portable claim."""

    try:
        python = resolve_runtime(registry.config, registry.config["qwen_base"]["engine"])
    except SystemExit as exc:
        raise ProvenanceError(str(exc)) from exc
    version = _probe_mlx_audio_version(python)
    source_manifest = manifest_path(registry.config, TTS_ROOT)
    rejected: list[str] = []
    for candidate in model_candidates(registry.config, TTS_ROOT):
        if not candidate.is_dir():
            rejected.append(f"{candidate} (missing directory)")
            continue
        try:
            return validate_receipt(
                model_root=candidate,
                manifest_file=source_manifest,
                qwen=registry.config["qwen_base"],
                mlx_audio_version=version,
                tts_root=TTS_ROOT,
            )
        except (OSError, ProvenanceError) as exc:
            rejected.append(f"{candidate} ({exc})")
    rendered = "; ".join(rejected) if rejected else "no configured model candidates"
    raise ProvenanceError(f"no current trusted Qwen model validation: {rendered}")


def _validate_portable_model_evidence(
    sidecar: dict,
    *,
    relative_sidecar: str,
    current_validation: dict,
    errors: list[str],
) -> None:
    validation = sidecar.get("model_validation")
    if not isinstance(validation, dict):
        errors.append(f"{relative_sidecar} has invalid model validation")
        return
    if not re.fullmatch(r"[0-9a-f]{64}", str(validation.get("receipt_sha256", ""))):
        errors.append(f"{relative_sidecar} has an invalid receipt hash")
    claim = {key: validation.get(key) for key in PORTABLE_CLAIM_KEYS}
    if validation.get("portable_claim_sha256") != canonical_sha256(claim):
        errors.append(f"{relative_sidecar} has an internally inconsistent portable claim")
    for key in PORTABLE_VALIDATION_KEYS:
        if validation.get(key) != current_validation.get(key):
            errors.append(f"{relative_sidecar} model validation mismatch: {key}")


def verify_project_voice(
    project: Path,
    selection_path: Path,
    *,
    registry: VoiceRegistry | None = None,
    current_model_validation: dict | None = None,
    model_validation_loader: Callable[[VoiceRegistry], dict] = current_qwen_model_validation,
    allow_legacy_qwen_sidecars: bool = False,
) -> VerificationResult:
    """Validate a project's selection and every TTS sidecar without printing/exiting.

    Production callers omit ``current_model_validation`` and the gate validates the
    pinned local model receipt lazily when it encounters a current Qwen sidecar.
    Tests may inject a synthetic trusted validation object without loading a model.
    """

    errors: list[str] = []
    warnings: list[str] = []
    evidence: list[SidecarEvidence] = []
    expected: str | None = None
    try:
        project = _project_root(project)
    except VoiceGateError as exc:
        return VerificationResult((str(exc),), (), (), None)
    try:
        registry = registry or VoiceRegistry.load()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return VerificationResult((f"cannot load voice registry: {exc}",), (), (), None)
    try:
        selection_candidate = selection_path
        if not selection_path.is_absolute():
            cwd_candidate = Path(os.path.abspath(selection_path))
            try:
                cwd_candidate.lstat()
            except FileNotFoundError:
                pass
            except OSError as exc:
                return VerificationResult(
                    (f"cannot inspect voice selection: {exc}",), (), (), None
                )
            else:
                selection_candidate = cwd_candidate
        selection_file = _closed_file(
            project,
            selection_candidate,
            label="voice selection",
        )
        selection = _json_object(
            _read_closed_file(selection_file, label="voice selection"),
            label="voice selection",
        )
    except (OSError, VoiceGateError) as exc:
        return VerificationResult((str(exc),), (), (), None)

    if not registry.accepts_selection_hashes(selection):
        errors.append("voice-selection.json config/registry hashes are stale")
    expected_value = selection.get("resolved_voice_id")
    if not isinstance(expected_value, str) or not expected_value.strip():
        errors.append("voice-selection.json resolved_voice_id must be non-empty")
        expected = None
    else:
        expected = expected_value
    expected_voice: dict | None = None
    is_kokoro = bool(expected and expected.startswith("kokoro:"))
    if is_kokoro:
        legacy_voice = registry.legacy_voice(expected or "")
        expected_engine = registry.config["legacy_kokoro"]["engine"]
        expected_model_id = registry.config["legacy_kokoro"]["model_id"]
        if legacy_voice is None:
            errors.append(f"voice-selection.json contains unknown legacy voice: {expected}")
        if selection.get("fallback") is not False:
            errors.append("legacy Kokoro selection must be an explicit non-fallback choice")
    else:
        expected_voice = registry.by_id(expected or "")
        expected_engine = expected_voice.get("engine") if expected_voice else None
        expected_model_id = registry.config["qwen_base"]["model_id"]
        if expected_voice is None:
            errors.append(f"voice-selection.json contains unknown voice: {expected}")
    if selection.get("engine") != expected_engine:
        errors.append(
            f"voice-selection.json engine is {selection.get('engine')}, expected {expected_engine}"
        )

    project_files, scan_errors = _project_files(project)
    errors.extend(scan_errors)
    sidecars = sorted(
        (path for path in project_files if path.name.endswith(".wav.tts.json")),
        key=lambda path: path.as_posix(),
    )
    if not sidecars:
        errors.append("no generated *.wav.tts.json sidecars found")

    loaded_current_validation = current_model_validation
    current_validation_attempted = current_model_validation is not None
    excluded_parts = {"archive", ".deps", "node_modules", "venv", "qwen.venv"}

    for sidecar_candidate in sidecars:
        relative_hint = sidecar_candidate.relative_to(project).as_posix()
        try:
            sidecar = _closed_file(project, sidecar_candidate, label=relative_hint)
            value = _json_object(
                _read_closed_file(sidecar, label=relative_hint),
                label=relative_hint,
            )
        except (OSError, VoiceGateError) as exc:
            errors.append(str(exc))
            continue
        relative_sidecar = sidecar.relative_to(project).as_posix()
        sidecar_errors_before = len(errors)
        if value.get("resolved_voice_id") != expected:
            errors.append(
                f"{relative_sidecar} uses {value.get('resolved_voice_id')}, expected {expected}"
            )
        if value.get("selection") != selection:
            errors.append(f"{relative_sidecar} was not generated from this project selection")
        if value.get("engine") != expected_engine:
            errors.append(
                f"{relative_sidecar} uses engine {value.get('engine')}, expected {expected_engine}"
            )
        if value.get("model_id") != expected_model_id:
            errors.append(
                f"{relative_sidecar} uses model {value.get('model_id')}, expected {expected_model_id}"
            )

        original_text = sidecar_input_text(value)
        if original_text is None:
            errors.append(f"{relative_sidecar} has no canonical input narration text")
            original_text = ""
        normalized_text = value.get("text")
        if not isinstance(normalized_text, str) or not normalized_text:
            errors.append(f"{relative_sidecar} has no generated narration text")
        elif value.get("text_sha256") not in (
            None,
            hashlib.sha256(normalized_text.encode("utf-8")).hexdigest(),
        ):
            errors.append(f"{relative_sidecar} text SHA-256 does not match")

        output_value = value.get("output")
        legacy_absolute_output = isinstance(output_value, str) and Path(output_value).is_absolute()
        provenance_mode = "legacy_explicit" if is_kokoro else "qwen_portable_current"
        if expected_voice is not None:
            qwen = registry.config["qwen_base"]
            if value.get("model_revision") != qwen["model_revision"]:
                errors.append(f"{relative_sidecar} has the wrong Qwen model revision")
            if value.get("model_tree_sha256") != qwen["model_tree_sha256"]:
                errors.append(f"{relative_sidecar} has the wrong Qwen model tree hash")
            if value.get("reference_sha256") != expected_voice["reference_sha256"]:
                errors.append(f"{relative_sidecar} has the wrong reference-audio hash")
            if value.get("model_validation") is None:
                provenance_mode = "legacy_explicit"
                if not legacy_absolute_output or not allow_legacy_qwen_sidecars:
                    errors.append(
                        f"{relative_sidecar} lacks current model validation; historical absolute-path "
                        "Qwen sidecars require explicit legacy opt-in"
                    )
                else:
                    warnings.append(
                        f"{relative_sidecar} accepted as explicit legacy Qwen evidence without a receipt"
                    )
            else:
                if not current_validation_attempted:
                    current_validation_attempted = True
                    try:
                        loaded_current_validation = model_validation_loader(registry)
                    except (OSError, ValueError, SystemExit, ProvenanceError) as exc:
                        errors.append(f"cannot validate current local Qwen model: {exc}")
                if not isinstance(loaded_current_validation, dict):
                    errors.append(f"{relative_sidecar} cannot bind to a current local Qwen receipt")
                else:
                    _validate_portable_model_evidence(
                        value,
                        relative_sidecar=relative_sidecar,
                        current_validation=loaded_current_validation,
                        errors=errors,
                    )

        if not isinstance(output_value, str) or not output_value.strip():
            errors.append(f"{relative_sidecar} has no output WAV path")
            continue
        try:
            output = _closed_file(
                project,
                Path(output_value),
                base=sidecar.parent,
                label=f"{relative_sidecar} output WAV",
            )
            output_raw = _read_closed_file(
                output,
                label=f"{relative_sidecar} output WAV",
            )
        except (OSError, VoiceGateError) as exc:
            errors.append(str(exc))
            continue
        output_sha256 = hashlib.sha256(output_raw).hexdigest()
        if value.get("output_sha256") != output_sha256:
            errors.append(f"{relative_sidecar} output WAV hash does not match")
        actual_wav: dict | None = None
        try:
            with wave.open(io.BytesIO(output_raw), "rb") as handle:
                frames = handle.getnframes()
                sample_rate = handle.getframerate()
                actual_wav = {
                    "channels": handle.getnchannels(),
                    "sample_rate_hz": sample_rate,
                    "sample_width_bytes": handle.getsampwidth(),
                    "frames": frames,
                    "duration_seconds": frames / sample_rate,
                }
                if handle.getnchannels() != 1 or handle.getframerate() != 24000:
                    errors.append(f"{relative_sidecar} output is not 24kHz mono WAV")
                if frames <= 0:
                    errors.append(f"{relative_sidecar} output WAV is empty")
        except (OSError, wave.Error) as exc:
            errors.append(f"{relative_sidecar} output is not a readable WAV: {exc}")
        if (
            expected_voice is not None
            and value.get("model_validation") is not None
            and actual_wav is not None
        ):
            expected_output_name = sidecar.name[: -len(".tts.json")]
            for contract_error in qwen_sidecar_contract_errors(
                value,
                qwen=registry.config["qwen_base"],
                selection=selection,
                voice=expected_voice,
                reference_text=registry.registry["reference_text"],
                expected_output_name=expected_output_name,
                actual_output_sha256=output_sha256,
                actual_wav=actual_wav,
            ):
                errors.append(f"{relative_sidecar} {contract_error}")
        if len(errors) == sidecar_errors_before and actual_wav is not None:
            evidence.append(
                SidecarEvidence(
                    relative_path=relative_sidecar,
                    input_text=original_text,
                    output_relative_path=output.relative_to(project).as_posix(),
                    provenance_mode=provenance_mode,
                    duration_seconds=float(actual_wav["duration_seconds"]),
                )
            )

    for source_candidate in sorted(
        (path for path in project_files if path.suffix == ".py"),
        key=lambda path: path.as_posix(),
    ):
        relative = source_candidate.relative_to(project)
        if excluded_parts.intersection(relative.parts):
            continue
        try:
            source = _closed_file(project, source_candidate, label=relative.as_posix())
            text = _read_closed_file(source, label=relative.as_posix()).decode(
                "utf-8", errors="replace"
            )
        except (OSError, VoiceGateError) as exc:
            errors.append(str(exc))
            continue
        for label, pattern in BYPASS_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"{relative.as_posix()} bypasses central TTS: {label}")

    return VerificationResult(
        tuple(errors),
        tuple(warnings),
        tuple(evidence),
        expected,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection", required=True, type=Path)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument(
        "--allow-legacy-qwen-sidecars",
        action="store_true",
        help="explicitly accept historical absolute-path Qwen sidecars without receipt evidence",
    )
    args = parser.parse_args()
    result = verify_project_voice(
        args.project_root,
        args.selection,
        allow_legacy_qwen_sidecars=args.allow_legacy_qwen_sidecars,
    )
    if not result.ok:
        print("VOICE GATE: FAIL")
        for error in result.errors:
            print(f"- {error}")
        return 1
    modes = ",".join(result.provenance_modes) or "none"
    print(
        f"VOICE GATE: PASS  voice={result.voice_id} "
        f"sidecars={result.sidecar_count} provenance={modes}"
    )
    for warning in result.warnings:
        print(f"- WARNING: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
