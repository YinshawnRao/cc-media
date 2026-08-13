#!/usr/bin/env python3
"""Prepare hash-bound final-video QA evidence without fabricating human review.

This repository-level helper creates:

* chapters derived from ``timeline.json`` and closed against the real final duration;
* current final/render/master and authoring hashes;
* narration expectations bound to the authoring text and WAV hashes;
* current pinned offline-Whisper receipts plus segment-level assertions;
* lossless PNG samples at frame 0 and inside every chapter;
* a staging manifest with honest pending reviews;
* one in-process run of the central mechanical verifier, reusing only the ASR
  and exact-frame receipts produced moments earlier in this invocation.

The default sandbox workflow writes ``qa/final-video-qa.json`` with those
pending records kept internally.  The central gate can therefore finish every
mechanical check without producing an unsolicited follow-up footer.  Explicit
``--require-human-review`` runs require a separate current
``status=approved`` / ``reviewer_kind=human`` input; when that input is absent,
only the strict run writes a template.  This helper never promotes a machine
result or an empty template into approval.

Capability boundary: this helper currently prepares only structured
``top_ranking`` and ``narrative`` projects whose timeline roles are intro, song,
outro and CTA.  It does not claim to prepare ``free_exploration`` final QA.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import os
import subprocess
import sys
import tempfile
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, NoReturn


SCRIPT = Path(__file__).resolve()


def find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "tools/video/verify_final_video.py").is_file():
            return candidate
    raise SystemExit("could not locate repository root from script path")


REPO_ROOT = find_repo_root(SCRIPT.parent)
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.video import verify_final_video as gate  # noqa: E402


ROLE_MAP = {
    "intro": "intro",
    "song": "transition",
    "outro": "outro",
    "cta": "cta",
}


def fail(message: str) -> NoReturn:
    raise SystemExit(message)


def json_error_message(label: str, exc: gate.GateFailure) -> str:
    """Map JSON parser failures to fixed messages without echoing raw input."""

    detail = str(exc)
    if "duplicate object key" in detail:
        return f"{label} is invalid JSON: duplicate object key"
    if "non-standard numeric constant" in detail:
        return f"{label} is invalid JSON: non-standard numeric constant"
    return f"{label} is invalid JSON"


def human_review_error_message(label: str, exc: gate.GateFailure) -> str:
    """Preserve useful approval categories while suppressing raw record values."""

    detail = str(exc)
    fixed_reasons = (
        "status must be approved",
        "reviewer_kind must be human",
        "reviewer must be a non-empty string",
        "reviewed_at must be a timezone-aware ISO-8601 timestamp",
        "does not match the current final SHA-256",
    )
    for reason in fixed_reasons:
        if reason in detail:
            return f"{label} {reason}"
    return f"{label} contains an invalid human review record"


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        fail(f"{label} cannot be read [io-or-encoding-error]")
    try:
        value = gate.strict_json_loads(raw, label)
    except gate.GateFailure as exc:
        fail(json_error_message(label, exc))
    if not isinstance(value, dict):
        fail(f"{label} must contain a JSON object")
    return value


def inside_existing(project: Path, raw: str, label: str) -> Path:
    try:
        return gate.resolve_project_file(project, raw, label)
    except (gate.GateFailure, FileNotFoundError):
        fail(
            f"{label} must be an existing regular project-relative file "
            "without symlinks or '..'"
        )


def plan_output(project: Path, raw: str, label: str) -> Path:
    """Resolve one output lexically without creating directories or files."""

    relative = Path(raw)
    if not raw.strip() or relative.is_absolute() or ".." in relative.parts:
        fail(f"{label} must be a non-empty project-relative path without '..'")
    root = project.resolve(strict=True)
    logical = root / relative
    cursor = root
    for part in relative.parts[:-1]:
        cursor = cursor / part
        if cursor.is_symlink():
            fail(f"{label} parent must not be a symlink")
        if cursor.exists() and not cursor.is_dir():
            fail(f"{label} parent component is not a directory")
    if logical.is_symlink():
        fail(f"{label} must not be a symlink")
    if logical.exists() and not logical.is_file():
        fail(f"{label} target must be a regular file when it already exists")
    try:
        logical.parent.resolve(strict=False).relative_to(root)
    except ValueError:
        fail(f"{label} escaped the project")
    return logical


def ensure_output_parent(project: Path, path: Path, label: str) -> None:
    root = project.resolve(strict=True)
    if path.is_symlink():
        fail(f"{label} must not be a symlink")
    try:
        relative = path.resolve(strict=False).relative_to(root)
    except ValueError:
        fail(f"{label} escaped the project")
    cursor = root
    for part in relative.parts[:-1]:
        cursor = cursor / part
        if cursor.is_symlink():
            fail(f"{label} parent must not be a symlink")
        if cursor.exists() and not cursor.is_dir():
            fail(f"{label} parent component is not a directory")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.parent.resolve(strict=True).relative_to(root)
    except ValueError:
        fail(f"{label} parent escaped the project")
    if path.is_symlink():
        fail(f"{label} must not be a symlink")


def write_json_atomic(project: Path, path: Path, value: Any, label: str) -> None:
    """Write through a random O_EXCL sibling, then atomically replace the target."""

    ensure_output_parent(project, path, label)
    descriptor, temporary_raw = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    temporary = Path(temporary_raw)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(
                json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
            )
            stream.flush()
            os.fsync(stream.fileno())
        if path.is_symlink():
            fail(f"{label} became a symlink before replace")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def paths_alias(left: Path, right: Path) -> bool:
    if left.resolve(strict=False) == right.resolve(strict=False):
        return True
    if left.exists() and right.exists():
        try:
            return os.path.samefile(left, right)
        except OSError:
            return False
    return False


def validate_path_plan(
    inputs: dict[str, Path],
    outputs: dict[str, Path],
) -> None:
    """Reject aliases and file/descendant collisions before the first write.

    JSON and frame temporary files do not appear in this plan because they are
    created later with random ``mkstemp`` names and O_EXCL semantics.
    """

    output_rows = list(outputs.items())
    for index, (left_label, left) in enumerate(output_rows):
        left_resolved = left.resolve(strict=False)
        for right_label, right in output_rows[index + 1 :]:
            right_resolved = right.resolve(strict=False)
            if (
                paths_alias(left, right)
                or left_resolved in right_resolved.parents
                or right_resolved in left_resolved.parents
            ):
                fail(f"output path collision: {left_label} conflicts with {right_label}")
        for input_label, input_path in inputs.items():
            input_resolved = input_path.resolve(strict=True)
            if (
                paths_alias(left, input_path)
                or left_resolved in input_resolved.parents
                or input_resolved in left_resolved.parents
            ):
                fail(f"output/input path collision: {left_label} conflicts with {input_label}")


def relative(project: Path, path: Path) -> str:
    return path.resolve(strict=True).relative_to(project.resolve(strict=True)).as_posix()


def asset(project: Path, path: Path, label: str) -> gate.Asset:
    return gate.Asset(
        label=label,
        raw_path=relative(project, path),
        path=path,
        sha256=gate.sha256_file(path),
    )


def asset_ref(value: gate.Asset) -> dict[str, str]:
    return {"path": value.raw_path, "sha256": value.sha256}


def authoring_asset(project: Path, raw: str) -> gate.Asset:
    path = inside_existing(project, raw, "authoring manifest")
    return asset(project, path, "authoring_manifest")


def build_chapters(
    timeline: dict[str, Any],
    final_duration: float,
) -> list[dict[str, Any]]:
    rows = timeline.get("segments")
    if not isinstance(rows, list) or not rows:
        fail("timeline.segments must be a non-empty array")
    timeline_duration = timeline.get("duration_sec")
    if not isinstance(timeline_duration, (int, float)) or isinstance(timeline_duration, bool):
        fail("timeline.duration_sec must be a finite number")
    if not math.isfinite(float(timeline_duration)):
        fail("timeline.duration_sec must be finite")
    if abs(float(timeline_duration) - final_duration) > 0.50:
        fail(
            "timeline/final duration mismatch exceeds 0.50s: "
            f"{float(timeline_duration):.3f}s vs {final_duration:.3f}s"
        )

    chapters: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw_row in enumerate(rows):
        if not isinstance(raw_row, dict):
            fail(f"timeline.segments[{index}] must be an object")
        key = raw_row.get("key")
        role = raw_row.get("role")
        if not isinstance(key, str) or not gate.KEY_RE.fullmatch(key) or key in seen:
            fail(f"timeline.segments[{index}].key must be unique and QA-safe")
        if role not in ROLE_MAP:
            fail(f"unsupported timeline role for {key}: {role!r}")
        seen.add(key)
        try:
            start = float(raw_row["start_sec"])
            configured_end = float(raw_row["end_sec"])
        except (KeyError, TypeError, ValueError):
            fail(f"timeline segment {key} has invalid start/end")
        if not math.isfinite(start) or not math.isfinite(configured_end):
            fail(f"timeline segment {key} has non-finite start/end")
        if index + 1 < len(rows):
            next_row = rows[index + 1]
            if not isinstance(next_row, dict):
                fail(f"timeline.segments[{index + 1}] must be an object")
            try:
                end = float(next_row["start_sec"])
            except (KeyError, TypeError, ValueError):
                fail(f"timeline segment after {key} has invalid start")
            if abs(configured_end - end) > gate.CHAPTER_TIMING_EPSILON_SECONDS:
                fail(f"timeline boundary after {key} is not contiguous")
        else:
            end = final_duration
        if start < 0 or end <= start:
            fail(f"invalid final chapter bounds for {key}: {start:.3f}-{end:.3f}")
        chapters.append(
            {
                "id": key,
                "role": ROLE_MAP[role],
                "start_sec": round(start, 6),
                "end_sec": round(end, 6),
                "requires_narration": True,
            }
        )
    return chapters


def chapter_for_author(
    author: dict[str, Any], chapters: list[dict[str, Any]]
) -> dict[str, Any]:
    role = author.get("role")
    if role == "transition":
        item_id = author.get("item_id")
        matches = [row for row in chapters if row["id"] == item_id and row["role"] == "transition"]
    else:
        qa_role = gate.AUTHOR_ROLE_TO_QA_ROLE.get(role)
        matches = [row for row in chapters if row["role"] == qa_role]
    if len(matches) != 1:
        fail(
            f"authoring narration {author.get('id')!r} maps to {len(matches)} chapters; "
            "expected exactly one"
        )
    return matches[0]


def build_expectations(
    project: Path,
    authoring: dict[str, Any],
    chapters: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = authoring.get("narration_sequence")
    if not isinstance(rows, list) or not rows:
        fail("authoring narration_sequence must be a non-empty array")
    expectations: list[dict[str, Any]] = []
    for index, raw in enumerate(rows):
        if not isinstance(raw, dict):
            fail(f"authoring narration_sequence[{index}] must be an object")
        narration_id = raw.get("id")
        text = raw.get("text")
        wav_raw = raw.get("wav")
        role = gate.AUTHOR_ROLE_TO_QA_ROLE.get(raw.get("role"))
        if not isinstance(narration_id, str) or not gate.KEY_RE.fullmatch(narration_id):
            fail(f"authoring narration_sequence[{index}].id is not QA-safe")
        if not isinstance(text, str) or not text.strip():
            fail(f"authoring narration {narration_id} has empty text")
        if not isinstance(wav_raw, str):
            fail(f"authoring narration {narration_id} has invalid WAV path")
        if role is None:
            fail(f"authoring narration {narration_id} has unsupported role")
        chapter = chapter_for_author(raw, chapters)
        wav = inside_existing(project, wav_raw, f"authoring narration {narration_id} WAV")
        expectations.append(
            {
                "id": narration_id,
                "role": role,
                "chapter_id": chapter["id"],
                "expected_text": text,
                "expected_text_sha256": gate.sha256_text(text),
                "authoring_narration_id": narration_id,
                "authoring_wav_sha256": gate.sha256_file(wav),
                "acceptable_variants": [],
            }
        )
    if {row["chapter_id"] for row in expectations} != {row["id"] for row in chapters}:
        fail("each chapter must map to exactly one authoring narration")
    return expectations


def expectation_runtime(
    project: Path,
    expectations: list[dict[str, Any]],
    chapters: list[dict[str, Any]],
    authoring: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    chapter_by_id = {row["id"]: row for row in chapters}
    author_by_id = {row["id"]: row for row in authoring["narration_sequence"]}
    runtime: dict[str, dict[str, Any]] = {}
    for row in expectations:
        author = author_by_id[row["authoring_narration_id"]]
        wav_path = inside_existing(project, author["wav"], f"{row['id']} WAV")
        wav = asset(project, wav_path, f"narration {row['id']} WAV")
        chapter = chapter_by_id[row["chapter_id"]]
        runtime[row["id"]] = {
            **row,
            "chapter_start_sec": float(chapter["start_sec"]),
            "chapter_end_sec": float(chapter["end_sec"]),
            "authoring_wav": wav,
        }
    return runtime


def receipt_segments(receipt: dict[str, Any]) -> tuple[dict[str, str], dict[str, list[dict[str, Any]]]]:
    source_paths: dict[str, str] = {}
    for source in receipt.get("sources", []):
        if isinstance(source, dict) and isinstance(source.get("id"), str):
            source_paths[source["id"]] = str(source.get("path", ""))
    by_source: dict[str, list[dict[str, Any]]] = {key: [] for key in source_paths}
    for result in receipt.get("results", []):
        if not isinstance(result, dict) or result.get("source_id") not in by_source:
            continue
        for segment in result.get("segments", []):
            if not isinstance(segment, dict):
                continue
            try:
                start = float(segment["start_sec"])
                end = float(segment["end_sec"])
            except (KeyError, TypeError, ValueError):
                continue
            text = segment.get("text")
            segment_id = segment.get("id")
            if (
                isinstance(text, str)
                and isinstance(segment_id, str)
                and end > start
                and gate.normalized_text(text)
            ):
                by_source[result["source_id"]].append(
                    {"id": segment_id, "start": start, "end": end, "text": text}
                )
    for rows in by_source.values():
        rows.sort(key=lambda row: (row["start"], row["end"], row["id"]))
    return source_paths, by_source


def best_contiguous_window(
    segments: list[dict[str, Any]], expected_text: str
) -> tuple[list[dict[str, Any]], str, float]:
    if not segments:
        fail("offline ASR returned no non-empty segments for an expectation")
    target = gate.normalized_text(expected_text)
    best_rows: list[dict[str, Any]] = []
    best_observed = ""
    best_score = -1.0
    for start in range(len(segments)):
        for end in range(start + 1, len(segments) + 1):
            rows = segments[start:end]
            observed = " ".join(row["text"] for row in rows).strip()
            normalized = gate.normalized_text(observed)
            if not normalized:
                continue
            ratio = SequenceMatcher(None, normalized, target, autojunk=False).ratio()
            length_penalty = abs(len(normalized) - len(target)) / max(
                len(normalized), len(target), 1
            )
            score = ratio - 0.12 * length_penalty
            if score > best_score:
                best_rows = rows
                best_observed = observed
                best_score = score
    if not best_rows:
        fail("offline ASR could not produce a usable contiguous segment window")
    return best_rows, best_observed, best_score


def assertion_for(
    expectation: dict[str, Any],
    candidates: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    selected, observed, score = best_contiguous_window(candidates, expectation["expected_text"])
    observed_norm = gate.normalized_text(observed)
    expected_norm = gate.normalized_text(expectation["expected_text"])
    variants = {
        gate.normalized_text(row["text"])
        for row in expectation.get("acceptable_variants", [])
    }
    if observed_norm == expected_norm:
        disposition = "exact"
        needs_human = False
    elif observed_norm in variants:
        disposition = "accepted_variant"
        needs_human = False
    else:
        # This is intentionally incomplete until a human supplies a hash-bound
        # review. No approved record is synthesized here.
        disposition = "human_review"
        needs_human = True
    assertion = {
        "expectation_id": expectation["id"],
        "segment_ids": [row["id"] for row in selected],
        "disposition": disposition,
    }
    report = {
        "expectation_id": expectation["id"],
        "chapter_id": expectation["chapter_id"],
        "segment_ids": assertion["segment_ids"],
        "observed_text": observed,
        "expected_text": expectation["expected_text"],
        "normalized_similarity": round(score, 6),
        "needs_human_review": needs_human,
    }
    return assertion, report


def build_asr_artifact(
    *,
    kind: str,
    final_sha256: str,
    receipt: dict[str, Any],
    expectations: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    source_paths, by_source = receipt_segments(receipt)
    assertions: list[dict[str, Any]] = []
    reports: list[dict[str, Any]] = []
    if kind == "isolated_narration_asr":
        by_path = {path: source_id for source_id, path in source_paths.items()}
        for expectation in expectations.values():
            source_id = by_path.get(expectation["authoring_wav"].raw_path)
            if source_id is None:
                fail(f"isolated ASR has no source for {expectation['id']}")
            assertion, report = assertion_for(expectation, by_source[source_id])
            assertions.append(assertion)
            reports.append({"kind": kind, **report})
    else:
        if len(by_source) != 1:
            fail("final AAC ASR must contain exactly one source")
        segments = next(iter(by_source.values()))
        for expectation in expectations.values():
            start = expectation["chapter_start_sec"]
            end = expectation["chapter_end_sec"]
            candidates = [
                row
                for row in segments
                if row["start"] >= start - gate.CHAPTER_TIMING_EPSILON_SECONDS
                and row["end"] <= end + gate.CHAPTER_TIMING_EPSILON_SECONDS
            ]
            assertion, report = assertion_for(expectation, candidates)
            assertions.append(assertion)
            reports.append({"kind": kind, **report})
    return (
        {
            "schema_version": 1,
            "kind": kind,
            "final_sha256": final_sha256,
            "live_receipt": receipt,
            "assertions": assertions,
        },
        reports,
    )


def extract_frame(
    project: Path,
    final: Path,
    timestamp: float,
    output: Path,
) -> None:
    ensure_output_parent(project, output, "frame output")
    descriptor, temporary_raw = tempfile.mkstemp(
        prefix=f".{output.stem}.",
        suffix=".png",
        dir=output.parent,
    )
    os.close(descriptor)
    temporary = Path(temporary_raw)
    try:
        try:
            lease = gate.resource_budget.resolve_ffmpeg_threads()
        except ValueError:
            fail("adaptive FFmpeg resource budget is unavailable")
        with lease:
            threads = str(lease.threads)
            command = [
                "ffmpeg",
                "-hide_banner",
                "-nostats",
                "-v",
                "error",
                "-xerror",
                "-threads",
                threads,
                "-filter_threads",
                threads,
                "-y",
                "-ss",
                f"{timestamp:.6f}",
                "-copyts",
                "-i",
                str(final),
                "-vf",
                "format=rgb24",
                "-map",
                "0:v:0",
                "-frames:v",
                "1",
                "-fps_mode",
                "passthrough",
                "-c:v",
                "png",
                str(temporary),
            ]
            process = subprocess.run(command, text=True, capture_output=True)
        if process.returncode != 0:
            fail(
                f"frame extraction failed at {timestamp:.6f}s "
                f"with exit code {process.returncode}"
            )
        if output.is_symlink():
            fail("frame output became a symlink before replace")
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)


def plan_visual_outputs(
    project: Path,
    chapters: list[dict[str, Any]],
    frame_dir_raw: str,
) -> list[tuple[Path, float]]:
    samples: list[tuple[str, float]] = [("00-cover", 0.0)]
    for index, chapter in enumerate(chapters):
        start = float(chapter["start_sec"])
        end = float(chapter["end_sec"])
        samples.append(
            (f"{index + 1:02d}-{chapter['id']}-mid", start + (end - start) / 2.0)
        )
    return [
        (
            plan_output(
                project,
                f"{frame_dir_raw}/{name}.png",
                f"visual frame {name}",
            ),
            timestamp,
        )
        for name, timestamp in samples
    ]


def build_visual_evidence(
    project: Path,
    final: gate.Asset,
    planned_outputs: list[tuple[Path, float]],
    tools: gate.MediaTools,
) -> tuple[list[dict[str, Any]], dict[tuple[Path, float | None], gate.FrameReceipt]]:
    evidence: list[dict[str, Any]] = []
    receipts: dict[tuple[Path, float | None], gate.FrameReceipt] = {}
    for output, timestamp in planned_outputs:
        sample_time = round(timestamp, 6)
        extract_frame(project, final.path, sample_time, output)
        current = tools.frame_rgb_receipt(final.path, sample_time)
        extracted = tools.frame_rgb_receipt(output)
        receipts[(final.path, sample_time)] = current
        receipts[(output, None)] = extracted
        if current.rgb_sha256 != extracted.rgb_sha256:
            fail(f"extracted PNG pixels do not match final at {sample_time:.6f}s")
        if current.pts_sec < sample_time - 0.001 or (
            current.pts_sec > sample_time + gate.FRAME_SAMPLE_TOLERANCE_SECONDS
        ):
            fail(
                f"final frame PTS {current.pts_sec:.6f}s is outside the allowed window "
                f"for requested {sample_time:.6f}s"
            )
        evidence.append(
            {
                "path": relative(project, output),
                "sha256": gate.sha256_file(output),
                "sample_time_sec": sample_time,
            }
        )
    return evidence, receipts


def format_summary(summary: gate.VerificationSummary) -> str:
    return (
        "FINAL VIDEO QA: PASS "
        f"final={summary.final_path} sha256={summary.final_sha256} "
        f"duration={summary.duration_sec:.3f}s codec={summary.video_codec} "
        f"I={summary.integrated_lufs:.2f}LUFS TP={summary.true_peak_dbtp:.2f}dBTP "
        f"audio_sdr={summary.master_aac_sdr_db:.2f}dB "
        f"advisories={len(summary.human_review_advisories)}"
    )


class PreparedRunMediaTools:
    """Reuse only evidence created in this invocation of the preparer.

    Every other operation delegates to the ordinary central ``MediaTools`` so
    SDR, loudness and final/render full-frame receipts execute live exactly
    once.  Black/silence detection is also executed exactly once, just before
    the manifest is written so its pending interval records can be complete,
    then reused here.  This object is intentionally in-memory: standalone
    verification cannot trust or replay a project-written cache.
    """

    def __init__(
        self,
        delegate: gate.MediaTools,
        *,
        asr_receipts: dict[str, tuple[tuple[tuple[str, str], ...], dict[str, Any], dict[str, Any]]],
        frame_receipts: dict[tuple[Path, float | None], gate.FrameReceipt],
        final_analysis: tuple[
            Path,
            float,
            tuple[list[gate.Interval], list[gate.Interval]],
        ],
    ) -> None:
        self._delegate = delegate
        self._asr_receipts = asr_receipts
        self._frame_receipts = frame_receipts
        self._final_analysis = final_analysis

    def __getattr__(self, name: str) -> Any:
        return getattr(self._delegate, name)

    def transcribe(
        self,
        sources: list[gate.Asset],
        parameters: dict[str, Any],
        kind: str,
    ) -> dict[str, Any]:
        cached = self._asr_receipts.get(kind)
        identity = tuple((source.raw_path, source.sha256) for source in sources)
        if cached is None or cached[0] != identity or cached[1] != parameters:
            fail(f"in-process ASR evidence changed before verification: {kind}")
        return copy.deepcopy(cached[2])

    def frame_rgb_receipt(
        self,
        path: Path,
        timestamp_sec: float | None = None,
    ) -> gate.FrameReceipt:
        receipt = self._frame_receipts.get((path, timestamp_sec))
        if receipt is None:
            fail("in-process visual evidence changed before verification")
        return receipt

    def analyze_final(
        self,
        path: Path,
        duration_sec: float,
    ) -> tuple[list[gate.Interval], list[gate.Interval]]:
        cached_path, cached_duration, intervals = self._final_analysis
        if path != cached_path or abs(duration_sec - cached_duration) > 0.000001:
            fail("in-process final analysis changed before verification")
        return copy.deepcopy(intervals)


def pending_record(final_sha256: str, *, text_field: str, evidence: Any = None) -> dict[str, Any]:
    row: dict[str, Any] = {
        "status": "pending_human_review",
        "reviewer_kind": None,
        "reviewer": "",
        "reviewed_at": "",
        "final_sha256": final_sha256,
        text_field: "",
    }
    if evidence is not None:
        row["evidence"] = evidence
    return row


def pending_interval(final_sha256: str, interval: gate.Interval) -> dict[str, Any]:
    return {
        **pending_record(final_sha256, text_field="context"),
        "start_sec": round(interval.start, 6),
        "end_sec": round(interval.end, 6),
    }


def build_human_template(
    final_sha256: str,
    staging_reviews: dict[str, Any],
    artifacts: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    asr_reviews: dict[str, dict[str, Any]] = {}
    for kind, artifact in artifacts.items():
        pending: dict[str, Any] = {}
        for assertion in artifact["assertions"]:
            if assertion["disposition"] == "human_review":
                pending[assertion["expectation_id"]] = pending_record(
                    final_sha256,
                    text_field="reason",
                )
        asr_reviews[kind] = pending
    return {
        "schema_version": 1,
        "final_sha256": final_sha256,
        "reviews": staging_reviews,
        "asr_reviews": asr_reviews,
    }


def validate_interval_input(
    rows: Any,
    label: str,
    expected: list[gate.Interval],
    final_sha256: str,
) -> None:
    advisories: list[str] = []
    try:
        parsed = gate.parse_interval_reviews(rows, label, final_sha256, advisories)
    except gate.GateFailure as exc:
        fail(human_review_error_message(label, exc))
    if advisories:
        fail(f"{label} must contain approved human records in release mode")
    if len(parsed) != len(expected):
        fail(f"{label} does not match current detected interval count")
    unused = list(expected)
    for row in parsed:
        matches = [item for item in unused if gate.interval_matches(row["interval"], item)]
        if len(matches) != 1:
            fail(f"{label} contains a stale or duplicate interval")
        unused.remove(matches[0])


def merge_human_input(
    *,
    project: Path,
    input_path: Path,
    final_sha256: str,
    staging_manifest: dict[str, Any],
    artifacts: dict[str, dict[str, Any]],
    artifact_paths: dict[str, Path],
    silences: list[gate.Interval],
    black: list[gate.Interval],
) -> dict[str, Any]:
    supplied = load_json(input_path, "human review input")
    if set(supplied) != {"schema_version", "final_sha256", "reviews", "asr_reviews"}:
        fail("human review input must contain exactly schema_version, final_sha256, reviews and asr_reviews")
    if supplied.get("schema_version") != 1 or supplied.get("final_sha256") != final_sha256:
        fail("human review input is not bound to the current final SHA-256")
    reviews = supplied.get("reviews")
    review_advisories: list[str] = []
    try:
        gate.validate_manual_approvals(
            project,
            reviews,
            final_sha256,
            review_advisories,
        )
    except gate.GateFailure as exc:
        fail(human_review_error_message("human review input", exc))
    if review_advisories:
        fail("human review input still contains pending review records")
    if reviews["visual_frames"]["evidence"] != staging_manifest["reviews"]["visual_frames"]["evidence"]:
        fail("human visual review must use the exact generated current-final PNG evidence")
    validate_interval_input(reviews["silence"], "reviews.silence", silences, final_sha256)
    validate_interval_input(reviews["black"], "reviews.black", black, final_sha256)

    asr_reviews = supplied.get("asr_reviews")
    if not isinstance(asr_reviews, dict) or set(asr_reviews) != set(artifacts):
        fail("human review input asr_reviews must contain both current ASR kinds")
    merged_artifacts = copy.deepcopy(artifacts)
    merged_manifest = copy.deepcopy(staging_manifest)
    for kind, artifact in merged_artifacts.items():
        kind_reviews = asr_reviews.get(kind)
        if not isinstance(kind_reviews, dict):
            fail(f"asr_reviews.{kind} must be an object")
        needed = {
            row["expectation_id"]
            for row in artifact["assertions"]
            if row["disposition"] == "human_review"
        }
        if set(kind_reviews) != needed:
            fail(f"asr_reviews.{kind} must contain exactly the pending expectation ids")
        for assertion in artifact["assertions"]:
            if assertion["disposition"] != "human_review":
                continue
            expectation_id = assertion["expectation_id"]
            record = kind_reviews[expectation_id]
            try:
                gate.validate_human_record(
                    record,
                    f"asr_reviews.{kind}.{expectation_id}",
                    final_sha256,
                    text_field="reason",
                )
            except gate.GateFailure as exc:
                fail(
                    human_review_error_message(
                        f"asr_reviews.{kind}.{expectation_id}", exc
                    )
                )
            assertion["review"] = record

    # No artifact is touched until every global, interval and ASR review has
    # passed strict human validation.  This prevents a later invalid record from
    # leaving only the first ASR artifact updated.
    for kind, artifact in merged_artifacts.items():
        write_json_atomic(
            project,
            artifact_paths[kind],
            artifact,
            f"{kind} merged ASR artifact",
        )
        merged_manifest["asr_evidence"][kind]["artifact"] = {
            "path": relative(project, artifact_paths[kind]),
            "sha256": gate.sha256_file(artifact_paths[kind]),
        }
    merged_manifest["reviews"] = reviews
    return merged_manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, help="project directory")
    parser.add_argument("--timeline", default="timeline.json", help="project-relative timeline JSON")
    parser.add_argument(
        "--authoring-manifest",
        default="project-manifest.json",
        help="project-relative authoring manifest",
    )
    parser.add_argument("--final", required=True, help="project-relative muxed final MP4")
    parser.add_argument("--render", required=True, help="project-relative video-only render MP4")
    parser.add_argument(
        "--master",
        help="project-relative PCM master WAV; defaults to timeline.master_audio",
    )
    parser.add_argument(
        "--staging-manifest",
        default="qa/final-video-qa.staging.json",
        help="manifest snapshot written before any optional human-review merge",
    )
    parser.add_argument(
        "--final-manifest",
        default="qa/final-video-qa.json",
        help="sandbox QA manifest; pending review data remains internal",
    )
    parser.add_argument(
        "--human-template",
        default="qa/human-review-input.template.json",
        help="strict-mode review template written only when review input is absent",
    )
    parser.add_argument(
        "--human-review-input",
        help="explicit current-final human approval input; never generated by this script",
    )
    parser.add_argument(
        "--require-human-review",
        action="store_true",
        help=(
            "explicit strict profile: require a complete --human-review-input; default "
            "sandbox preparation keeps pending review data internal"
        ),
    )
    parser.add_argument("--frame-dir", default="qa/final-frames")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    project_argument = Path(args.project)
    if project_argument.is_symlink():
        fail("project directory must not be a symlink")
    try:
        project = project_argument.resolve(strict=True)
    except FileNotFoundError:
        fail("project directory does not exist")
    if not project.is_dir():
        fail("project must be a real directory")
    for option, value in (("--final", args.final), ("--render", args.render)):
        if not gate.starts_with_renders_directory(value):
            fail(
                f"{option} first path component must be lowercase "
                f"'{gate.RENDERS_DIRECTORY}'"
            )
    timeline_path = inside_existing(project, args.timeline, "timeline")
    authoring_path = inside_existing(project, args.authoring_manifest, "authoring manifest")
    final_path = inside_existing(project, args.final, "final")
    render_path = inside_existing(project, args.render, "render")
    timeline = load_json(timeline_path, "timeline")
    authoring = load_json(authoring_path, "authoring manifest")
    master_raw = args.master or timeline.get("master_audio")
    if not isinstance(master_raw, str):
        fail("--master is required when timeline.master_audio is absent")
    master_path = inside_existing(project, master_raw, "master")
    human_input_path = (
        inside_existing(project, args.human_review_input, "human review input")
        if args.human_review_input
        else None
    )
    generate_human_template = args.require_human_review and human_input_path is None

    tools = gate.MediaTools()
    author_ref = authoring_asset(project, args.authoring_manifest)
    author_errors = tools.verify_authoring(
        project,
        author_ref.raw_path,
        require_human_review=args.require_human_review,
    )
    if author_errors:
        fail(
            "authoring project contract failed "
            f"[{len(author_errors)} issue(s)]; run verify_project.py for details"
        )
    if authoring.get("project_kind") not in {"top_ranking", "narrative"}:
        fail(
            "prepare_final_qa currently supports only structured "
            "top_ranking or narrative projects"
        )

    assets = {
        "final": asset(project, final_path, "assets.final"),
        "render": asset(project, render_path, "assets.render"),
        "master": asset(project, master_path, "assets.master"),
    }
    final_probe = tools.probe(final_path)
    video_codecs = gate.stream_codecs(final_probe, "video")
    if len(video_codecs) != 1 or video_codecs[0] not in gate.ALLOWED_VIDEO_CODECS:
        fail("final must contain one supported video codec")
    checks = {
        "expected_video_codec": video_codecs[0],
        "duration_tolerance_sec": 0.5,
        "min_master_aac_sdr_db": gate.DEFAULT_MIN_MASTER_AAC_SDR_DB,
        "loudness": {
            "integrated_lufs_min": gate.DEFAULT_INTEGRATED_LUFS_MIN,
            "integrated_lufs_max": gate.DEFAULT_INTEGRATED_LUFS_MAX,
            "max_true_peak_dbtp": gate.DEFAULT_MAX_TRUE_PEAK_DBTP,
        },
    }
    parsed_checks = gate.parse_checks(checks)
    probes = {
        "final": final_probe,
        "render": tools.probe(render_path),
        "master": tools.probe(master_path),
    }
    final_duration, _codec = gate.validate_media_structure(assets, probes, parsed_checks)
    chapters = build_chapters(timeline, final_duration)
    parsed_chapters = gate.parse_chapters(chapters)
    gate.validate_chapter_coverage(parsed_chapters, final_duration)
    expectations = build_expectations(project, authoring, chapters)
    runtime_expectations = expectation_runtime(project, expectations, chapters, authoring)
    author_by_id = {
        row["id"]: row
        for row in authoring["narration_sequence"]
        if isinstance(row, dict) and isinstance(row.get("id"), str)
    }
    gate.parse_narration_expectations(
        expectations,
        "structured",
        parsed_chapters,
        {
            key: {
                "id": value["id"],
                "author_role": author_by_id[key]["role"],
                "qa_role": value["role"],
                "text": value["expected_text"],
                "text_sha256": value["expected_text_sha256"],
                "wav": value["authoring_wav"],
            }
            for key, value in runtime_expectations.items()
        },
    )

    artifact_paths = {
        "final_aac_asr": plan_output(
            project,
            "qa/final-aac-asr.json",
            "final AAC ASR artifact",
        ),
        "isolated_narration_asr": plan_output(
            project,
            "qa/isolated-narration-asr.json",
            "isolated narration ASR artifact",
        ),
    }
    mapping_report_path = plan_output(
        project,
        "qa/asr-mapping-report.json",
        "ASR mapping report",
    )
    staging_path = plan_output(project, args.staging_manifest, "staging manifest")
    final_manifest_path = plan_output(project, args.final_manifest, "final QA manifest")
    human_template_path = (
        plan_output(project, args.human_template, "human template")
        if generate_human_template
        else None
    )
    frame_outputs = plan_visual_outputs(project, chapters, args.frame_dir)

    input_paths: dict[str, Path] = {
        "timeline": timeline_path,
        "authoring manifest": authoring_path,
        "final video": final_path,
        "render video": render_path,
        "master audio": master_path,
    }
    for path in gate.collect_project_file_inputs(project, authoring).keys():
        input_paths[f"authoring input {path.relative_to(project)}"] = path
    for expectation_id, value in runtime_expectations.items():
        input_paths[f"narration WAV {expectation_id}"] = value["authoring_wav"].path
    if human_input_path is not None:
        input_paths["human review input"] = human_input_path
    output_paths: dict[str, Path] = {
        "final AAC ASR artifact": artifact_paths["final_aac_asr"],
        "isolated narration ASR artifact": artifact_paths["isolated_narration_asr"],
        "ASR mapping report": mapping_report_path,
        "staging manifest": staging_path,
        "final QA manifest": final_manifest_path,
    }
    if human_template_path is not None:
        output_paths["human review template"] = human_template_path
    output_paths.update(
        {
            f"visual frame {index}": path
            for index, (path, _timestamp) in enumerate(frame_outputs)
        }
    )
    validate_path_plan(input_paths, output_paths)

    visual_evidence, frame_receipts = build_visual_evidence(
        project,
        assets["final"],
        frame_outputs,
        tools,
    )
    gate.validate_visual_sample_coverage(
        [row["sample_time_sec"] for row in visual_evidence],
        parsed_chapters,
        final_duration,
    )

    final_parameters = {
        "engine": "openai-whisper",
        "model": "small",
        "language": "zh",
        "audio_stream": "0:a:0",
    }
    isolated_parameters = {
        "engine": "openai-whisper",
        "model": "small",
        "language": "zh",
    }
    isolated_sources = [value["authoring_wav"] for value in runtime_expectations.values()]
    final_receipt = tools.transcribe([assets["final"]], final_parameters, "final_aac_asr")
    isolated_receipt = tools.transcribe(
        isolated_sources,
        isolated_parameters,
        "isolated_narration_asr",
    )
    artifacts: dict[str, dict[str, Any]] = {}
    reports: list[dict[str, Any]] = []
    for kind, receipt in (
        ("final_aac_asr", final_receipt),
        ("isolated_narration_asr", isolated_receipt),
    ):
        artifact, kind_reports = build_asr_artifact(
            kind=kind,
            final_sha256=assets["final"].sha256,
            receipt=receipt,
            expectations=runtime_expectations,
        )
        artifacts[kind] = artifact
        reports.extend(kind_reports)

    for kind, artifact in artifacts.items():
        write_json_atomic(
            project,
            artifact_paths[kind],
            artifact,
            f"{kind} ASR artifact",
        )
    write_json_atomic(
        project,
        mapping_report_path,
        {
            "schema_version": 1,
            "final_sha256": assets["final"].sha256,
            "mappings": reports,
        },
        "ASR mapping report",
    )

    # The interval list must exist before pending/local or approved/release
    # records can be bound to it.  Decode once here and pass the result directly
    # into the in-process verifier; it is never persisted as trusted diagnostics.
    silences, black = tools.analyze_final(final_path, final_duration)
    silence_review = [
        row
        for row in silences
        if row.duration + 0.001 >= gate.SILENCE_DETECT_MIN_SECONDS
    ]

    staging_reviews = {
        "visual_frames": pending_record(
            assets["final"].sha256,
            text_field="notes",
            evidence=visual_evidence,
        ),
        "leakage": pending_record(
            assets["final"].sha256,
            text_field="notes",
            evidence=[],
        ),
        "release_safety": pending_record(
            assets["final"].sha256,
            text_field="notes",
            evidence=[],
        ),
        "silence": [
            pending_interval(assets["final"].sha256, row)
            for row in silence_review
        ],
        "black": [pending_interval(assets["final"].sha256, row) for row in black],
    }
    asr_evidence = {
        "final_aac_asr": {
            "artifact": {
                "path": relative(project, artifact_paths["final_aac_asr"]),
                "sha256": gate.sha256_file(artifact_paths["final_aac_asr"]),
            },
            "sources": [asset_ref(assets["final"])],
            "parameters": final_parameters,
        },
        "isolated_narration_asr": {
            "artifact": {
                "path": relative(project, artifact_paths["isolated_narration_asr"]),
                "sha256": gate.sha256_file(artifact_paths["isolated_narration_asr"]),
            },
            "sources": [asset_ref(row) for row in isolated_sources],
            "parameters": isolated_parameters,
        },
    }
    staging_manifest = {
        "schema_version": 1,
        "narration_mode": "structured",
        "authoring_manifest": asset_ref(author_ref),
        "assets": {key: asset_ref(value) for key, value in assets.items()},
        "chapters": chapters,
        "checks": checks,
        "narration_expectations": expectations,
        "asr_evidence": asr_evidence,
        "reviews": staging_reviews,
    }
    write_json_atomic(project, staging_path, staging_manifest, "staging manifest")
    if human_template_path is not None:
        write_json_atomic(
            project,
            human_template_path,
            build_human_template(assets["final"].sha256, staging_reviews, artifacts),
            "human review template",
        )

    if human_input_path is not None:
        final_manifest = merge_human_input(
            project=project,
            input_path=human_input_path,
            final_sha256=assets["final"].sha256,
            staging_manifest=staging_manifest,
            artifacts=artifacts,
            artifact_paths=artifact_paths,
            silences=silence_review,
            black=black,
        )
        write_json_atomic(
            project,
            final_manifest_path,
            final_manifest,
            "final QA manifest",
        )
    if args.require_human_review and human_input_path is None:
        assert human_template_path is not None
        print(f"FINAL QA STAGING READY: {relative(project, staging_path)}")
        print(
            "RELEASE REVIEW REQUIRED: copy and complete "
            f"{relative(project, human_template_path)}"
        )
        print("No reviewer was synthesized and no release-ready manifest was generated.")
        return 2

    # Sandbox goals must be able to complete without a forged human record.
    # Preserve every pending field exactly as generated and let the central gate
    # validate all machine evidence.  Pending details remain in the manifest;
    # the default CLI must not turn them into unsolicited delivery boilerplate.
    if human_input_path is None:
        write_json_atomic(
            project,
            final_manifest_path,
            staging_manifest,
            "final QA manifest",
        )

    # Validate exactly what was atomically written, using only invocation-local
    # ASR/frame receipts while keeping every expensive mechanical red line live.
    asr_receipts = {
        "final_aac_asr": (
            ((assets["final"].raw_path, assets["final"].sha256),),
            final_parameters,
            final_receipt,
        ),
        "isolated_narration_asr": (
            tuple((row.raw_path, row.sha256) for row in isolated_sources),
            isolated_parameters,
            isolated_receipt,
        ),
    }
    prepared_tools = PreparedRunMediaTools(
        tools,
        asr_receipts=asr_receipts,
        frame_receipts=frame_receipts,
        final_analysis=(final_path, final_duration, (silences, black)),
    )
    try:
        summary = gate.verify_project(
            project,
            relative(project, final_manifest_path),
            tools=prepared_tools,
            require_human_review=args.require_human_review,
        )
    except gate.HumanReviewRequired as exc:
        print(f"FINAL VIDEO QA: REVIEW_REQUIRED — {exc}", file=sys.stderr)
        return 2
    except (gate.GateFailure, FileNotFoundError) as exc:
        print(f"FINAL VIDEO QA: FAIL — {exc}", file=sys.stderr)
        return 1
    print(format_summary(summary))
    return 0


def cli(argv: list[str] | None = None) -> int:
    """Run the CLI without exposing an unexpected exception payload."""

    try:
        return main(argv)
    except SystemExit:
        raise
    except Exception:
        print(
            "FINAL QA PREP: FAIL [unexpected]; inspect project-relative inputs "
            "and rerun",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(cli())
