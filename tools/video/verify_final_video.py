#!/usr/bin/env python3
"""Fail-closed verification gate for a muxed final video.

The gate consumes one project-local QA manifest. It never downloads anything,
loads cookies, runs TTS, or claims to understand images. Mechanical checks are
performed with ffmpeg/ffprobe. Semantic visual states remain explicit,
hash-bound review data inside the manifest; ``--require-human-review`` is a
separate strict-mode opt-in.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any, Callable, NoReturn

try:
    from . import resource_budget
    from . import verify_project as authoring_contract
    from .outro_cta import FIXED_OUTRO_CTA
except ImportError:  # Direct ``python tools/video/verify_final_video.py`` execution.
    import resource_budget  # type: ignore[no-redef]
    import verify_project as authoring_contract  # type: ignore[no-redef]
    from outro_cta import FIXED_OUTRO_CTA  # type: ignore[no-redef]


SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
ALLOWED_VIDEO_CODECS = {"h264", "hevc"}
MP4_FORMAT_NAMES = {"mov", "mp4", "m4a", "3gp", "3g2", "mj2"}
NARRATION_MODES = {"structured", "free_exploration"}
REQUIRED_ASR_KINDS = ("final_aac_asr", "isolated_narration_asr")
REQUIRED_HUMAN_APPROVALS = ("visual_frames", "leakage", "release_safety")
RENDERS_DIRECTORY = "renders"
PINNED_WHISPER_CHECKPOINT_SHA256 = (
    "9ecf779972d90ba49c06d968637d720dd632c55bbf19d441fb42bf17a411e794"
)
PINNED_OPENAI_WHISPER_VERSION = "20250625"

SILENCE_NOISE_DB = -35.0
SILENCE_DETECT_MIN_SECONDS = 1.0
SILENCE_HARD_FAIL_SECONDS = 1.5
INTERVAL_MATCH_TOLERANCE_SECONDS = 0.20
STREAM_COVERAGE_TOLERANCE_SECONDS = 0.10
CHAPTER_TIMING_EPSILON_SECONDS = 0.05
FRAME_SAMPLE_TOLERANCE_SECONDS = 0.05
REVIEW_CLOCK_SKEW_SECONDS = 300
MIN_FINAL_AAC_BIT_RATE = 160_000
BLACK_DETECT_MIN_SECONDS = 0.50
BLACK_PIXEL_THRESHOLD = 0.10

DEFAULT_INTEGRATED_LUFS_MIN = -20.0
DEFAULT_INTEGRATED_LUFS_MAX = -10.0
DEFAULT_MAX_TRUE_PEAK_DBTP = -0.1
DEFAULT_MIN_MASTER_AAC_SDR_DB = 12.0
OFFLINE_ASR_TIMEOUT_PER_JOB_SECONDS = 600
OFFLINE_ASR_TIMEOUT_MAX_SECONDS = 900


class GateFailure(ValueError):
    """A deterministic verification failure safe to show to the caller."""


class HumanReviewRequired(RuntimeError):
    """Mechanical QA passed, but an explicitly strict run still needs a person."""

    def __init__(self, labels: tuple[str, ...]):
        self.labels = labels
        preview = ", ".join(labels[:5])
        if len(labels) > 5:
            preview += f", ... (+{len(labels) - 5})"
        super().__init__(
            f"{len(labels)} current human-review item(s) remain pending: {preview}"
        )


def fail(message: str) -> NoReturn:
    raise GateFailure(message)


@dataclass(frozen=True)
class Asset:
    label: str
    raw_path: str
    path: Path
    sha256: str


@dataclass(frozen=True)
class Chapter:
    key: str
    role: str
    start: float
    end: float
    requires_narration: bool


@dataclass(frozen=True)
class Interval:
    start: float
    end: float

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)


@dataclass(frozen=True)
class Loudness:
    integrated_lufs: float
    true_peak_dbtp: float


@dataclass(frozen=True)
class VideoDecodeReceipt:
    frame_count: int
    first_pts_sec: float
    end_pts_sec: float
    frame_records_sha256: str


@dataclass(frozen=True)
class FrameReceipt:
    pts_sec: float
    duration_sec: float
    rgb_sha256: str


@dataclass(frozen=True)
class VerificationSummary:
    final_path: str
    final_sha256: str
    duration_sec: float
    video_codec: str
    integrated_lufs: float
    true_peak_dbtp: float
    master_aac_sdr_db: float
    reviewed_silences: int
    reviewed_black_intervals: int
    human_review_advisories: tuple[str, ...]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def strict_json_loads(value: str, label: str) -> Any:
    def reject_constant(token: str) -> NoReturn:
        raise ValueError(f"non-standard numeric constant {token}")

    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, child in pairs:
            if key in result:
                raise ValueError(f"duplicate object key {key!r}")
            result[key] = child
        return result

    try:
        return json.loads(
            value,
            parse_constant=reject_constant,
            object_pairs_hook=unique_object,
        )
    except (json.JSONDecodeError, ValueError) as exc:
        fail(f"{label} is invalid JSON: {exc}")


def require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"{label} must be an object")
    return value


def require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        fail(f"{label} must be an array")
    return value


def require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        fail(f"{label} must be a non-empty string")
    return value


def starts_with_renders_directory(value: Any) -> bool:
    """Return whether a project-relative output starts with lowercase renders/."""

    if not isinstance(value, str) or not value.strip():
        return False
    candidate = Path(value)
    return (
        not candidate.is_absolute()
        and ".." not in candidate.parts
        and len(candidate.parts) >= 2
        and candidate.parts[0] == RENDERS_DIRECTORY
    )


def require_number(value: Any, label: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        fail(f"{label} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        fail(f"{label} must be a finite number")
    return result


def require_sha(value: Any, label: str) -> str:
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        fail(f"{label} must be 64 lowercase hexadecimal characters")
    return value


def resolve_project_file(project: Path, raw: Any, label: str) -> Path:
    """Resolve one existing regular file without following any symlink."""

    value = require_string(raw, label)
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        fail(f"{label} must be a project-relative path without '..'")

    root = project.resolve(strict=True)
    logical = root / candidate
    cursor = root
    for part in candidate.parts[:-1]:
        cursor = cursor / part
        if cursor.is_symlink():
            fail(f"{label} parent must not be a symlink: {value}")
    if logical.is_symlink():
        fail(f"{label} must not be a symlink: {value}")
    try:
        resolved = logical.resolve(strict=True)
        resolved.relative_to(root)
    except FileNotFoundError:
        fail(f"{label} does not exist: {value}")
    except ValueError:
        fail(f"{label} resolves outside the project: {value}")
    if not resolved.is_file():
        fail(f"{label} must be a regular file: {value}")
    return logical


def read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        fail(f"{label} cannot be read as UTF-8 JSON: {exc}")
    value = strict_json_loads(raw, label)
    return require_object(value, label)


def collect_project_file_inputs(project: Path, value: Any) -> dict[Path, str]:
    """Snapshot project-local files named anywhere in an authoring manifest."""

    found: dict[Path, str] = {}

    def visit(node: Any) -> None:
        if isinstance(node, dict):
            for child in node.values():
                visit(child)
            return
        if isinstance(node, list):
            for child in node:
                visit(child)
            return
        if not isinstance(node, str) or not node.strip():
            return
        candidate = Path(node)
        if candidate.is_absolute() or ".." in candidate.parts:
            return
        logical = project / candidate
        if logical.is_symlink() or not logical.is_file():
            return
        try:
            logical.resolve(strict=True).relative_to(project)
        except (FileNotFoundError, ValueError):
            return
        found[logical] = sha256_file(logical)

    visit(value)
    return found


def parse_asset(project: Path, value: Any, label: str) -> Asset:
    row = require_object(value, label)
    raw_path = require_string(row.get("path"), f"{label}.path")
    expected_hash = require_sha(row.get("sha256"), f"{label}.sha256")
    path = resolve_project_file(project, raw_path, f"{label}.path")
    actual_hash = sha256_file(path)
    if actual_hash != expected_hash:
        fail(f"{label} SHA-256 mismatch: manifest is stale")
    return Asset(label=label, raw_path=raw_path, path=path, sha256=actual_hash)


def parse_chapters(value: Any) -> list[Chapter]:
    rows = require_list(value, "chapters")
    if not rows:
        fail("chapters must not be empty")
    chapters: list[Chapter] = []
    seen: set[str] = set()
    previous_end = 0.0
    for index, raw in enumerate(rows):
        label = f"chapters[{index}]"
        row = require_object(raw, label)
        key = require_string(row.get("id"), f"{label}.id")
        if not KEY_RE.fullmatch(key):
            fail(f"{label}.id must match {KEY_RE.pattern}")
        if key in seen:
            fail(f"duplicate chapter id: {key}")
        seen.add(key)
        role = require_string(row.get("role"), f"{label}.role")
        start = require_number(row.get("start_sec"), f"{label}.start_sec")
        end = require_number(row.get("end_sec"), f"{label}.end_sec")
        if start < 0 or end <= start:
            fail(f"{label} must have 0 <= start_sec < end_sec")
        if index and start < previous_end - 0.001:
            fail(f"{label} overlaps the previous chapter")
        requires_narration = row.get("requires_narration")
        if not isinstance(requires_narration, bool):
            fail(f"{label}.requires_narration must be boolean")
        chapters.append(Chapter(key, role, start, end, requires_narration))
        previous_end = end
    return chapters


def parse_loudness_thresholds(value: Any) -> dict[str, float]:
    row = {} if value is None else require_object(value, "checks.loudness")
    minimum = require_number(
        row.get("integrated_lufs_min", DEFAULT_INTEGRATED_LUFS_MIN),
        "checks.loudness.integrated_lufs_min",
    )
    maximum = require_number(
        row.get("integrated_lufs_max", DEFAULT_INTEGRATED_LUFS_MAX),
        "checks.loudness.integrated_lufs_max",
    )
    true_peak = require_number(
        row.get("max_true_peak_dbtp", DEFAULT_MAX_TRUE_PEAK_DBTP),
        "checks.loudness.max_true_peak_dbtp",
    )
    if minimum < DEFAULT_INTEGRATED_LUFS_MIN:
        fail("loudness minimum may narrow but must not be below -20 LUFS")
    if maximum > DEFAULT_INTEGRATED_LUFS_MAX:
        fail("loudness maximum may narrow but must not be above -10 LUFS")
    if minimum >= maximum:
        fail("loudness integrated_lufs_min must be below integrated_lufs_max")
    if true_peak > DEFAULT_MAX_TRUE_PEAK_DBTP:
        fail("max_true_peak_dbtp may narrow but must remain below 0 dBTP")
    return {"minimum": minimum, "maximum": maximum, "true_peak": true_peak}


def parse_checks(value: Any) -> dict[str, Any]:
    row = require_object(value, "checks")
    codec = require_string(row.get("expected_video_codec"), "checks.expected_video_codec")
    if codec not in ALLOWED_VIDEO_CODECS:
        fail(f"checks.expected_video_codec must be one of {sorted(ALLOWED_VIDEO_CODECS)}")
    tolerance = require_number(
        row.get("duration_tolerance_sec", 0.50), "checks.duration_tolerance_sec"
    )
    if not 0 < tolerance <= 1.0:
        fail("checks.duration_tolerance_sec must be in (0, 1.0]")
    min_audio_sdr = require_number(
        row.get("min_master_aac_sdr_db", DEFAULT_MIN_MASTER_AAC_SDR_DB),
        "checks.min_master_aac_sdr_db",
    )
    if min_audio_sdr < DEFAULT_MIN_MASTER_AAC_SDR_DB:
        fail("min_master_aac_sdr_db may narrow but must not be below 12 dB")
    return {
        "expected_video_codec": codec,
        "duration_tolerance_sec": tolerance,
        "min_master_aac_sdr_db": min_audio_sdr,
        "loudness": parse_loudness_thresholds(row.get("loudness")),
    }


def normalized_text(value: str) -> str:
    return "".join(
        character.casefold()
        for character in unicodedata.normalize("NFKC", value)
        if not unicodedata.category(character).startswith(("P", "Z"))
    )


AUTHOR_ROLE_TO_QA_ROLE = {
    "intro": "intro",
    "transition": "transition",
    "work_outro": "outro",
    "outro_cta": "cta",
    "free": "free",
}


def parse_authoring_contract(
    project: Path,
    value: Any,
    narration_mode: str,
    authoring_verifier: Any,
    *,
    require_human_review: bool = False,
) -> tuple[Asset, dict[str, dict[str, Any]]]:
    asset = parse_asset(project, value, "authoring_manifest")
    errors = authoring_verifier(
        project,
        asset.raw_path,
        require_human_review=require_human_review,
    )
    if errors:
        fail("authoring project contract failed: " + " | ".join(errors))
    manifest = read_json(asset.path, "authoring_manifest")
    project_kind = require_string(
        manifest.get("project_kind"), "authoring_manifest.project_kind"
    )
    if narration_mode == "structured" and project_kind not in {"top_ranking", "narrative"}:
        fail("structured final QA requires a top_ranking or narrative authoring project")
    if narration_mode == "free_exploration" and project_kind != "free_exploration":
        fail("free_exploration final QA requires a free_exploration authoring project")

    rows = require_list(
        manifest.get("narration_sequence"),
        "authoring_manifest.narration_sequence",
    )
    narration: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(rows):
        label = f"authoring_manifest.narration_sequence[{index}]"
        row = require_object(raw, label)
        narration_id = require_string(row.get("id"), f"{label}.id")
        if narration_id in narration:
            fail(f"duplicate authoring narration id: {narration_id}")
        author_role = require_string(row.get("role"), f"{label}.role")
        if author_role not in AUTHOR_ROLE_TO_QA_ROLE:
            fail(f"{label}.role is not supported by final QA: {author_role}")
        text = require_string(row.get("text"), f"{label}.text")
        if not normalized_text(text):
            fail(f"{label}.text becomes empty after ASR normalization")
        if author_role == "outro_cta" and text != FIXED_OUTRO_CTA:
            fail(f"{label}.text must equal the canonical fixed outro CTA")
        wav_raw = require_string(row.get("wav"), f"{label}.wav")
        wav_path = resolve_project_file(project, wav_raw, f"{label}.wav")
        narration[narration_id] = {
            "id": narration_id,
            "author_role": author_role,
            "qa_role": AUTHOR_ROLE_TO_QA_ROLE[author_role],
            "text": text,
            "text_sha256": sha256_text(text),
            "wav": Asset(
                label=f"{label}.wav",
                raw_path=wav_raw,
                path=wav_path,
                sha256=sha256_file(wav_path),
            ),
        }
    wav_paths = [row["wav"].path for row in narration.values()]
    if len(set(wav_paths)) != len(wav_paths):
        fail("authoring narration rows must use distinct WAV files")
    return asset, narration


def parse_narration_expectations(
    value: Any,
    narration_mode: str,
    chapters: list[Chapter],
    authoring_narration: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    rows = require_list(value, "narration_expectations")
    chapter_by_id = {chapter.key: chapter for chapter in chapters}
    chapter_ids = set(chapter_by_id)
    expectations: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(rows):
        label = f"narration_expectations[{index}]"
        row = require_object(raw, label)
        key = require_string(row.get("id"), f"{label}.id")
        if not KEY_RE.fullmatch(key) or key in expectations:
            fail(f"{label}.id must be unique and match {KEY_RE.pattern}")
        role = require_string(row.get("role"), f"{label}.role")
        authoring_id = require_string(
            row.get("authoring_narration_id"),
            f"{label}.authoring_narration_id",
        )
        if authoring_id not in authoring_narration:
            fail(f"{label}.authoring_narration_id is unknown: {authoring_id}")
        author = authoring_narration[authoring_id]
        if role != author["qa_role"]:
            fail(
                f"{label}.role does not match authoring narration role "
                f"{author['author_role']}"
            )
        chapter_id = require_string(row.get("chapter_id"), f"{label}.chapter_id")
        if chapter_id not in chapter_ids:
            fail(f"{label}.chapter_id is unknown: {chapter_id}")
        if chapter_by_id[chapter_id].role != role:
            fail(
                f"{label}.role={role} must reference a chapter whose role is also {role}"
            )
        expected_text = require_string(row.get("expected_text"), f"{label}.expected_text")
        if not normalized_text(expected_text):
            fail(f"{label}.expected_text becomes empty after ASR normalization")
        expected_hash = require_sha(
            row.get("expected_text_sha256"), f"{label}.expected_text_sha256"
        )
        if sha256_text(expected_text) != expected_hash:
            fail(f"{label}.expected_text_sha256 does not match expected_text")
        if expected_text != author["text"] or expected_hash != author["text_sha256"]:
            fail(f"{label} text/hash does not match its authoring narration")
        wav_hash = require_sha(
            row.get("authoring_wav_sha256"), f"{label}.authoring_wav_sha256"
        )
        if wav_hash != author["wav"].sha256:
            fail(f"{label}.authoring_wav_sha256 is stale")
        variants: list[dict[str, str]] = []
        variant_rows = require_list(
            row.get("acceptable_variants", []), f"{label}.acceptable_variants"
        )
        for variant_index, variant_raw in enumerate(variant_rows):
            variant_label = f"{label}.acceptable_variants[{variant_index}]"
            variant = require_object(variant_raw, variant_label)
            text = require_string(variant.get("text"), f"{variant_label}.text")
            text_hash = require_sha(variant.get("sha256"), f"{variant_label}.sha256")
            if sha256_text(text) != text_hash:
                fail(f"{variant_label}.sha256 does not match text")
            if not normalized_text(text):
                fail(f"{variant_label}.text becomes empty after ASR normalization")
            variants.append({"text": text, "sha256": text_hash})
        expectations[key] = {
            "id": key,
            "role": role,
            "chapter_id": chapter_id,
            "chapter_start_sec": chapter_by_id[chapter_id].start,
            "chapter_end_sec": chapter_by_id[chapter_id].end,
            "expected_text": expected_text,
            "expected_text_sha256": expected_hash,
            "acceptable_variants": variants,
            "authoring_narration_id": authoring_id,
            "authoring_wav": author["wav"],
        }

    mapped_authoring = [row["authoring_narration_id"] for row in expectations.values()]
    if len(set(mapped_authoring)) != len(mapped_authoring):
        fail("each authoring narration may be bound by only one expectation")
    if set(mapped_authoring) != set(authoring_narration):
        missing = sorted(set(authoring_narration) - set(mapped_authoring))
        extra = sorted(set(mapped_authoring) - set(authoring_narration))
        fail(
            "narration expectations must bind every authoring narration exactly once; "
            f"missing={missing} extra={extra}"
        )

    if narration_mode == "free_exploration" and not authoring_narration:
        return expectations
    if not expectations:
        fail(f"{narration_mode} requires narration expectations")
    roles = {row["role"] for row in expectations.values()}
    if narration_mode == "structured":
        missing_roles = {"intro", "outro", "cta"} - roles
        if missing_roles:
            fail("structured narration is missing roles: " + ", ".join(sorted(missing_roles)))
    covered_chapters = {row["chapter_id"] for row in expectations.values()}
    missing_chapters = [
        chapter.key
        for chapter in chapters
        if chapter.requires_narration and chapter.key not in covered_chapters
    ]
    if missing_chapters:
        fail("narration expectations do not cover chapters: " + ", ".join(missing_chapters))
    return expectations


def validate_human_record(
    value: Any,
    label: str,
    final_sha256: str,
    *,
    text_field: str,
) -> dict[str, Any]:
    row = require_object(value, label)
    if row.get("status") != "approved":
        fail(f"{label}.status must be approved")
    if row.get("reviewer_kind") != "human":
        fail(f"{label}.reviewer_kind must be human; machine approval is not accepted")
    require_string(row.get("reviewer"), f"{label}.reviewer")
    timestamp = require_string(row.get("reviewed_at"), f"{label}.reviewed_at")
    try:
        parsed_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        fail(f"{label}.reviewed_at must be ISO-8601")
    if parsed_time.tzinfo is None:
        fail(f"{label}.reviewed_at must include a timezone")
    if parsed_time.astimezone(timezone.utc) > datetime.now(timezone.utc) + timedelta(
        seconds=REVIEW_CLOCK_SKEW_SECONDS
    ):
        fail(f"{label}.reviewed_at must not be in the future")
    if require_sha(row.get("final_sha256"), f"{label}.final_sha256") != final_sha256:
        fail(f"{label} is stale: final_sha256 does not match the current final video")
    require_string(row.get(text_field), f"{label}.{text_field}")
    return row


def validate_review_record(
    value: Any,
    label: str,
    final_sha256: str,
    *,
    text_field: str,
    advisories: list[str],
) -> tuple[dict[str, Any], bool]:
    """Validate an approved human record or an honest pending placeholder.

    Pending records are deliberately narrow: they cannot name a reviewer, carry a
    review timestamp, or contain human-authored conclusions.  They remain bound to
    the current final SHA and are reported separately from mechanical PASS.
    """

    row = require_object(value, label)
    status = row.get("status")
    if status == "approved":
        return (
            validate_human_record(
                row,
                label,
                final_sha256,
                text_field=text_field,
            ),
            True,
        )
    if status != "pending_human_review":
        fail(f"{label}.status must be approved or pending_human_review")
    if row.get("reviewer_kind") is not None:
        fail(f"{label}.reviewer_kind must be null while human review is pending")
    if row.get("reviewer") not in (None, ""):
        fail(f"{label}.reviewer must be empty while human review is pending")
    if row.get("reviewed_at") not in (None, ""):
        fail(f"{label}.reviewed_at must be empty while human review is pending")
    if require_sha(row.get("final_sha256"), f"{label}.final_sha256") != final_sha256:
        fail(f"{label} is stale: final_sha256 does not match the current final video")
    if row.get(text_field) not in (None, ""):
        fail(f"{label}.{text_field} must be empty while human review is pending")
    advisories.append(label)
    return row, False


def parse_interval(value: Any, label: str) -> Interval:
    row = require_object(value, label)
    start = require_number(row.get("start_sec"), f"{label}.start_sec")
    end = require_number(row.get("end_sec"), f"{label}.end_sec")
    if start < 0 or end <= start:
        fail(f"{label} must have 0 <= start_sec < end_sec")
    return Interval(start, end)


def validate_evidence_artifacts(
    project: Path,
    value: Any,
    label: str,
    *,
    require_sample_time: bool = False,
    require_nonempty: bool = True,
) -> tuple[list[dict[str, Any]], list[float]]:
    rows = require_list(value, f"{label}.evidence")
    if require_nonempty and not rows:
        fail(f"{label}.evidence must contain at least one hashed artifact")
    artifacts: list[dict[str, Any]] = []
    sample_times: list[float] = []
    for index, raw in enumerate(rows):
        artifact_label = f"{label}.evidence[{index}]"
        row = require_object(raw, artifact_label)
        raw_path = require_string(row.get("path"), f"{artifact_label}.path")
        expected_hash = require_sha(row.get("sha256"), f"{artifact_label}.sha256")
        path = resolve_project_file(project, raw_path, f"{artifact_label}.path")
        if sha256_file(path) != expected_hash:
            fail(f"{artifact_label} SHA-256 mismatch")
        times: list[float] = []
        timestamp: float | None = None
        if require_sample_time:
            timestamp = require_number(
                row.get("sample_time_sec"), f"{artifact_label}.sample_time_sec"
            )
            if timestamp < 0:
                fail(f"{artifact_label}.sample_time_sec must be non-negative")
            times.append(timestamp)
        artifacts.append(
            {
                "path": path,
                "raw_path": raw_path,
                "sha256": expected_hash,
                "sample_time_sec": timestamp,
            }
        )
        sample_times.extend(times)
    return artifacts, sample_times


def validate_manual_approvals(
    project: Path,
    value: Any,
    final_sha256: str,
    advisories: list[str] | None = None,
) -> tuple[
    dict[str, Any],
    list[float],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    advisory_sink = [] if advisories is None else advisories
    reviews = require_object(value, "reviews")
    expected_review_keys = set(REQUIRED_HUMAN_APPROVALS) | {"silence", "black"}
    if set(reviews) != expected_review_keys:
        fail(
            "reviews must contain exactly visual_frames, leakage, release_safety, "
            "silence and black"
        )
    sample_times: list[float] = []
    visual_artifacts: list[dict[str, Any]] = []
    all_artifacts: list[dict[str, Any]] = []
    for key in REQUIRED_HUMAN_APPROVALS:
        label = f"reviews.{key}"
        row, approved = validate_review_record(
            reviews.get(key),
            label,
            final_sha256,
            text_field="notes",
            advisories=advisory_sink,
        )
        artifacts, times = validate_evidence_artifacts(
            project,
            row.get("evidence"),
            label,
            require_sample_time=key == "visual_frames",
            require_nonempty=approved or key == "visual_frames",
        )
        if key == "visual_frames" and any(
            artifact["path"].suffix.lower() != ".png"
            for artifact in artifacts
        ):
            fail("reviews.visual_frames evidence must be one lossless PNG per sample")
        if key == "visual_frames":
            visual_artifacts.extend(artifacts)
        all_artifacts.extend(artifacts)
        sample_times.extend(times)
    visual_paths = [artifact["path"] for artifact in visual_artifacts]
    if len(set(visual_paths)) != len(visual_paths):
        fail("reviews.visual_frames evidence paths must be unique")
    rounded_times = [round(timestamp, 6) for timestamp in sample_times]
    if len(set(rounded_times)) != len(rounded_times):
        fail("reviews.visual_frames sample_time_sec values must be unique")
    return reviews, sample_times, visual_artifacts, all_artifacts


def parse_interval_reviews(
    value: Any,
    label: str,
    final_sha256: str,
    advisories: list[str] | None = None,
) -> list[dict[str, Any]]:
    advisory_sink = [] if advisories is None else advisories
    rows = require_list(value, label)
    parsed: list[dict[str, Any]] = []
    for index, raw in enumerate(rows):
        row_label = f"{label}[{index}]"
        row, approved = validate_review_record(
            raw,
            row_label,
            final_sha256,
            text_field="context",
            advisories=advisory_sink,
        )
        parsed.append(
            {
                **row,
                "interval": parse_interval(row, row_label),
                "used": False,
                "approved": approved,
            }
        )
    return parsed


def validate_asr_assertions(
    evidence: dict[str, Any],
    live_receipt: dict[str, Any],
    expectations: dict[str, dict[str, Any]],
    final_sha256: str,
    label: str,
    advisories: list[str] | None = None,
    *,
    kind: str,
) -> None:
    advisory_sink = [] if advisories is None else advisories
    rows = require_list(evidence.get("assertions"), f"{label}.assertions")
    by_id: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(rows):
        assertion_label = f"{label}.assertions[{index}]"
        row = require_object(raw, assertion_label)
        expectation_id = require_string(
            row.get("expectation_id"), f"{assertion_label}.expectation_id"
        )
        allowed_keys = {"expectation_id", "segment_ids", "disposition", "review"}
        extra_keys = set(row) - allowed_keys
        if extra_keys:
            fail(
                f"{assertion_label} contains untrusted derived fields: "
                + ", ".join(sorted(extra_keys))
            )
        if expectation_id in by_id:
            fail(f"duplicate ASR assertion for expectation: {expectation_id}")
        by_id[expectation_id] = row
    if set(by_id) != set(expectations):
        missing = sorted(set(expectations) - set(by_id))
        extra = sorted(set(by_id) - set(expectations))
        fail(f"{label}.assertions mismatch; missing={missing} extra={extra}")

    receipt_sources = require_list(live_receipt.get("sources"), f"{label}.live_receipt.sources")
    source_paths: dict[str, str] = {}
    for source_index, raw_source in enumerate(receipt_sources):
        source_label = f"{label}.live_receipt.sources[{source_index}]"
        source = require_object(raw_source, source_label)
        source_id = require_string(source.get("id"), f"{source_label}.id")
        if source_id in source_paths:
            fail(f"duplicate live ASR source id: {source_id}")
        source_paths[source_id] = require_string(source.get("path"), f"{source_label}.path")

    segments_by_id: dict[str, dict[str, Any]] = {}
    results = require_list(live_receipt.get("results"), f"{label}.live_receipt.results")
    result_ids: set[str] = set()
    for result_index, raw_result in enumerate(results):
        result_label = f"{label}.live_receipt.results[{result_index}]"
        result = require_object(raw_result, result_label)
        source_id = require_string(result.get("source_id"), f"{result_label}.source_id")
        if source_id not in source_paths or source_id in result_ids:
            fail(f"{result_label}.source_id must uniquely match a declared live source")
        result_ids.add(source_id)
        if not isinstance(result.get("transcript"), str):
            fail(f"{result_label}.transcript must be a string")
        for segment_index, raw_segment in enumerate(
            require_list(result.get("segments"), f"{result_label}.segments")
        ):
            segment_label = f"{result_label}.segments[{segment_index}]"
            segment = require_object(raw_segment, segment_label)
            segment_id = require_string(segment.get("id"), f"{segment_label}.id")
            if segment_id in segments_by_id:
                fail(f"duplicate live ASR segment id: {segment_id}")
            interval = parse_interval(segment, segment_label)
            text = segment.get("text")
            if not isinstance(text, str):
                fail(f"{segment_label}.text must be a string")
            segments_by_id[segment_id] = {
                "source_id": source_id,
                "interval": interval,
                "text": text,
            }
    if result_ids != set(source_paths):
        fail(f"{label}.live_receipt must contain exactly one result per source")

    consumed_segments: set[str] = set()
    for expectation_id, expectation in expectations.items():
        assertion_label = f"{label}.assertions[{expectation_id}]"
        row = by_id[expectation_id]
        raw_segment_ids = require_list(row.get("segment_ids"), f"{assertion_label}.segment_ids")
        if not raw_segment_ids:
            fail(f"{assertion_label}.segment_ids must not be empty")
        segment_ids: list[str] = []
        for segment_index, raw_segment_id in enumerate(raw_segment_ids):
            segment_id = require_string(
                raw_segment_id, f"{assertion_label}.segment_ids[{segment_index}]"
            )
            if segment_id not in segments_by_id:
                fail(f"{assertion_label} references an unknown live ASR segment: {segment_id}")
            if segment_id in consumed_segments or segment_id in segment_ids:
                fail(f"live ASR segment may be consumed by only one assertion: {segment_id}")
            segment_ids.append(segment_id)
        chronological = sorted(
            segment_ids,
            key=lambda segment_id: (
                segments_by_id[segment_id]["interval"].start,
                segments_by_id[segment_id]["interval"].end,
                segment_id,
            ),
        )
        if segment_ids != chronological:
            fail(f"{assertion_label}.segment_ids must be in chronological order")
        consumed_segments.update(segment_ids)
        selected = [segments_by_id[segment_id] for segment_id in segment_ids]
        selected_source_ids = {segment["source_id"] for segment in selected}
        if len(selected_source_ids) != 1:
            fail(f"{assertion_label} may not combine segments from multiple sources")
        selected_source_id = next(iter(selected_source_ids))
        if kind == "isolated_narration_asr":
            if source_paths[selected_source_id] != expectation["authoring_wav"].raw_path:
                fail(f"{assertion_label} does not use its bound authoring narration WAV")

        observed = " ".join(segment["text"] for segment in selected).strip()
        normalized_observed = normalized_text(observed)
        if not normalized_observed:
            fail(f"{assertion_label} live observed text becomes empty after normalization")
        observed_interval = Interval(
            min(segment["interval"].start for segment in selected),
            max(segment["interval"].end for segment in selected),
        )
        if kind == "final_aac_asr":
            chapter_start = expectation["chapter_start_sec"]
            chapter_end = expectation["chapter_end_sec"]
            if (
                observed_interval.start < chapter_start - CHAPTER_TIMING_EPSILON_SECONDS
                or observed_interval.end > chapter_end + CHAPTER_TIMING_EPSILON_SECONDS
            ):
                fail(f"{assertion_label} live segments fall outside the expectation chapter")

        disposition = require_string(row.get("disposition"), f"{assertion_label}.disposition")
        if disposition == "exact":
            if normalized_observed != normalized_text(expectation["expected_text"]):
                fail(f"{assertion_label} is not an exact expected-text match")
        elif disposition == "accepted_variant":
            variants = {
                normalized_text(variant["text"])
                for variant in expectation["acceptable_variants"]
            }
            if not variants or normalized_observed not in variants:
                fail(f"{assertion_label} is not a registered acceptable variant")
        elif disposition in {"human_review", "pending_human_review"}:
            review_label = f"{assertion_label}.review"
            review = row.get("review")
            if review is None:
                advisory_sink.append(review_label)
            else:
                validate_review_record(
                    review,
                    review_label,
                    final_sha256,
                    text_field="reason",
                    advisories=advisory_sink,
                )
        else:
            fail(
                f"{assertion_label}.disposition must be exact, accepted_variant, "
                "human_review or pending_human_review"
            )


def validate_live_asr_identity(receipt: Any, label: str) -> dict[str, Any]:
    row = require_object(receipt, f"{label}.live_receipt")
    expected_keys = {
        "schema_version",
        "engine",
        "model",
        "language",
        "checkpoint_sha256",
        "openai_whisper_version",
        "sources",
        "results",
    }
    if set(row) != expected_keys:
        fail(f"{label}.live_receipt contains missing or unsupported fields")
    if (
        row.get("schema_version") != 1
        or row.get("engine") != "openai-whisper"
        or row.get("model") != "small"
        or row.get("checkpoint_sha256") != PINNED_WHISPER_CHECKPOINT_SHA256
        or row.get("openai_whisper_version") != PINNED_OPENAI_WHISPER_VERSION
    ):
        fail(f"{label}.live_receipt does not use the pinned offline ASR toolchain")
    return row


def validate_asr_evidence(
    project: Path,
    value: Any,
    assets: dict[str, Asset],
    expectations: dict[str, dict[str, Any]],
    tools: "MediaTools",
    advisories: list[str] | None = None,
) -> tuple[list[Asset], list[Asset]]:
    advisory_sink = [] if advisories is None else advisories
    rows = require_object(value, "asr_evidence")
    if set(rows) != set(REQUIRED_ASR_KINDS):
        fail(f"asr_evidence must contain exactly {list(REQUIRED_ASR_KINDS)}")
    isolated_sources: list[Asset] = []
    evidence_assets: list[Asset] = []
    for kind in REQUIRED_ASR_KINDS:
        label = f"asr_evidence.{kind}"
        row = require_object(rows[kind], label)
        artifact = parse_asset(project, row.get("artifact"), f"{label}.artifact")
        if artifact.path.suffix.lower() != ".json":
            fail(f"{label}.artifact.path must end in .json")
        parameters = require_object(row.get("parameters"), f"{label}.parameters")
        expected_parameters = {
            "engine": "openai-whisper",
            "model": "small",
            "language": "zh",
        }
        if kind == "final_aac_asr":
            expected_parameters["audio_stream"] = "0:a:0"
        if parameters != expected_parameters:
            fail(f"{label}.parameters must equal the fixed offline ASR contract")
        sources_raw = require_list(row.get("sources"), f"{label}.sources")
        sources = [
            parse_asset(project, source_raw, f"{label}.sources[{index}]")
            for index, source_raw in enumerate(sources_raw)
        ]
        if kind == "final_aac_asr":
            if len(sources) != 1 or sources[0].path != assets["final"].path:
                fail("final_aac_asr must bind exactly the current final MP4")
        else:
            if any(source.path in {asset.path for asset in assets.values()} for source in sources):
                fail(
                    "isolated_narration_asr sources must be narration-only files, "
                    "not final/render/master"
                )
            expected_wavs = [row["authoring_wav"] for row in expectations.values()]
            if len({source.path for source in sources}) != len(sources):
                fail("isolated_narration_asr sources must be unique")
            if {source.path for source in sources} != {wav.path for wav in expected_wavs}:
                fail("isolated_narration_asr sources must exactly match authoring narration WAVs")

        evidence = read_json(artifact.path, f"{label}.artifact")
        if evidence.get("schema_version") != 1 or evidence.get("kind") != kind:
            fail(f"{label}.artifact schema_version/kind mismatch")
        if evidence.get("final_sha256") != assets["final"].sha256:
            fail(f"{label}.artifact is stale: final_sha256 does not match the current final")
        live_receipt = validate_live_asr_identity(
            tools.transcribe(sources, parameters, kind),
            label,
        )
        if evidence.get("live_receipt") != live_receipt:
            fail(f"{label}.artifact live_receipt does not match a current offline ASR run")
        validate_asr_assertions(
            evidence,
            live_receipt,
            expectations,
            assets["final"].sha256,
            f"{label}.artifact",
            advisory_sink,
            kind=kind,
        )
        evidence_assets.append(artifact)
        if kind == "isolated_narration_asr":
            isolated_sources.extend(sources)
        evidence_assets.extend(sources)
    return isolated_sources, evidence_assets


def parse_silence_intervals(log: str, total_duration: float) -> list[Interval]:
    starts: list[float] = []
    intervals: list[Interval] = []
    for line in log.splitlines():
        start_match = re.search(r"silence_start:\s*(-?[0-9.]+)", line)
        if start_match:
            starts.append(max(0.0, float(start_match.group(1))))
        end_match = re.search(r"silence_end:\s*([0-9.]+)", line)
        if end_match:
            end = min(total_duration, float(end_match.group(1)))
            start = starts.pop(0) if starts else 0.0
            if end > start:
                intervals.append(Interval(start, end))
    for start in starts:
        if total_duration > start:
            intervals.append(Interval(start, total_duration))
    return intervals


def parse_black_intervals(log: str) -> list[Interval]:
    intervals: list[Interval] = []
    pattern = re.compile(
        r"black_start:\s*([0-9.]+)\s+black_end:\s*([0-9.]+)\s+black_duration:"
    )
    for match in pattern.finditer(log):
        start, end = float(match.group(1)), float(match.group(2))
        if end > start:
            intervals.append(Interval(start, end))
    return intervals


def parse_loudnorm(log: str) -> Loudness:
    candidates = re.findall(r"\{\s*\"input_i\".*?\}", log, flags=re.DOTALL)
    if not candidates:
        fail("ffmpeg loudnorm did not emit input loudness JSON")
    try:
        payload = require_object(
            strict_json_loads(candidates[-1], "ffmpeg loudnorm output"),
            "ffmpeg loudnorm output",
        )
        integrated = float(payload["input_i"])
        true_peak = float(payload["input_tp"])
    except (KeyError, TypeError, ValueError):
        fail("ffmpeg loudnorm emitted invalid input_i/input_tp values")
    if not math.isfinite(integrated) or not math.isfinite(true_peak):
        fail("loudness measurement is not finite")
    return Loudness(integrated, true_peak)


def parse_framemd5(log: str, label: str) -> list[tuple[float, float, str]]:
    time_bases: dict[int, Fraction] = {}
    records: list[tuple[float, float, str]] = []
    for line in log.splitlines():
        time_base_match = re.fullmatch(r"#tb\s+(\d+):\s*([^\s]+)", line.strip())
        if time_base_match:
            try:
                time_bases[int(time_base_match.group(1))] = Fraction(time_base_match.group(2))
            except (ValueError, ZeroDivisionError):
                fail(f"{label} emitted an invalid frame time base")
            continue
        if not line or line.startswith("#"):
            continue
        parts = [part.strip() for part in line.split(",")]
        if len(parts) != 6:
            fail(f"{label} emitted an invalid framemd5 row")
        try:
            stream_index = int(parts[0])
            pts = int(parts[2])
            duration = int(parts[3])
            time_base = time_bases[stream_index]
        except (ValueError, KeyError):
            fail(f"{label} emitted invalid frame timing")
        frame_hash = parts[5].lower()
        if not SHA256_RE.fullmatch(frame_hash) or duration <= 0:
            fail(f"{label} emitted an invalid frame hash/duration")
        records.append((float(pts * time_base), float(duration * time_base), frame_hash))
    if not records:
        fail(f"{label} emitted no decoded frames")
    return records


def run_offline_asr_process(
    command: list[str], request: str, timeout_seconds: int
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            input=request,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        fail(f"current offline ASR run timed out after {timeout_seconds}s")
    except OSError as exc:
        fail(f"current offline ASR runtime could not start: {type(exc).__name__}")


class MediaTools:
    """Small injectable boundary around local ffmpeg and ffprobe."""

    def __init__(self) -> None:
        missing = [name for name in ("ffmpeg", "ffprobe") if shutil.which(name) is None]
        if missing:
            fail("missing required command(s): " + ", ".join(missing))

    @staticmethod
    def _run(command: list[str], label: str) -> subprocess.CompletedProcess[str]:
        process = subprocess.run(command, text=True, capture_output=True)
        if process.returncode != 0:
            fail(f"{label} failed with exit code {process.returncode}")
        return process

    def _run_ffmpeg(
        self,
        command_builder: Callable[[str], list[str]],
        label: str,
    ) -> subprocess.CompletedProcess[str]:
        """Run one FFmpeg command under an invocation-local adaptive lease.

        The lease only selects this newly starting command's thread budget.  It
        never waits for another goal and it never changes a command that is
        already running.
        """

        try:
            lease = resource_budget.resolve_ffmpeg_threads()
        except ValueError:
            fail("adaptive FFmpeg resource budget is unavailable")
        with lease:
            return self._run(command_builder(str(lease.threads)), label)

    def probe(self, path: Path) -> dict[str, Any]:
        process = self._run(
            [
                "ffprobe", "-v", "error", "-show_format", "-show_streams",
                "-of", "json", str(path),
            ],
            "ffprobe",
        )
        return require_object(
            strict_json_loads(process.stdout, "ffprobe output"),
            "ffprobe output",
        )

    def verify_authoring(
        self,
        project: Path,
        manifest: str,
        *,
        require_human_review: bool = False,
    ) -> list[str]:
        return authoring_contract.verify_project(
            project,
            manifest,
            require_human_review=require_human_review,
        )

    def analyze_final(
        self,
        path: Path,
        duration_sec: float,
    ) -> tuple[list[Interval], list[Interval]]:
        graph = (
            f"[0:v:0]blackdetect=d={BLACK_DETECT_MIN_SECONDS}:"
            f"pix_th={BLACK_PIXEL_THRESHOLD}[video];"
            f"[0:a:0]silencedetect=noise={SILENCE_NOISE_DB}dB:"
            f"d={SILENCE_DETECT_MIN_SECONDS}[audio]"
        )
        process = self._run_ffmpeg(
            lambda threads: [
                "ffmpeg", "-hide_banner", "-nostats", "-v", "info", "-xerror",
                "-threads", threads, "-filter_threads", threads,
                "-filter_complex_threads", threads,
                "-i", str(path), "-filter_complex", graph,
                "-map", "[video]", "-map", "[audio]", "-f", "null", "-",
            ],
            "full final decode / silence / black detection",
        )
        return (
            parse_silence_intervals(process.stderr, duration_sec),
            parse_black_intervals(process.stderr),
        )

    def video_decode_receipt(self, path: Path) -> VideoDecodeReceipt:
        process = self._run_ffmpeg(
            lambda threads: [
                "ffmpeg", "-hide_banner", "-nostats", "-v", "error", "-xerror",
                "-threads", threads, "-filter_threads", threads,
                "-i", str(path), "-map", "0:v:0", "-an", "-pix_fmt", "rgb24",
                "-f", "framemd5", "-hash", "sha256", "-",
            ],
            "decoded-frame PTS/duration/hash receipt",
        )
        records = parse_framemd5(process.stdout, "decoded-frame receipt")
        canonical = "\n".join(
            f"{pts:.9f},{duration:.9f},{frame_hash}"
            for pts, duration, frame_hash in records
        )
        return VideoDecodeReceipt(
            frame_count=len(records),
            first_pts_sec=records[0][0],
            end_pts_sec=max(pts + duration for pts, duration, _ in records),
            frame_records_sha256=sha256_text(canonical),
        )

    def frame_rgb_receipt(
        self, path: Path, timestamp_sec: float | None = None
    ) -> FrameReceipt:
        def build_command(threads: str) -> list[str]:
            command = [
                "ffmpeg", "-hide_banner", "-nostats", "-v", "error", "-xerror",
                "-threads", threads, "-filter_threads", threads,
            ]
            if timestamp_sec is not None:
                # Input-side seek keeps chapter sampling proportional to the GOP
                # distance instead of decoding every prefix from t=0.  ``-copyts``
                # preserves the absolute source PTS used by the gate.
                command.extend(["-ss", f"{timestamp_sec:.6f}", "-copyts"])
            command.extend(["-i", str(path), "-vf", "format=rgb24"])
            command.extend([
                "-map", "0:v:0", "-frames:v", "1", "-fps_mode", "passthrough",
                "-f", "framemd5", "-hash", "sha256", "-",
            ])
            return command

        process = self._run_ffmpeg(
            build_command,
            "visual evidence RGB-frame decode",
        )
        records = parse_framemd5(process.stdout, "visual evidence RGB-frame receipt")
        if len(records) != 1:
            fail("visual evidence decode must emit exactly one frame")
        pts, duration, frame_hash = records[0]
        return FrameReceipt(pts, duration, frame_hash)

    def transcribe(
        self,
        sources: list[Asset],
        parameters: dict[str, Any],
        kind: str,
    ) -> dict[str, Any]:
        prefix = "final" if kind == "final_aac_asr" else "isolated"
        declared_sources = [
            {
                "id": f"{prefix}-{index:03d}",
                "path": source.raw_path,
                "sha256": source.sha256,
            }
            for index, source in enumerate(sources)
        ]
        if not sources:
            return {
                "schema_version": 1,
                "engine": "openai-whisper",
                "model": "small",
                "language": parameters["language"],
                "checkpoint_sha256": PINNED_WHISPER_CHECKPOINT_SHA256,
                "openai_whisper_version": PINNED_OPENAI_WHISPER_VERSION,
                "sources": [],
                "results": [],
            }
        local_python = Path(__file__).resolve().parents[1] / "tts" / "venv" / "bin" / "python"
        runner = Path(__file__).with_name("offline_asr.py")
        checkpoint = Path.home() / ".cache" / "whisper" / "small.pt"
        if not local_python.is_file():
            fail("fixed offline ASR runtime is missing: tools/tts/venv/bin/python")
        if not runner.is_file():
            fail("fixed offline ASR runner is missing: tools/video/offline_asr.py")
        if not checkpoint.is_file():
            fail("fixed offline ASR model is missing: cached Whisper small.pt")
        request = {
            "model": "small",
            "language": parameters["language"],
            "jobs": [
                {"id": declared["id"], "path": str(source.path)}
                for declared, source in zip(declared_sources, sources)
            ],
        }
        timeout_seconds = min(
            OFFLINE_ASR_TIMEOUT_MAX_SECONDS,
            max(OFFLINE_ASR_TIMEOUT_PER_JOB_SECONDS, len(sources) * OFFLINE_ASR_TIMEOUT_PER_JOB_SECONDS),
        )
        process = run_offline_asr_process(
            [str(local_python), str(runner)],
            json.dumps(request, ensure_ascii=False),
            timeout_seconds,
        )
        if process.returncode != 0:
            fail(f"current offline ASR run failed with exit code {process.returncode}")
        result = require_object(
            strict_json_loads(process.stdout, "offline ASR output"),
            "offline ASR output",
        )
        expected_result_keys = {
            "engine",
            "model",
            "language",
            "checkpoint_sha256",
            "openai_whisper_version",
            "results",
        }
        if set(result) != expected_result_keys or (
            result.get("engine") != "openai-whisper"
            or result.get("model") != "small"
            or result.get("language") != parameters["language"]
            or result.get("checkpoint_sha256") != PINNED_WHISPER_CHECKPOINT_SHA256
            or result.get("openai_whisper_version") != PINNED_OPENAI_WHISPER_VERSION
        ):
            fail("offline ASR runner emitted an unexpected or unpinned toolchain identity")
        return {
            "schema_version": 1,
            "engine": result["engine"],
            "model": result["model"],
            "language": result["language"],
            "checkpoint_sha256": result["checkpoint_sha256"],
            "openai_whisper_version": result["openai_whisper_version"],
            "sources": declared_sources,
            "results": result.get("results"),
        }

    def loudness(self, path: Path) -> Loudness:
        process = self._run_ffmpeg(
            lambda threads: [
                "ffmpeg", "-hide_banner", "-nostats", "-v", "info",
                "-threads", threads, "-filter_threads", threads,
                "-i", str(path),
                "-map", "0:a:0", "-af",
                "loudnorm=I=-14:LRA=11:TP=-1:print_format=json", "-f", "null", "-",
            ],
            "loudness / true-peak measurement",
        )
        return parse_loudnorm(process.stderr)

    def audio_sdr(self, master: Path, final: Path, duration_sec: float) -> float:
        process = self._run_ffmpeg(
            lambda threads: [
                "ffmpeg", "-hide_banner", "-nostats", "-v", "info", "-xerror",
                "-threads", threads, "-filter_threads", threads,
                "-filter_complex_threads", threads,
                "-i", str(master), "-threads", threads, "-i", str(final),
                "-filter_complex",
                (
                    f"[0:a:0]aresample=48000:first_pts=0,apad,"
                    f"atrim=duration={duration_sec:.6f}[master];"
                    f"[1:a:0]aresample=48000:first_pts=0,apad,"
                    f"atrim=duration={duration_sec:.6f}[final];"
                    "[master][final]asdr"
                ),
                "-f", "null", "-",
            ],
            "master/final decoded-audio SDR",
        )
        values = re.findall(r"SDR ch\d+:\s*(inf|[0-9.+-]+)\s*dB", process.stderr)
        if not values:
            fail("ffmpeg asdr did not emit per-channel SDR")
        parsed = [math.inf if value == "inf" else float(value) for value in values]
        if any(math.isnan(value) for value in parsed):
            fail("master/final audio SDR is invalid")
        return min(parsed)


def probe_duration(probe: dict[str, Any], label: str) -> float:
    try:
        duration = float(probe["format"]["duration"])
    except (KeyError, TypeError, ValueError):
        fail(f"{label} has no finite container duration")
    if not math.isfinite(duration) or duration <= 0:
        fail(f"{label} duration must be positive and finite")
    return duration


def stream_codecs(probe: dict[str, Any], stream_type: str) -> list[str]:
    streams = probe.get("streams")
    if not isinstance(streams, list):
        return []
    return [
        str(stream.get("codec_name", ""))
        for stream in streams
        if isinstance(stream, dict) and stream.get("codec_type") == stream_type
    ]


def media_streams(probe: dict[str, Any]) -> list[dict[str, Any]]:
    streams = probe.get("streams")
    if not isinstance(streams, list):
        return []
    return [stream for stream in streams if isinstance(stream, dict)]


def stream_time_bounds(
    probe: dict[str, Any],
    stream_type: str,
    label: str,
) -> tuple[float, float]:
    streams = [
        stream
        for stream in media_streams(probe)
        if stream.get("codec_type") == stream_type
    ]
    if len(streams) != 1:
        fail(f"{label} must have exactly one {stream_type} stream")
    stream = streams[0]
    if "start_time" in stream:
        raw_start = stream["start_time"]
    else:
        format_names = {
            name.strip()
            for name in str(probe.get("format", {}).get("format_name", "")).split(",")
            if name.strip()
        }
        codec = str(stream.get("codec_name", ""))
        # ffprobe omits start_time/start_pts for ordinary PCM WAV even though
        # the format has no timeline offset. This is the sole deterministic
        # zero-start fallback; MP4/video/AAC streams must report their start.
        if stream_type == "audio" and "wav" in format_names and codec.startswith("pcm_"):
            raw_start = 0.0
        else:
            fail(f"{label} {stream_type} stream has no finite start_time")
    try:
        start = float(raw_start)
    except (TypeError, ValueError):
        fail(f"{label} {stream_type} stream has no finite start_time")
    raw_duration = stream.get("duration")
    try:
        duration = float(raw_duration)
    except (TypeError, ValueError):
        try:
            duration = float(int(stream["duration_ts"]) * Fraction(stream["time_base"]))
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            fail(f"{label} {stream_type} stream has no finite duration")
    if not math.isfinite(start) or not math.isfinite(duration) or duration <= 0:
        fail(f"{label} {stream_type} stream timing must be finite and positive")
    return start, start + duration


def single_stream(
    probe: dict[str, Any], stream_type: str, label: str
) -> dict[str, Any]:
    streams = [
        stream
        for stream in media_streams(probe)
        if stream.get("codec_type") == stream_type
    ]
    if len(streams) != 1:
        fail(f"{label} must have exactly one {stream_type} stream")
    return streams[0]


def validate_media_structure(
    assets: dict[str, Asset],
    probes: dict[str, dict[str, Any]],
    checks: dict[str, Any],
) -> tuple[float, str]:
    final_probe = probes["final"]
    format_name = str((final_probe.get("format") or {}).get("format_name", ""))
    if assets["final"].path.suffix.lower() != ".mp4" or not (
        set(format_name.split(",")) & MP4_FORMAT_NAMES
    ):
        fail("final asset must be an MP4 container")
    render_format_name = str((probes["render"].get("format") or {}).get("format_name", ""))
    if assets["render"].path.suffix.lower() != ".mp4" or not (
        set(render_format_name.split(",")) & MP4_FORMAT_NAMES
    ):
        fail("render asset must be an MP4 container")
    if assets["master"].path.suffix.lower() != ".wav":
        fail("master asset must be a WAV file")

    expected_codec = checks["expected_video_codec"]
    final_video = stream_codecs(final_probe, "video")
    render_video = stream_codecs(probes["render"], "video")
    final_audio = stream_codecs(final_probe, "audio")
    master_audio = stream_codecs(probes["master"], "audio")
    if len(media_streams(final_probe)) != 2 or len(final_video) != 1 or len(final_audio) != 1:
        fail("final MP4 must contain exactly one video stream and one audio stream")
    if len(media_streams(probes["render"])) != 1 or len(render_video) != 1:
        fail("render MP4 must contain exactly one video stream and no other streams")
    if len(media_streams(probes["master"])) != 1 or len(master_audio) != 1:
        fail("master WAV must contain exactly one audio stream and no other streams")
    if final_video[0] != expected_codec:
        fail(f"final video codec must be manifest-selected {expected_codec}")
    if render_video[0] != expected_codec:
        fail(f"render video codec must be manifest-selected {expected_codec}")
    if final_audio[0] != "aac":
        fail("final MP4 must contain an AAC audio stream")
    if not master_audio[0].startswith("pcm_"):
        fail("master WAV must contain PCM audio")

    final_audio_stream = single_stream(final_probe, "audio", "final")
    master_audio_stream = single_stream(probes["master"], "audio", "master")
    try:
        final_audio_bit_rate = int(final_audio_stream["bit_rate"])
        final_sample_rate = int(final_audio_stream["sample_rate"])
        master_sample_rate = int(master_audio_stream["sample_rate"])
        final_channels = int(final_audio_stream["channels"])
        master_channels = int(master_audio_stream["channels"])
    except (KeyError, TypeError, ValueError):
        fail("final/master audio stream metadata is incomplete")
    if final_audio_bit_rate < MIN_FINAL_AAC_BIT_RATE:
        fail(
            f"final AAC bit rate must be at least {MIN_FINAL_AAC_BIT_RATE // 1000} kbps"
        )
    if final_sample_rate != master_sample_rate or final_channels != master_channels:
        fail("final AAC sample rate/channels must match the PCM master")

    durations = {key: probe_duration(value, key) for key, value in probes.items()}
    tolerance = checks["duration_tolerance_sec"]
    for key in ("render", "master"):
        if abs(durations["final"] - durations[key]) > tolerance:
            fail(
                f"final/{key} duration mismatch exceeds {tolerance:.3f}s: "
                f"{durations['final']:.3f}s vs {durations[key]:.3f}s"
            )
    for asset_key, stream_type in (
        ("final", "video"),
        ("final", "audio"),
        ("render", "video"),
        ("master", "audio"),
    ):
        start, end = stream_time_bounds(probes[asset_key], stream_type, asset_key)
        coverage_tolerance = STREAM_COVERAGE_TOLERANCE_SECONDS
        if abs(start) > coverage_tolerance or end < durations[asset_key] - coverage_tolerance:
            fail(
                f"{asset_key} {stream_type} stream does not cover its container within "
                f"{coverage_tolerance:.3f}s: stream={start:.3f}-{end:.3f}s "
                f"container=0.000-{durations[asset_key]:.3f}s"
            )
    return durations["final"], expected_codec


def validate_chapter_coverage(
    chapters: list[Chapter],
    duration_sec: float,
) -> None:
    tolerance = CHAPTER_TIMING_EPSILON_SECONDS
    if abs(chapters[0].start) > tolerance:
        fail("chapters must start at final-video time 0")
    for previous, current in zip(chapters, chapters[1:]):
        if abs(previous.end - current.start) > tolerance:
            fail(f"chapter boundary gap is too large between {previous.key} and {current.key}")
    if abs(chapters[-1].end - duration_sec) > tolerance:
        fail("chapters do not cover the current final-video duration")
    total_uncovered = max(0.0, chapters[0].start)
    total_uncovered += sum(
        max(0.0, current.start - previous.end)
        for previous, current in zip(chapters, chapters[1:])
    )
    total_uncovered += max(0.0, duration_sec - chapters[-1].end)
    if total_uncovered > tolerance:
        fail(
            "chapter boundary gaps cumulatively leave too much final-video time "
            f"unassigned: {total_uncovered:.3f}s"
        )


def interval_matches(left: Interval, right: Interval) -> bool:
    return (
        abs(left.start - right.start) <= INTERVAL_MATCH_TOLERANCE_SECONDS
        and abs(left.end - right.end) <= INTERVAL_MATCH_TOLERANCE_SECONDS
    )


def chapter_for_interval(interval: Interval, chapters: list[Chapter]) -> Chapter | None:
    for chapter in chapters:
        if interval.start >= chapter.start - 0.001 and interval.end <= chapter.end + 0.001:
            return chapter
    return None


def consume_matching_review(
    interval: Interval,
    reviews: list[dict[str, Any]],
    label: str,
) -> bool:
    matches = [row for row in reviews if not row["used"] and interval_matches(interval, row["interval"])]
    if len(matches) != 1:
        fail(
            f"{label} interval {interval.start:.3f}-{interval.end:.3f}s requires exactly "
            "one current review record (pending or approved)"
        )
    matches[0]["used"] = True
    return bool(matches[0]["approved"])


def validate_detected_intervals(
    silences: list[Interval],
    black_intervals: list[Interval],
    chapters: list[Chapter],
    silence_reviews: list[dict[str, Any]],
    black_reviews: list[dict[str, Any]],
) -> tuple[int, int]:
    reviewed_silences = 0
    for interval in silences:
        if interval.duration + 0.001 < SILENCE_DETECT_MIN_SECONDS:
            continue
        chapter = chapter_for_interval(interval, chapters)
        if interval.duration > SILENCE_HARD_FAIL_SECONDS:
            if chapter is None:
                fail(
                    f"hard silence crosses a chapter boundary: "
                    f"{interval.start:.3f}-{interval.end:.3f}s "
                    f"({interval.duration:.3f}s)"
                )
            fail(
                f"hard silence inside chapter {chapter.key}: "
                f"{interval.start:.3f}-{interval.end:.3f}s ({interval.duration:.3f}s)"
            )
        if consume_matching_review(interval, silence_reviews, "silence REVIEW"):
            reviewed_silences += 1

    reviewed_black = 0
    for interval in black_intervals:
        if consume_matching_review(interval, black_reviews, "blackdetect REVIEW"):
            reviewed_black += 1
    stale_silence = [row for row in silence_reviews if not row["used"]]
    stale_black = [row for row in black_reviews if not row["used"]]
    if stale_silence:
        fail("reviews.silence contains stale entries not found in the current final video")
    if stale_black:
        fail("reviews.black contains stale entries not found in the current final video")
    return reviewed_silences, reviewed_black


def validate_visual_sample_coverage(
    sample_times: list[float],
    chapters: list[Chapter],
    duration_sec: float,
) -> None:
    if any(timestamp > duration_sec + 0.05 for timestamp in sample_times):
        fail("visual frame sample time exceeds the current final-video duration")
    if not any(abs(timestamp) <= 0.000001 for timestamp in sample_times):
        fail("visual frame evidence must include final-video frame 0 for cover QA")
    covered: set[str] = set()
    for timestamp in sample_times:
        if abs(timestamp) <= 0.000001 and abs(chapters[0].start) <= 0.000001:
            owners = [chapters[0]]
        else:
            owners = [
                chapter
                for chapter in chapters
                if chapter.start < timestamp < chapter.end
            ]
        if len(owners) != 1:
            fail(
                f"visual frame sample {timestamp:.3f}s must lie strictly inside exactly "
                "one chapter, not on a boundary or gap"
            )
        covered.add(owners[0].key)
    uncovered = [chapter.key for chapter in chapters if chapter.key not in covered]
    if uncovered:
        fail("visual frame evidence does not sample chapters: " + ", ".join(uncovered))


def verify_project(
    project: Path,
    manifest_relative: str = "qa/final-video-qa.json",
    *,
    tools: MediaTools | None = None,
    require_human_review: bool = False,
) -> VerificationSummary:
    if project.is_symlink():
        fail("project directory must not be a symlink")
    project = project.resolve(strict=True)
    if not project.is_dir():
        fail("project must be a directory")
    manifest_path = resolve_project_file(project, manifest_relative, "manifest")
    manifest_initial_hash = sha256_file(manifest_path)
    manifest = read_json(manifest_path, "manifest")
    if manifest.get("schema_version") != 1:
        fail("manifest.schema_version must be 1")
    expected_manifest_keys = {
        "schema_version",
        "narration_mode",
        "authoring_manifest",
        "assets",
        "chapters",
        "checks",
        "narration_expectations",
        "asr_evidence",
        "reviews",
    }
    if set(manifest) != expected_manifest_keys:
        fail("manifest contains missing or unsupported top-level fields")
    narration_mode = require_string(manifest.get("narration_mode"), "narration_mode")
    if narration_mode not in NARRATION_MODES:
        fail(f"narration_mode must be one of {sorted(NARRATION_MODES)}")
    media_tools = MediaTools() if tools is None else tools
    authoring_asset, authoring_narration = parse_authoring_contract(
        project,
        manifest.get("authoring_manifest"),
        narration_mode,
        media_tools.verify_authoring,
        require_human_review=require_human_review,
    )
    authoring_manifest_value = read_json(authoring_asset.path, "authoring_manifest")
    authoring_inputs = collect_project_file_inputs(project, authoring_manifest_value)

    assets_raw = require_object(manifest.get("assets"), "assets")
    if set(assets_raw) != {"final", "render", "master"}:
        fail("assets must contain exactly final, render and master")
    for key in ("final", "render"):
        asset_row = require_object(assets_raw[key], f"assets.{key}")
        if not starts_with_renders_directory(asset_row.get("path")):
            fail(
                f"assets.{key}.path first path component must be lowercase "
                f"'{RENDERS_DIRECTORY}'"
            )
    assets = {
        key: parse_asset(project, assets_raw[key], f"assets.{key}")
        for key in ("final", "render", "master")
    }
    if len({asset.path for asset in assets.values()}) != 3:
        fail("final, render and master paths must be distinct")
    if assets["final"].sha256 == assets["render"].sha256:
        fail("final and render file hashes are identical; post-render mux is not proven")

    chapters = parse_chapters(manifest.get("chapters"))
    checks = parse_checks(manifest.get("checks"))
    expectations = parse_narration_expectations(
        manifest.get("narration_expectations"),
        narration_mode,
        chapters,
        authoring_narration,
    )
    human_review_advisories: list[str] = []
    reviews, sample_times, visual_artifacts, approval_artifacts = validate_manual_approvals(
        project,
        manifest.get("reviews"),
        assets["final"].sha256,
        human_review_advisories,
    )
    silence_reviews = parse_interval_reviews(
        reviews.get("silence"),
        "reviews.silence",
        assets["final"].sha256,
        human_review_advisories,
    )
    black_reviews = parse_interval_reviews(
        reviews.get("black"),
        "reviews.black",
        assets["final"].sha256,
        human_review_advisories,
    )
    isolated_asr_sources, asr_assets = validate_asr_evidence(
        project,
        manifest.get("asr_evidence"),
        assets,
        expectations,
        media_tools,
        human_review_advisories,
    )

    probes = {key: media_tools.probe(asset.path) for key, asset in assets.items()}
    for source in isolated_asr_sources:
        source_probe = media_tools.probe(source.path)
        if not stream_codecs(source_probe, "audio") or stream_codecs(source_probe, "video"):
            fail(
                "isolated_narration_asr sources must be decodable audio-only media: "
                f"{source.raw_path}"
            )
    duration_sec, video_codec = validate_media_structure(assets, probes, checks)
    validate_chapter_coverage(chapters, duration_sec)
    validate_visual_sample_coverage(sample_times, chapters, duration_sec)
    for artifact in visual_artifacts:
        final_frame = media_tools.frame_rgb_receipt(
            assets["final"].path,
            artifact["sample_time_sec"],
        )
        requested = artifact["sample_time_sec"]
        if (
            final_frame.pts_sec < requested - 0.001
            or final_frame.pts_sec > requested + FRAME_SAMPLE_TOLERANCE_SECONDS
        ):
            fail(
                f"visual frame extraction returned PTS {final_frame.pts_sec:.6f}s "
                f"for requested {requested:.6f}s"
            )
        evidence_frame = media_tools.frame_rgb_receipt(artifact["path"])
        if final_frame.rgb_sha256 != evidence_frame.rgb_sha256:
            fail(
                "visual frame evidence pixels do not match the current final at "
                f"{artifact['sample_time_sec']:.3f}s: {artifact['raw_path']}"
            )

    final_video_receipt = media_tools.video_decode_receipt(assets["final"].path)
    render_video_receipt = media_tools.video_decode_receipt(assets["render"].path)
    if final_video_receipt != render_video_receipt:
        fail(
            "decoded final-video PTS/duration/frame hashes do not match the declared "
            "render input"
        )
    if (
        abs(final_video_receipt.first_pts_sec) > STREAM_COVERAGE_TOLERANCE_SECONDS
        or final_video_receipt.end_pts_sec
        < duration_sec - STREAM_COVERAGE_TOLERANCE_SECONDS
    ):
        fail("decoded final-video frame receipt does not cover the final container")

    audio_sdr = media_tools.audio_sdr(
        assets["master"].path,
        assets["final"].path,
        duration_sec,
    )
    if audio_sdr < checks["min_master_aac_sdr_db"]:
        fail(
            f"decoded final AAC does not match master closely enough: "
            f"SDR={audio_sdr:.2f}dB < {checks['min_master_aac_sdr_db']:.2f}dB"
        )

    silences, black_intervals = media_tools.analyze_final(
        assets["final"].path, duration_sec
    )
    reviewed_silences, reviewed_black = validate_detected_intervals(
        silences,
        black_intervals,
        chapters,
        silence_reviews,
        black_reviews,
    )

    loudness = media_tools.loudness(assets["final"].path)
    thresholds = checks["loudness"]
    if not thresholds["minimum"] <= loudness.integrated_lufs <= thresholds["maximum"]:
        fail(
            f"integrated loudness {loudness.integrated_lufs:.2f} LUFS is outside "
            f"[{thresholds['minimum']:.2f}, {thresholds['maximum']:.2f}]"
        )
    if loudness.true_peak_dbtp > thresholds["true_peak"]:
        fail(
            f"true peak {loudness.true_peak_dbtp:.2f} dBTP exceeds "
            f"{thresholds['true_peak']:.2f} dBTP"
        )

    tracked_inputs: dict[Path, tuple[str, str]] = {}
    for asset in [
        *assets.values(),
        authoring_asset,
        *(row["wav"] for row in authoring_narration.values()),
        *asr_assets,
    ]:
        tracked_inputs[asset.path] = (asset.sha256, asset.label)
    for artifact in approval_artifacts:
        tracked_inputs[artifact["path"]] = (
            artifact["sha256"],
            f"review evidence {artifact['raw_path']}",
        )
    for path, expected_hash in authoring_inputs.items():
        tracked_inputs[path] = (expected_hash, f"authoring input {path.relative_to(project)}")
    for path, (expected_hash, label) in tracked_inputs.items():
        if sha256_file(path) != expected_hash:
            fail(f"{label} changed while final-video QA was running")
    if sha256_file(manifest_path) != manifest_initial_hash:
        fail("final-video QA manifest changed while verification was running")
    authoring_errors = media_tools.verify_authoring(
        project,
        authoring_asset.raw_path,
        require_human_review=require_human_review,
    )
    if authoring_errors:
        fail("authoring project contract changed or failed during QA: " + " | ".join(authoring_errors))

    advisory_labels = tuple(dict.fromkeys(human_review_advisories))
    if require_human_review and advisory_labels:
        raise HumanReviewRequired(advisory_labels)

    return VerificationSummary(
        final_path=assets["final"].raw_path,
        final_sha256=assets["final"].sha256,
        duration_sec=duration_sec,
        video_codec=video_codec,
        integrated_lufs=loudness.integrated_lufs,
        true_peak_dbtp=loudness.true_peak_dbtp,
        master_aac_sdr_db=audio_sdr,
        reviewed_silences=reviewed_silences,
        reviewed_black_intervals=reviewed_black,
        human_review_advisories=advisory_labels,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, help="video project directory")
    parser.add_argument(
        "--manifest",
        default="qa/final-video-qa.json",
        help="project-relative QA manifest path",
    )
    parser.add_argument(
        "--require-human-review",
        action="store_true",
        help="strict opt-in requiring all hash-bound human reviews",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        summary = verify_project(
            Path(args.project),
            args.manifest,
            require_human_review=args.require_human_review,
        )
    except HumanReviewRequired as exc:
        print(f"FINAL VIDEO QA: REVIEW_REQUIRED — {exc}", file=sys.stderr)
        return 2
    except (GateFailure, FileNotFoundError) as exc:
        print(f"FINAL VIDEO QA: FAIL — {exc}", file=sys.stderr)
        return 1
    print(
        "FINAL VIDEO QA: PASS "
        f"final={summary.final_path} sha256={summary.final_sha256} "
        f"duration={summary.duration_sec:.3f}s codec={summary.video_codec} "
        f"I={summary.integrated_lufs:.2f}LUFS TP={summary.true_peak_dbtp:.2f}dBTP "
        f"audio_sdr={summary.master_aac_sdr_db:.2f}dB "
        f"advisories={len(summary.human_review_advisories)}"
    )
    # The default sandbox command ends at the machine result.  Do not append
    # unsolicited next-step or manual-review boilerplate.
    # Explicit strict-mode requests still use the REVIEW_REQUIRED branch above.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
