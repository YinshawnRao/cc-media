#!/usr/bin/env python3
"""Run the fixed, already-cached Whisper small model without network access.

The final-video gate invokes this module with the repository's local TTS Python
environment.  A JSON request is read from stdin and a deterministic receipt is
written to stdout.  The model name is intentionally not configurable: changing
the verifier model is a contract change, not a per-project escape hatch.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

try:
    from . import resource_budget
except ImportError:  # Direct script execution.
    import resource_budget  # type: ignore[no-redef]


# Must run before importing vocal_segments -> Whisper/Torch/numeric libraries.
ASR_RESOURCE_BUDGET = resource_budget.configure_asr_environment()


MODEL = "small"
CHECKPOINT_SHA256 = "9ecf779972d90ba49c06d968637d720dd632c55bbf19d441fb42bf17a411e794"
WHISPER_DISTRIBUTION = "openai-whisper"
WHISPER_VERSION = "20250625"
LONG_AUDIO_THRESHOLD_SECONDS = 90.0
WINDOW_SECONDS = 20.0
WINDOW_STEP_SECONDS = 10.0


def _transcribe_options(language: str) -> dict[str, Any]:
    return {
        "language": language,
        "task": "transcribe",
        "fp16": False,
        "temperature": 0,
        "condition_on_previous_text": False,
        "word_timestamps": True,
        "verbose": None,
    }


def _media_duration(path: Path) -> float | None:
    """Return current media duration, retaining the legacy path on probe failure."""

    try:
        completed = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=nk=1:nw=1",
                str(path),
            ],
            text=True,
            capture_output=True,
            timeout=30,
        )
        if completed.returncode != 0:
            return None
        duration = float(completed.stdout.strip())
    except (OSError, subprocess.TimeoutExpired, ValueError):
        return None
    return duration if math.isfinite(duration) and duration > 0 else None


def _transcribe_long_source(model: Any, path: Path, language: str) -> dict[str, Any]:
    """Transcribe long musical programs in overlapping fixed windows.

    Whisper's free-running timestamp seek can jump across speech after long sung
    passages. Fixed overlapping windows retain the pinned model and options
    while ensuring each part of the source is decoded. Equivalent overlapping
    results are de-duplicated before absolute source timestamps are emitted.
    """

    from whisper.audio import SAMPLE_RATE, load_audio

    audio = load_audio(str(path))
    total_seconds = len(audio) / SAMPLE_RATE
    step_samples = int(WINDOW_STEP_SECONDS * SAMPLE_RATE)
    window_samples = int(WINDOW_SECONDS * SAMPLE_RATE)
    raw_segments: list[dict[str, Any]] = []
    for start_sample in range(0, len(audio), step_samples):
        end_sample = min(len(audio), start_sample + window_samples)
        start_sec = start_sample / SAMPLE_RATE
        transcript = model.transcribe(
            audio[start_sample:end_sample],
            **_transcribe_options(language),
        )
        rows = transcript.get("segments", [])
        if not isinstance(rows, list):
            raise ValueError("Whisper window segments are invalid")
        for raw in rows:
            if not isinstance(raw, dict):
                raise ValueError("Whisper window segment is invalid")
            local_start = _finite_number(raw.get("start"), "segment.start")
            local_end = _finite_number(raw.get("end"), "segment.end")
            text = raw.get("text")
            raw_segments.append(
                {
                    **raw,
                    "start": start_sec + local_start,
                    "end": min(total_seconds, start_sec + local_end),
                }
            )
    raw_segments.sort(key=lambda row: (float(row["start"]), float(row["end"]), str(row.get("text", ""))))
    deduplicated: list[dict[str, Any]] = []
    for candidate in raw_segments:
        candidate_start = float(candidate["start"])
        candidate_end = float(candidate["end"])
        candidate_text = str(candidate.get("text", "")).strip()
        duplicate = False
        for existing in reversed(deduplicated):
            existing_end = float(existing["end"])
            if existing_end < candidate_start - WINDOW_SECONDS:
                break
            if str(existing.get("text", "")).strip() != candidate_text:
                continue
            overlap = min(existing_end, candidate_end) - max(float(existing["start"]), candidate_start)
            shorter = min(existing_end - float(existing["start"]), candidate_end - candidate_start)
            if shorter > 0 and overlap / shorter >= 0.6:
                duplicate = True
                break
        if not duplicate:
            deduplicated.append(candidate)
    transcript_parts = [str(row.get("text", "")).strip() for row in deduplicated if str(row.get("text", "")).strip()]
    return {"text": " ".join(transcript_parts), "segments": deduplicated}


def _sha256_file(path: Path) -> str:
    before = path.stat()
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    after = path.stat()
    before_signature = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
    )
    after_signature = (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    )
    if before_signature != after_signature:
        raise ValueError("Whisper checkpoint changed while hashing")
    return digest.hexdigest()


def verify_toolchain_identity(
    checkpoint: Path,
    *,
    hash_reader: Callable[[Path], str] = _sha256_file,
    version_reader: Callable[[str], str] = importlib.metadata.version,
) -> dict[str, str]:
    """Verify the pinned local checkpoint and distribution before model loading.

    The injectable readers keep unit tests synthetic; production always reads the
    complete checkpoint and installed distribution metadata.
    """

    if checkpoint.is_symlink() or not checkpoint.is_file():
        raise ValueError("fixed Whisper checkpoint is missing or is a symlink")
    actual_hash = hash_reader(checkpoint)
    if actual_hash != CHECKPOINT_SHA256:
        raise ValueError(
            "Whisper checkpoint SHA-256 mismatch: "
            f"expected {CHECKPOINT_SHA256}, got {actual_hash}"
        )
    try:
        actual_version = version_reader(WHISPER_DISTRIBUTION)
    except importlib.metadata.PackageNotFoundError as exc:
        raise ValueError("openai-whisper distribution metadata is unavailable") from exc
    if actual_version != WHISPER_VERSION:
        raise ValueError(
            "openai-whisper version mismatch: "
            f"expected {WHISPER_VERSION}, got {actual_version}"
        )
    return {
        "checkpoint_sha256": actual_hash,
        "openai_whisper_version": actual_version,
    }


def _load_pinned_model(checkpoint: Path) -> Any:
    try:
        from .vocal_segments import load_whisper_model
    except ImportError:  # Direct script execution.
        from vocal_segments import load_whisper_model  # type: ignore[no-redef]

    return load_whisper_model(str(checkpoint), "cpu")


def _strict_object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate object key {key!r}")
        result[key] = value
    return result


def _reject_constant(token: str) -> None:
    raise ValueError(f"non-standard numeric constant {token}")


def _finite_number(value: Any, label: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{label} must be finite")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label} must be finite")
    return result


def run(
    request: dict[str, Any],
    *,
    checkpoint: Path | None = None,
    identity_loader: Callable[[Path], dict[str, str]] = verify_toolchain_identity,
    model_loader: Callable[[Path], Any] = _load_pinned_model,
) -> dict[str, Any]:
    if request.get("model") != MODEL:
        raise ValueError(f"model must be fixed to {MODEL}")
    language = request.get("language")
    if not isinstance(language, str) or not language.strip():
        raise ValueError("language must be a non-empty string")
    jobs = request.get("jobs")
    if not isinstance(jobs, list) or not jobs:
        raise ValueError("jobs must be a non-empty array")

    checkpoint = checkpoint or (Path.home() / ".cache" / "whisper" / f"{MODEL}.pt")
    identity = identity_loader(checkpoint)
    model = model_loader(checkpoint)
    results: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for job_index, raw in enumerate(jobs):
        if not isinstance(raw, dict):
            raise ValueError(f"jobs[{job_index}] must be an object")
        job_id = raw.get("id")
        raw_path = raw.get("path")
        if not isinstance(job_id, str) or not job_id or job_id in seen_ids:
            raise ValueError(f"jobs[{job_index}].id must be unique and non-empty")
        if not isinstance(raw_path, str) or not raw_path:
            raise ValueError(f"jobs[{job_index}].path must be non-empty")
        path = Path(raw_path)
        if not path.is_file():
            raise ValueError(f"jobs[{job_index}].path is not a file")
        seen_ids.add(job_id)
        source_duration = _media_duration(path)
        if source_duration is not None and source_duration > LONG_AUDIO_THRESHOLD_SECONDS:
            transcript = _transcribe_long_source(model, path, language)
        else:
            transcript = model.transcribe(str(path), **_transcribe_options(language))
        raw_segments = transcript.get("segments", [])
        if not isinstance(raw_segments, list):
            raise ValueError(f"Whisper segments for {job_id} are invalid")
        segments: list[dict[str, Any]] = []
        for segment_index, raw_segment in enumerate(raw_segments):
            if not isinstance(raw_segment, dict):
                raise ValueError(f"Whisper segment {job_id}:{segment_index} is invalid")
            start = _finite_number(raw_segment.get("start"), "segment.start")
            end = _finite_number(raw_segment.get("end"), "segment.end")
            text = raw_segment.get("text")
            if start < 0 or end < start or not isinstance(text, str):
                raise ValueError(f"Whisper segment {job_id}:{segment_index} is invalid")
            # Whisper can emit zero-duration or blank bookkeeping segments at
            # repeated sung syllables. They cannot carry temporal/textual
            # evidence, so exclude them while keeping malformed ranges strict.
            if end == start or not text.strip():
                continue
            segments.append(
                {
                    "id": f"{job_id}:{segment_index:06d}",
                    "start_sec": round(start, 6),
                    "end_sec": round(end, 6),
                    "text": text.strip(),
                }
            )
        text = transcript.get("text")
        if not isinstance(text, str):
            text = " ".join(segment["text"] for segment in segments)
        results.append(
            {
                "source_id": job_id,
                "transcript": text.strip(),
                "segments": segments,
            }
        )
    return {
        "engine": "openai-whisper",
        "model": MODEL,
        "language": language,
        **identity,
        "results": results,
    }


def main() -> int:
    try:
        request = json.loads(
            sys.stdin.read(),
            parse_constant=_reject_constant,
            object_pairs_hook=_strict_object_pairs,
        )
        if not isinstance(request, dict):
            raise ValueError("request must be an object")
        result = run(request)
    except Exception as exc:
        print(f"offline ASR failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    json.dump(result, sys.stdout, ensure_ascii=False, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
