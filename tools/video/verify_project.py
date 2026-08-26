#!/usr/bin/env python3
"""Fail-closed authoring contract for ranking, narrative and free-exploration projects.

This gate validates project structure and evidence before a build. It does not
replace post-mux visual/audio QA, and AI voice-clone MVs use the separate durable
builder under ``tools/video/templates/ai-voice-mv``.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import os
import re
import shutil
import stat
import subprocess
import sys
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

try:
    from . import showcase_align
    from .outro_cta import FIXED_OUTRO_CTA
except ImportError:  # Direct ``python tools/video/verify_project.py`` execution.
    import showcase_align  # type: ignore[no-redef]
    from outro_cta import FIXED_OUTRO_CTA  # type: ignore[no-redef]


SCHEMA_VERSION = 2
SUPPORTED_SCHEMA_VERSIONS = frozenset({1, 2})
PACING_SCHEMA_VERSION = 2
PROJECT_KINDS = {"top_ranking", "narrative", "free_exploration"}
NARRATION_ROLES = {"intro", "transition", "work_outro", "outro_cta", "free"}
TRANSITION_NARRATION_MAX_SECONDS = {
    "top_ranking": 8.0,
    "narrative": 10.0,
}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
RANK_ONE_RE = re.compile(
    r"(?:第\s*一\s*名|冠\s*军|no\.?\s*0?1\b|#\s*0?1\b|0?1\s*[-—:：])",
    re.IGNORECASE,
)
COVER_ORDER_HINT_RE = re.compile(
    r"(?:"
    r"(?:0?[2-9]|[1-9]\d+|N)\s*(?:→|->|⇒|⟶|\bto\b)\s*0?1"
    r"|倒数(?:开始|揭晓)"
    r"|倒序揭晓"
    r"|从第?\s*(?:0?[2-9]|[1-9]\d+)\s*名开始"
    r")",
    re.IGNORECASE,
)
PLATFORM_HOSTS = {
    "youtube": ("youtube.com", "youtu.be"),
    "bilibili": ("bilibili.com", "b23.tv"),
}
SOURCE_TIERS = {
    (True, "mv"): (0, "official_mv"),
    (True, "live"): (1, "official_performance"),
    (True, "show"): (1, "official_performance"),
}
START_BOUNDARY_KINDS = {"source_head", "strong_attack", "phrase_start", "loop_boundary"}
END_BOUNDARY_KINDS = {"natural_decay", "phrase_end", "complete_source", "loop_boundary"}
MEDIA_DURATION_TOLERANCE_SEC = 0.10
SOURCE_RECEIPT_REQUIRED = frozenset(
    {
        "schema_version",
        "kind",
        "platform",
        "url",
        "downloaded_at",
        "raw_asset",
        "raw_duration_sec",
        "derivation",
    }
)
SOURCE_DERIVATION_REQUIRED = frozenset(
    {
        "input_sha256",
        "tool",
        "operation",
        "source_start_sec",
        "source_end_sec",
        "output",
        "output_duration_sec",
    }
)
VOCAL_EVIDENCE_REQUIRED = frozenset(
    {
        "schema_version",
        "kind",
        "status",
        "item_id",
        "clip",
        "clip_sha256",
        "analysis",
        "analysis_key",
        "window",
    }
)
INSTRUMENTAL_EVIDENCE_REQUIRED = frozenset(
    {
        "schema_version",
        "kind",
        "status",
        "item_id",
        "clip",
        "clip_sha256",
        "clip_duration_sec",
        "window",
        "continuity",
        "boundaries",
    }
)
REVIEW_APPROVAL_REQUIRED = frozenset(
    {
        "status",
        "clip",
        "analysis_sha256",
        "window",
        "reason",
        "evidence",
        "reviewer_kind",
        "reviewer",
        "reviewed_at",
        "evidence_files",
    }
)
TTS_ROOT = Path(__file__).resolve().parents[1] / "tts"


@dataclass(frozen=True)
class MediaInfo:
    duration_sec: float
    video_streams: int
    audio_streams: int


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalized_title(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    return "".join(character for character in value if character.isalnum())


def is_finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def first_nonfinite_path(value: Any, label: str) -> str | None:
    if isinstance(value, float) and not math.isfinite(value):
        return label
    if isinstance(value, dict):
        for key, child in value.items():
            found = first_nonfinite_path(child, f"{label}.{key}")
            if found is not None:
                return found
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found = first_nonfinite_path(child, f"{label}[{index}]")
            if found is not None:
                return found
    return None


def reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, child in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key {key!r}")
        value[key] = child
    return value


def parse_aware_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


class ProjectVerifier:
    def __init__(
        self,
        project: Path,
        *,
        voice_registry: Any = None,
        current_model_validation: dict[str, Any] | None = None,
        require_human_review: bool = False,
    ) -> None:
        self.project = Path(os.path.abspath(project))
        self.errors: list[str] = []
        self.project_valid = True
        self.voice_registry = voice_registry
        self.current_model_validation = current_model_validation
        self.require_human_review = require_human_review
        self._voice_sidecars: dict[str, Any] = {}
        try:
            resolved = self.project.resolve(strict=True)
        except OSError as exc:
            self.error(f"cannot resolve project root: {exc}")
            self.project_valid = False
            return
        if resolved != self.project:
            self.error("project root or one of its parents must not be a symlink")
            self.project_valid = False
            return
        try:
            root_info = self.project.lstat()
        except OSError as exc:
            self.error(f"cannot inspect project root: {exc}")
            self.project_valid = False
            return
        if stat.S_ISLNK(root_info.st_mode) or not stat.S_ISDIR(root_info.st_mode):
            self.error("project root must be a real directory, not a symlink")
            self.project_valid = False

    def error(self, message: str) -> None:
        self.errors.append(message)

    def safe_path(
        self,
        raw: Any,
        label: str,
        *,
        must_exist: bool = True,
        allow_absolute: bool = False,
    ) -> Path | None:
        if not isinstance(raw, str) or not raw.strip():
            self.error(f"{label} must be a non-empty project path")
            return None
        candidate = Path(raw)
        if ".." in candidate.parts:
            self.error(f"{label} must not contain '..': {raw!r}")
            return None
        if candidate.is_absolute():
            if not allow_absolute:
                self.error(f"{label} must be project-relative: {raw!r}")
                return None
            logical = candidate
        else:
            logical = self.project / candidate
        try:
            relative = logical.relative_to(self.project)
        except ValueError:
            self.error(f"{label} logical path is outside the project: {logical}")
            return None
        cursor = self.project
        for part in relative.parent.parts:
            cursor = cursor / part
            if cursor.is_symlink():
                self.error(f"{label} parent must not be a symlink: {cursor}")
                return None
        if logical.is_symlink():
            self.error(f"{label} must not be a symlink: {logical}")
            return None
        try:
            logical.resolve().relative_to(self.project)
        except ValueError:
            self.error(f"{label} resolves outside the project: {logical}")
            return None
        if must_exist and not logical.is_file():
            self.error(f"{label} file is missing: {logical}")
            return None
        return logical

    def load_json_path(self, path: Path, label: str) -> dict[str, Any] | None:
        try:
            value = json.loads(
                path.read_text(encoding="utf-8"),
                parse_constant=lambda token: (_ for _ in ()).throw(
                    ValueError(f"non-standard numeric constant {token}")
                ),
                object_pairs_hook=reject_duplicate_json_keys,
            )
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            self.error(f"{label} is not valid JSON: {exc}")
            return None
        nonfinite = first_nonfinite_path(value, label)
        if nonfinite is not None:
            self.error(f"{nonfinite} must be finite")
            return None
        if not isinstance(value, dict):
            self.error(f"{label} must contain a JSON object")
            return None
        return value

    def file_ref(self, value: Any, label: str) -> Path | None:
        if not isinstance(value, dict):
            self.error(f"{label} must be an object with path and sha256")
            return None
        expected = value.get("sha256")
        if not isinstance(expected, str) or not SHA256_RE.fullmatch(expected):
            self.error(f"{label}.sha256 must be 64 lowercase hex characters")
            return None
        path = self.safe_path(value.get("path"), f"{label}.path")
        if path is not None:
            try:
                actual = sha256_file(path)
            except OSError as exc:
                self.error(f"{label} cannot be hashed: {exc}")
                return None
            if actual != expected:
                self.error(f"{label} SHA-256 mismatch: expected {expected}, got {actual}")
        return path

    def probe_media(
        self,
        path: Path,
        label: str,
        *,
        require_video: bool,
        require_audio: bool,
    ) -> MediaInfo | None:
        ffprobe = shutil.which("ffprobe")
        if ffprobe is None:
            self.error(f"{label} cannot be verified because ffprobe is unavailable")
            return None
        try:
            process = subprocess.run(
                [
                    ffprobe,
                    "-v",
                    "error",
                    "-show_format",
                    "-show_streams",
                    "-of",
                    "json",
                    str(path),
                ],
                text=True,
                capture_output=True,
                timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            self.error(f"{label} ffprobe failed: {exc}")
            return None
        if process.returncode != 0:
            self.error(f"{label} is not ffprobe-decodable media")
            return None
        try:
            payload = json.loads(process.stdout)
            duration = float(payload["format"]["duration"])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            self.error(f"{label} has no finite media duration")
            return None
        if not math.isfinite(duration) or duration <= 0:
            self.error(f"{label} duration must be positive and finite")
            return None
        streams = payload.get("streams")
        if not isinstance(streams, list):
            self.error(f"{label} has no ffprobe stream list")
            return None
        video_streams = sum(
            isinstance(stream, dict) and stream.get("codec_type") == "video"
            for stream in streams
        )
        audio_streams = sum(
            isinstance(stream, dict) and stream.get("codec_type") == "audio"
            for stream in streams
        )
        if require_video and video_streams < 1:
            self.error(f"{label} must contain a decodable video stream")
        if require_audio and audio_streams < 1:
            self.error(f"{label} must contain a decodable audio stream")
        if (require_video and video_streams < 1) or (require_audio and audio_streams < 1):
            return None
        return MediaInfo(duration, video_streams, audio_streams)

    def validate_voice_contract(self, selection_path: Path | None) -> None:
        """Delegate registry, model, reference, WAV and sidecar closure to TTS."""

        if selection_path is None:
            return
        tts_root = str(TTS_ROOT)
        if tts_root not in sys.path:
            sys.path.insert(0, tts_root)
        try:
            voice_gate = importlib.import_module("verify_voice_usage")
            result = voice_gate.verify_project_voice(
                self.project,
                selection_path,
                registry=self.voice_registry,
                current_model_validation=self.current_model_validation,
                # Formal projects must never silently accept historical Qwen
                # sidecars that lack the current portable model receipt claim.
                allow_legacy_qwen_sidecars=False,
            )
        except (ImportError, OSError, RuntimeError, TypeError, ValueError) as exc:
            self.error(f"central voice gate could not run: {exc}")
            return
        for error in result.errors:
            self.error(f"central voice gate: {error}")
        allowed_modes = {"qwen_portable_current", "legacy_explicit"}
        for evidence in result.sidecars:
            if evidence.provenance_mode not in allowed_modes:
                self.error(
                    f"central voice gate returned unknown provenance mode: "
                    f"{evidence.provenance_mode}"
                )
            if evidence.relative_path in self._voice_sidecars:
                self.error(
                    f"central voice gate returned duplicate sidecar: {evidence.relative_path}"
                )
            self._voice_sidecars[evidence.relative_path] = evidence

    def validate_narration(
        self,
        manifest: dict[str, Any],
        kind: str,
        item_ids: list[str],
        schema_version: int | None,
    ) -> tuple[str, str]:
        sequence = manifest.get("narration_sequence")
        if not isinstance(sequence, list):
            self.error("narration_sequence must be an array")
            return "", ""

        if kind != "free_exploration":
            expected = [("intro", None)]
            expected.extend(("transition", item_id) for item_id in item_ids)
            expected.extend((("work_outro", None), ("outro_cta", None)))
            actual = []
            for row in sequence:
                if isinstance(row, dict):
                    actual.append((row.get("role"), row.get("item_id")))
                else:
                    actual.append((None, None))
            if actual != expected:
                self.error(
                    "narration_sequence must be exactly intro -> each item transition -> "
                    "work_outro -> outro_cta in item order"
                )

        intro_text = ""
        cta_text = ""
        seen_ids: set[str] = set()
        listed_sidecars: set[Path] = set()
        for index, row in enumerate(sequence):
            label = f"narration_sequence[{index}]"
            if not isinstance(row, dict):
                self.error(f"{label} must be an object")
                continue
            block_id = row.get("id")
            role = row.get("role")
            text = row.get("text")
            if not isinstance(block_id, str) or not block_id.strip() or block_id in seen_ids:
                self.error(f"{label}.id must be a unique non-empty string")
            else:
                seen_ids.add(block_id)
            if role not in NARRATION_ROLES:
                self.error(f"{label}.role is invalid: {role!r}")
            if not isinstance(text, str) or not text.strip():
                self.error(f"{label}.text must be non-empty")
                text = ""
            if role == "intro":
                intro_text = text
                if "接下来" in text:
                    self.error("intro narration must not contain '接下来'")
            elif role == "outro_cta":
                cta_text = text
                if text != FIXED_OUTRO_CTA:
                    self.error("outro CTA must exactly equal tools/video/outro_cta.py canonical text")

            wav = self.safe_path(row.get("wav"), f"{label}.wav")
            sidecar = self.safe_path(row.get("sidecar"), f"{label}.sidecar")
            if sidecar is not None:
                relative_sidecar = sidecar.relative_to(self.project).as_posix()
                if sidecar in listed_sidecars:
                    self.error(f"{label}.sidecar is reused by more than one narration row")
                listed_sidecars.add(sidecar)
                evidence = self._voice_sidecars.get(relative_sidecar)
                if evidence is None:
                    self.error(
                        f"{label}.sidecar has no valid evidence from the central voice gate"
                    )
                else:
                    if evidence.input_text != text:
                        self.error(
                            f"{label}.text does not exactly match the sidecar canonical input text"
                        )
                    if wav is not None:
                        expected_wav = wav.relative_to(self.project).as_posix()
                        if evidence.output_relative_path != expected_wav:
                            self.error(
                                f"{label}.sidecar output does not point to the manifest WAV"
                            )
                    pacing_limit = (
                        TRANSITION_NARRATION_MAX_SECONDS.get(kind)
                        if schema_version is not None
                        and schema_version >= PACING_SCHEMA_VERSION
                        and role == "transition"
                        else None
                    )
                    if (
                        pacing_limit is not None
                        and evidence.duration_seconds > pacing_limit
                    ):
                        self.error(
                            f"{label}.wav duration {evidence.duration_seconds:.3f}s exceeds "
                            f"{kind} transition narration hard limit {pacing_limit:.3f}s"
                        )

        listed_relative = {
            path.relative_to(self.project).as_posix() for path in listed_sidecars
        }
        for extra in sorted(set(self._voice_sidecars) - listed_relative):
            self.error(
                f"central voice sidecar is not declared in narration_sequence: {extra}"
            )
        return intro_text, cta_text

    def validate_top_disclosure(
        self,
        kind: str,
        cover: Any,
        intro_text: str,
        items: list[dict[str, Any]],
    ) -> None:
        if not isinstance(cover, dict):
            self.error("cover must be an object")
            return
        cover_text = cover.get("text")
        if not isinstance(cover_text, str) or not cover_text.strip():
            self.error("cover.text must be non-empty")
            cover_text = ""
        disclosed = cover.get("disclosed_item_ids")
        if not isinstance(disclosed, list) or any(not isinstance(x, str) for x in disclosed):
            self.error("cover.disclosed_item_ids must be an explicit string array")
            disclosed = []
        if kind != "top_ranking":
            return
        if disclosed:
            self.error("TOP cover.disclosed_item_ids must be []")
        if COVER_ORDER_HINT_RE.search(cover_text):
            self.error("TOP cover.text must not expose internal countdown order hints")

        intro = next(
            (
                row for row in (self.manifest.get("narration_sequence") or [])
                if isinstance(row, dict) and row.get("role") == "intro"
            ),
            {},
        )
        intro_disclosed = intro.get("disclosed_item_ids")
        if not isinstance(intro_disclosed, list) or any(
            not isinstance(x, str) for x in intro_disclosed
        ):
            self.error("TOP intro.disclosed_item_ids must be an explicit string array")
        elif intro_disclosed:
            self.error("TOP intro.disclosed_item_ids must be []")

        combined = f"{cover_text}\n{intro_text}"
        if RANK_ONE_RE.search(combined):
            self.error("TOP cover/intro must not reveal the first-place rank")
        titles = [str(item.get("title", "")) for item in items]
        normalized_combined = normalized_title(combined)
        normalized_titles = [normalized_title(title) for title in titles]
        present = [
            bool(title and len(title) >= 2 and title in normalized_combined)
            for title in normalized_titles
        ]
        if present and present[-1]:
            self.error("TOP cover/intro must not reveal the first-place item title")
        if present and all(present):
            self.error("TOP cover/intro must not reveal the complete item list")

    def source_tier(self, candidate: dict[str, Any]) -> tuple[int, str]:
        return SOURCE_TIERS.get(
            (candidate.get("official") is True, candidate.get("asset_type")),
            (2, "secondary"),
        )

    def validate_source_receipt(
        self,
        receipt_ref: Any,
        *,
        selected_platform: str,
        selected_url: str,
        clip: Path | None,
        clip_sha256: Any,
        clip_duration: float | None,
        label: str,
    ) -> None:
        receipt_path = self.file_ref(receipt_ref, f"{label}.download_receipt")
        if receipt_path is None:
            return
        receipt = self.load_json_path(receipt_path, f"{label}.download_receipt")
        if receipt is None:
            return
        if set(receipt) != SOURCE_RECEIPT_REQUIRED:
            self.error(
                f"{label}.download_receipt must contain exactly the redacted local fields "
                f"{sorted(SOURCE_RECEIPT_REQUIRED)}"
            )
        if receipt.get("schema_version") != 1 or receipt.get("kind") != "selected_download":
            self.error(f"{label}.download_receipt schema/kind mismatch")
        if receipt.get("platform") != selected_platform or receipt.get("url") != selected_url:
            self.error(f"{label}.download_receipt is not bound to the selected platform/url")
        if parse_aware_datetime(receipt.get("downloaded_at")) is None:
            self.error(f"{label}.download_receipt.downloaded_at must be ISO-8601 with timezone")

        raw_ref = receipt.get("raw_asset")
        if not isinstance(raw_ref, dict) or set(raw_ref) != {"path", "sha256"}:
            self.error(f"{label}.download_receipt.raw_asset must contain exactly path and sha256")
        raw_path = self.file_ref(raw_ref, f"{label}.download_receipt.raw_asset")
        raw_info = (
            self.probe_media(
                raw_path,
                f"{label}.download_receipt.raw_asset",
                require_video=True,
                require_audio=True,
            )
            if raw_path is not None
            else None
        )
        claimed_raw_duration = receipt.get("raw_duration_sec")
        if not is_finite_number(claimed_raw_duration) or float(claimed_raw_duration) <= 0:
            self.error(f"{label}.download_receipt.raw_duration_sec must be positive and finite")
        elif raw_info is not None and abs(
            float(claimed_raw_duration) - raw_info.duration_sec
        ) > MEDIA_DURATION_TOLERANCE_SEC:
            self.error(f"{label}.download_receipt.raw_duration_sec is stale")

        derivation = receipt.get("derivation")
        if not isinstance(derivation, dict):
            self.error(f"{label}.download_receipt.derivation must be an object")
            return
        if set(derivation) != SOURCE_DERIVATION_REQUIRED:
            self.error(
                f"{label}.download_receipt.derivation must contain exactly "
                f"{sorted(SOURCE_DERIVATION_REQUIRED)}"
            )
        raw_sha = raw_ref.get("sha256") if isinstance(raw_ref, dict) else None
        if derivation.get("input_sha256") != raw_sha:
            self.error(f"{label}.download_receipt.derivation input_sha256 is stale")
        for key in ("tool", "operation"):
            if not isinstance(derivation.get(key), str) or not derivation[key].strip():
                self.error(f"{label}.download_receipt.derivation.{key} must be non-empty")
        start = derivation.get("source_start_sec")
        end = derivation.get("source_end_sec")
        if not is_finite_number(start) or not is_finite_number(end):
            self.error(
                f"{label}.download_receipt.derivation source_start_sec/source_end_sec "
                "must be finite numbers"
            )
        else:
            start_value, end_value = float(start), float(end)
            if start_value < 0 or end_value <= start_value:
                self.error(
                    f"{label}.download_receipt.derivation source window must satisfy "
                    "0 <= start < end"
                )
            if raw_info is not None and end_value > (
                raw_info.duration_sec + MEDIA_DURATION_TOLERANCE_SEC
            ):
                self.error(f"{label}.download_receipt.derivation source window exceeds raw media")

        output_ref = derivation.get("output")
        if not isinstance(output_ref, dict) or set(output_ref) != {"path", "sha256"}:
            self.error(f"{label}.download_receipt.derivation.output needs exactly path and sha256")
        else:
            output_path = self.file_ref(
                output_ref, f"{label}.download_receipt.derivation.output"
            )
            if clip is not None and output_path is not None and output_path.resolve() != clip.resolve():
                self.error(f"{label}.download_receipt.derivation.output is not the item clip")
            if output_ref.get("sha256") != clip_sha256:
                self.error(f"{label}.download_receipt.derivation.output SHA is not the item clip SHA")
        output_duration = derivation.get("output_duration_sec")
        if not is_finite_number(output_duration) or float(output_duration) <= 0:
            self.error(
                f"{label}.download_receipt.derivation.output_duration_sec must be positive and finite"
            )
        elif clip_duration is not None and abs(
            float(output_duration) - clip_duration
        ) > MEDIA_DURATION_TOLERANCE_SEC:
            self.error(f"{label}.download_receipt.derivation.output_duration_sec is stale")

    def validate_sources(
        self,
        item: dict[str, Any],
        label: str,
        clip: Path | None,
        clip_duration: float | None,
    ) -> None:
        sources = item.get("sources")
        if not isinstance(sources, dict):
            self.error(f"{label}.sources must be an object")
            return
        target = sources.get("target_version")
        if not isinstance(target, dict):
            self.error(f"{label}.sources.target_version must be an object")
            return
        target_kind = target.get("kind")
        target_performer = target.get("performer")
        if target_kind not in {"original", "cover"}:
            self.error(f"{label}.sources.target_version.kind must be original or cover")
        if not isinstance(target_performer, str) or not target_performer.strip():
            self.error(f"{label}.sources.target_version.performer must be non-empty")
        elif item.get("performer") != target_performer:
            self.error(f"{label}.performer must match sources.target_version.performer")
        if target_kind == "cover" and not str(target.get("original_artist", "")).strip():
            self.error(f"{label}.sources.target_version.original_artist is required for covers")

        platforms = sources.get("platforms")
        if not isinstance(platforms, dict):
            self.error(f"{label}.sources.platforms must be an object")
            return
        all_candidates: list[tuple[str, dict[str, Any]]] = []
        for platform in ("youtube", "bilibili"):
            record = platforms.get(platform)
            platform_label = f"{label}.sources.platforms.{platform}"
            if not isinstance(record, dict):
                self.error(f"{platform_label} must be an object")
                continue
            if record.get("searched") is not True:
                self.error(f"{platform_label}.searched must be true")
            queries = record.get("search_queries")
            if not isinstance(queries, list) or not queries or any(
                not isinstance(query, str) or not query.strip() for query in queries
            ):
                self.error(f"{platform_label}.search_queries must be a non-empty string array")
            candidates = record.get("candidates")
            if not isinstance(candidates, list):
                self.error(f"{platform_label}.candidates must be an array")
                continue
            if not candidates and not str(record.get("no_usable_reason", "")).strip():
                self.error(f"{platform_label} needs candidates or no_usable_reason")
            for index, candidate in enumerate(candidates):
                candidate_label = f"{platform_label}.candidates[{index}]"
                if not isinstance(candidate, dict):
                    self.error(f"{candidate_label} must be an object")
                    continue
                url = candidate.get("url")
                try:
                    parsed = urlparse(url) if isinstance(url, str) else None
                    host = (parsed.hostname or "").lower() if parsed else ""
                except ValueError:
                    parsed = None
                    host = ""
                if (
                    parsed is None
                    or parsed.scheme not in {"http", "https"}
                    or not host
                    or not any(
                        host == allowed or host.endswith(f".{allowed}")
                        for allowed in PLATFORM_HOSTS[platform]
                    )
                ):
                    self.error(f"{candidate_label}.url does not belong to {platform}")
                if candidate.get("version_kind") not in {"original", "cover"}:
                    self.error(f"{candidate_label}.version_kind is invalid")
                if candidate.get("asset_type") not in {"mv", "live", "show", "secondary"}:
                    self.error(f"{candidate_label}.asset_type is invalid")
                if not isinstance(candidate.get("official"), bool):
                    self.error(f"{candidate_label}.official must be boolean")
                if not isinstance(candidate.get("usable"), bool):
                    self.error(f"{candidate_label}.usable must be boolean")
                if not str(candidate.get("performer", "")).strip():
                    self.error(f"{candidate_label}.performer must be non-empty")
                if candidate.get("usable") is False and not str(
                    candidate.get("reject_reason", "")
                ).strip():
                    self.error(f"{candidate_label}.reject_reason is required when unusable")
                all_candidates.append((platform, candidate))

        selection = sources.get("selection")
        if not isinstance(selection, dict):
            self.error(f"{label}.sources.selection must be an object")
            return
        selected_platform = selection.get("platform")
        selected_url = selection.get("url")
        if selected_platform not in PLATFORM_HOSTS:
            self.error(f"{label}.sources.selection.platform is invalid")
            return
        matches = [
            candidate
            for platform, candidate in all_candidates
            if platform == selected_platform and candidate.get("url") == selected_url
        ]
        if len(matches) != 1:
            self.error(f"{label}.sources.selection must match exactly one platform candidate")
            return
        selected = matches[0]
        if selected.get("usable") is not True:
            self.error(f"{label}.sources.selection points to an unusable candidate")
        if not str(selection.get("decision_reason", "")).strip():
            self.error(f"{label}.sources.selection.decision_reason must be non-empty")
        self.validate_source_receipt(
            selection.get("download_receipt"),
            selected_platform=selected_platform,
            selected_url=selected_url,
            clip=clip,
            clip_sha256=item.get("clip_sha256"),
            clip_duration=clip_duration,
            label=f"{label}.sources.selection",
        )

        matching_target = [
            candidate
            for _, candidate in all_candidates
            if candidate.get("usable") is True
            and candidate.get("version_kind") == target_kind
            and candidate.get("performer") == target_performer
        ]
        fallback = sources.get("cover_fallback")
        if target_kind == "cover" and not (
            selected.get("version_kind") == "cover"
            and selected.get("performer") == target_performer
        ):
            if not isinstance(fallback, dict) or fallback.get("used") is not True:
                self.error(f"{label} selected original source without explicit cover_fallback")
            else:
                if matching_target:
                    self.error(f"{label} cannot fall back: a usable target cover exists")
                for platform in ("youtube", "bilibili"):
                    if not str(fallback.get(f"{platform}_reason", "")).strip():
                        self.error(f"{label}.sources.cover_fallback.{platform}_reason is required")
            if not (
                selected.get("version_kind") == "original"
                and selected.get("performer") == target.get("original_artist")
            ):
                self.error(
                    f"{label} cover fallback must select the declared original artist/version"
                )
            effective_kind = selected.get("version_kind")
            effective_performer = selected.get("performer")
        else:
            if (
                selected.get("version_kind") != target_kind
                or selected.get("performer") != target_performer
            ):
                self.error(f"{label} selected source does not match target version/performer")
            if isinstance(fallback, dict) and fallback.get("used") is True:
                self.error(
                    f"{label}.sources.cover_fallback.used must be false when no fallback occurred"
                )
            effective_kind = target_kind
            effective_performer = target_performer

        comparable = [
            candidate
            for _, candidate in all_candidates
            if candidate.get("usable") is True
            and candidate.get("version_kind") == effective_kind
            and candidate.get("performer") == effective_performer
        ]
        if comparable:
            best_tier = min(self.source_tier(candidate)[0] for candidate in comparable)
            selected_tier, selected_label = self.source_tier(selected)
            official_choice = sources.get("official_choice")
            if not isinstance(official_choice, dict):
                self.error(f"{label}.sources.official_choice must be an object")
            else:
                if official_choice.get("selected_tier") != selected_label:
                    self.error(f"{label}.sources.official_choice.selected_tier is stale")
                if selected_tier > 0 and not str(official_choice.get("fallback_reason", "")).strip():
                    self.error(f"{label}.sources.official_choice.fallback_reason is required")
                if selected_tier == 0 and official_choice.get("fallback_reason") not in {None, ""}:
                    self.error(f"{label} official MV selection must not claim a fallback reason")
            if selected_tier != best_tier:
                self.error(f"{label} did not select the best available official source tier")

    def validate_clip(
        self, item: dict[str, Any], label: str
    ) -> tuple[Path | None, float | None]:
        clip = self.safe_path(item.get("clip"), f"{label}.clip")
        expected = item.get("clip_sha256")
        if not isinstance(expected, str) or not SHA256_RE.fullmatch(expected):
            self.error(f"{label}.clip_sha256 must be 64 lowercase hex characters")
        elif clip is not None:
            try:
                actual = sha256_file(clip)
            except OSError as exc:
                self.error(f"{label}.clip cannot be hashed: {exc}")
                return clip, None
            if actual != expected:
                self.error(f"{label}.clip_sha256 mismatch: expected {expected}, got {actual}")
        info = (
            self.probe_media(
                clip,
                f"{label}.clip",
                require_video=True,
                require_audio=True,
            )
            if clip is not None
            else None
        )
        return clip, info.duration_sec if info is not None else None

    def analysis_for(self, payload: dict[str, Any], key: str) -> Any:
        if "lead_segments" in payload or "vocal_segments" in payload:
            return payload
        clips = payload.get("clips") if isinstance(payload.get("clips"), dict) else payload
        return clips.get(key) if isinstance(clips, dict) else None

    def validate_review_approval_metadata(
        self,
        approval_payload: dict[str, Any],
        item: dict[str, Any],
        label: str,
    ) -> None:
        if set(approval_payload) != {"schema_version", "approvals"}:
            self.error(f"{label} must contain exactly schema_version and approvals")
        if approval_payload.get("schema_version") != 1:
            self.error(f"{label}.schema_version must be 1")
        approvals = approval_payload.get("approvals")
        if not isinstance(approvals, dict):
            self.error(f"{label}.approvals must be an object")
            return
        row = approvals.get(item.get("id")) or approvals.get(item.get("clip"))
        if not isinstance(row, dict):
            self.error(f"{label} has no approval for the current item/clip")
            return
        if set(row) != REVIEW_APPROVAL_REQUIRED:
            self.error(
                f"{label} approval must contain exactly {sorted(REVIEW_APPROVAL_REQUIRED)}"
            )
        reviewer_kind = row.get("reviewer_kind")
        if reviewer_kind not in {"agent", "human"}:
            self.error(f"{label} approval.reviewer_kind must be agent or human")
        elif self.require_human_review and reviewer_kind != "human":
            self.error(
                f"{label} approval.reviewer_kind must be human in release mode; "
                "agent observation is local-only"
            )
        if not isinstance(row.get("reviewer"), str) or not row["reviewer"].strip():
            self.error(f"{label} approval.reviewer must be non-empty")
        if parse_aware_datetime(row.get("reviewed_at")) is None:
            self.error(f"{label} approval.reviewed_at must be ISO-8601 with timezone")
        self.evidence_refs(row.get("evidence_files"), f"{label} approval.evidence_files")

    def validate_vocal_evidence(
        self, item: dict[str, Any], label: str, clip_duration: float | None
    ) -> None:
        evidence_path = self.file_ref(item.get("evidence"), f"{label}.evidence")
        if evidence_path is None:
            return
        evidence = self.load_json_path(evidence_path, f"{label}.evidence")
        if evidence is None:
            return
        if evidence.get("schema_version") != 1 or evidence.get("kind") != "vocal_showcase":
            self.error(f"{label}.evidence schema/kind mismatch")
            return
        allowed_evidence_keys = set(VOCAL_EVIDENCE_REQUIRED) | {"approval", "mode"}
        if not VOCAL_EVIDENCE_REQUIRED.issubset(evidence) or not set(evidence).issubset(
            allowed_evidence_keys
        ):
            self.error(
                f"{label}.evidence fields do not match the vocal_showcase contract"
            )
        if evidence.get("item_id") != item.get("id"):
            self.error(f"{label}.evidence item_id mismatch")
        mode = evidence.get("mode")
        if mode not in {None, "intro_hard_restart"}:
            self.error(f"{label}.evidence.mode is invalid")
        if evidence.get("clip") != item.get("clip") or evidence.get("clip_sha256") != item.get(
            "clip_sha256"
        ):
            self.error(f"{label}.evidence is not bound to the current clip path/hash")
        analysis_path = self.file_ref(evidence.get("analysis"), f"{label}.evidence.analysis")
        window = evidence.get("window")
        if not isinstance(window, dict) or any(
            not is_finite_number(window.get(name))
            for name in ("narr_end_src", "show_start_src", "show_end_src")
        ):
            self.error(f"{label}.evidence.window must contain three finite source times")
            return
        narr_end = float(window["narr_end_src"])
        show_start = float(window["show_start_src"])
        show_end = float(window["show_end_src"])
        if not (0 <= narr_end <= show_start < show_end):
            self.error(f"{label}.evidence.window is not ordered")
            return
        if clip_duration is not None and show_end > (
            clip_duration + MEDIA_DURATION_TOLERANCE_SEC
        ):
            self.error(f"{label}.evidence.window exceeds the current clip duration")
        if analysis_path is None:
            return
        analysis_payload = self.load_json_path(analysis_path, f"{label}.evidence.analysis")
        if analysis_payload is None:
            return
        analysis_key = evidence.get("analysis_key")
        if not isinstance(analysis_key, str) or not analysis_key.strip():
            self.error(f"{label}.evidence.analysis_key must be non-empty")
            return
        analysis = self.analysis_for(analysis_payload, analysis_key)
        if analysis is None:
            self.error(f"{label}.evidence analysis_key not found in analysis file")
            return
        if not isinstance(analysis, dict):
            self.error(f"{label}.evidence selected analysis must be an object")
            return
        if analysis.get("source_sha256") != item.get("clip_sha256"):
            self.error(f"{label}.evidence analysis source_sha256 is not the current clip SHA")
        analysis_duration = analysis.get("duration")
        if not is_finite_number(analysis_duration) or float(analysis_duration) <= 0:
            self.error(f"{label}.evidence analysis duration must be positive and finite")
        else:
            analysis_duration_value = float(analysis_duration)
            if clip_duration is not None and abs(
                analysis_duration_value - clip_duration
            ) > MEDIA_DURATION_TOLERANCE_SEC:
                self.error(f"{label}.evidence analysis duration is stale for the current clip")
            if show_end > analysis_duration_value + MEDIA_DURATION_TOLERANCE_SEC:
                self.error(f"{label}.evidence.window exceeds the analyzed clip duration")
        try:
            verdict = showcase_align.verify_song(
                analysis,
                key=item.get("id"),
                clip=item.get("clip"),
                mode=mode,
                **window,
            )
        except (KeyError, TypeError, ValueError) as exc:
            self.error(f"{label}.evidence analysis cannot be recomputed: {exc}")
            return
        computed_status = verdict["status"]
        if computed_status == "REVIEW":
            approval_path = self.file_ref(evidence.get("approval"), f"{label}.evidence.approval")
            if approval_path is not None:
                approval_payload = self.load_json_path(
                    approval_path, f"{label}.evidence.approval"
                )
                if approval_payload is not None:
                    self.validate_review_approval_metadata(
                        approval_payload, item, f"{label}.evidence.approval"
                    )
                    try:
                        approval, approval_error = showcase_align._validate_approval(
                            showcase_align._load_approvals(approval_payload),
                            item.get("id"),
                            item.get("clip"),
                            expected_window=window,
                            expected_analysis=analysis,
                            require_human_review=self.require_human_review,
                        )
                    except (KeyError, TypeError, ValueError) as exc:
                        approval, approval_error = None, f"malformed approval: {exc}"
                    if approval is not None:
                        computed_status = (
                            "APPROVED"
                            if approval["reviewer_kind"] == "human"
                            else "OBSERVED"
                        )
                    else:
                        self.error(f"{label}.evidence approval is invalid: {approval_error}")
        if computed_status not in {"OK", "OBSERVED", "APPROVED"}:
            self.error(f"{label}.evidence recomputed showcase status is {computed_status}")
        if evidence.get("status") != computed_status:
            self.error(
                f"{label}.evidence declared status {evidence.get('status')} "
                f"does not match recomputed {computed_status}"
            )

    def evidence_refs(self, value: Any, label: str) -> None:
        if not isinstance(value, list) or not value:
            self.error(f"{label} must contain at least one hash-bound evidence file")
            return
        for index, ref in enumerate(value):
            self.file_ref(ref, f"{label}[{index}]")

    def validate_boundary(
        self,
        boundary: Any,
        expected_time: float,
        allowed_kinds: set[str],
        label: str,
    ) -> None:
        if not isinstance(boundary, dict):
            self.error(f"{label} must be an object")
            return
        if boundary.get("status") != "verified":
            self.error(f"{label}.status must be verified")
        if boundary.get("kind") not in allowed_kinds:
            self.error(f"{label}.kind is not an auditable boundary kind")
        measured = boundary.get("time_sec")
        if not is_finite_number(measured):
            self.error(f"{label}.time_sec must be finite")
        elif abs(float(measured) - expected_time) > 0.05:
            self.error(f"{label}.time_sec is not bound to the configured window")
        if not str(boundary.get("reason", "")).strip():
            self.error(f"{label}.reason must be non-empty")
        review = boundary.get("review")
        if not isinstance(review, dict) or not str(review.get("method", "")).strip():
            self.error(f"{label}.review.method must document the manual review")
        else:
            reviewed_at = review.get("reviewed_at")
            try:
                date.fromisoformat(reviewed_at)
            except (TypeError, ValueError):
                self.error(f"{label}.review.reviewed_at must use YYYY-MM-DD")
        self.evidence_refs(boundary.get("evidence_files"), f"{label}.evidence_files")

    def validate_instrumental_evidence(
        self, item: dict[str, Any], label: str, clip_duration: float | None
    ) -> None:
        evidence_path = self.file_ref(item.get("evidence"), f"{label}.evidence")
        if evidence_path is None:
            return
        evidence = self.load_json_path(evidence_path, f"{label}.evidence")
        if evidence is None:
            return
        if evidence.get("schema_version") != 1 or evidence.get("kind") != "instrumental_plan":
            self.error(f"{label}.evidence schema/kind mismatch")
            return
        if set(evidence) != INSTRUMENTAL_EVIDENCE_REQUIRED:
            self.error(
                f"{label}.evidence must contain exactly the instrumental_plan contract fields"
            )
        if evidence.get("status") != "OK" or evidence.get("item_id") != item.get("id"):
            self.error(f"{label}.evidence status/item_id mismatch")
        if evidence.get("clip") != item.get("clip") or evidence.get("clip_sha256") != item.get(
            "clip_sha256"
        ):
            self.error(f"{label}.evidence is not bound to the current clip path/hash")
        claimed_clip_duration = evidence.get("clip_duration_sec")
        if not is_finite_number(claimed_clip_duration) or float(claimed_clip_duration) <= 0:
            self.error(f"{label}.evidence.clip_duration_sec must be positive and finite")
        elif clip_duration is not None and abs(
            float(claimed_clip_duration) - clip_duration
        ) > MEDIA_DURATION_TOLERANCE_SEC:
            self.error(f"{label}.evidence.clip_duration_sec is stale")
        window = evidence.get("window")
        if not isinstance(window, dict):
            self.error(f"{label}.evidence.window must be an object")
            return
        start, end = window.get("start_sec"), window.get("end_sec")
        if any(not is_finite_number(value) for value in (start, end)):
            self.error(f"{label}.evidence.window start/end must be finite")
            return
        start, end = float(start), float(end)
        if start < 0 or end <= start:
            self.error(f"{label}.evidence.window must satisfy 0 <= start < end")
            return
        if clip_duration is not None and end > clip_duration + MEDIA_DURATION_TOLERANCE_SEC:
            self.error(f"{label}.evidence.window exceeds the current clip duration")
        continuity = evidence.get("continuity")
        if not isinstance(continuity, dict):
            self.error(f"{label}.evidence.continuity must be an object")
        else:
            if continuity.get("status") != "verified":
                self.error(f"{label}.evidence.continuity.status must be verified")
            measured = continuity.get("continuous_duration_sec")
            if not is_finite_number(measured):
                self.error(f"{label}.evidence.continuity duration must be finite")
            elif abs(float(measured) - (end - start)) > 0.05:
                self.error(f"{label}.evidence.continuity duration does not match window")
            if not str(continuity.get("method", "")).strip() or not str(
                continuity.get("reason", "")
            ).strip():
                self.error(f"{label}.evidence.continuity method/reason must be non-empty")
            self.evidence_refs(
                continuity.get("evidence_files"),
                f"{label}.evidence.continuity.evidence_files",
            )
        boundaries = evidence.get("boundaries")
        if not isinstance(boundaries, dict):
            self.error(f"{label}.evidence.boundaries must be an object")
            return
        self.validate_boundary(
            boundaries.get("start"), start, START_BOUNDARY_KINDS, f"{label}.evidence.boundaries.start"
        )
        self.validate_boundary(
            boundaries.get("end"), end, END_BOUNDARY_KINDS, f"{label}.evidence.boundaries.end"
        )

    def verify(self, manifest_path: Path) -> list[str]:
        manifest = self.load_json_path(manifest_path, "project manifest")
        if manifest is None:
            return self.errors
        self.manifest = manifest
        schema_version = manifest.get("schema_version")
        if type(schema_version) is not int or schema_version not in SUPPORTED_SCHEMA_VERSIONS:
            self.error(
                f"schema_version must be one of {sorted(SUPPORTED_SCHEMA_VERSIONS)}"
            )
            schema_version = None
        kind = manifest.get("project_kind")
        if kind not in PROJECT_KINDS:
            self.error(f"project_kind must be one of {sorted(PROJECT_KINDS)}")
            kind = ""
        if kind == "free_exploration" and not str(manifest.get("rationale", "")).strip():
            self.error("free_exploration requires a non-empty rationale")

        selection_path = self.safe_path(manifest.get("voice_selection"), "voice_selection")
        selection = (
            self.load_json_path(selection_path, "voice_selection")
            if selection_path is not None
            else None
        )
        if selection is None:
            selection = {}
        if not str(selection.get("resolved_voice_id", "")).strip():
            self.error("voice_selection.resolved_voice_id must be non-empty")
        self.validate_voice_contract(selection_path)

        raw_items = manifest.get("items")
        if not isinstance(raw_items, list):
            self.error("items must be an array")
            raw_items = []
        items: list[dict[str, Any]] = []
        item_ids: list[str] = []
        for index, item in enumerate(raw_items):
            label = f"items[{index}]"
            if not isinstance(item, dict):
                self.error(f"{label} must be an object")
                continue
            item_id = item.get("id")
            if not isinstance(item_id, str) or not item_id.strip() or item_id in item_ids:
                self.error(f"{label}.id must be a unique non-empty string")
                continue
            if not str(item.get("title", "")).strip():
                self.error(f"{label}.title must be non-empty")
            if not str(item.get("performer", "")).strip():
                self.error(f"{label}.performer must be non-empty")
            if kind != "top_ranking" and item.get("rank") is not None:
                self.error(f"{label}.rank is forbidden for {kind or 'invalid project kind'}")
            item_ids.append(item_id)
            items.append(item)

        if kind != "free_exploration" and not items:
            self.error(f"{kind or 'non-free project'} requires at least one item")
        if kind == "top_ranking":
            if len(items) < 2:
                self.error("top_ranking requires at least two items")
            ranks = [item.get("rank") for item in items]
            expected_ranks = list(range(len(items), 0, -1))
            valid_rank_types = all(
                isinstance(rank, int) and not isinstance(rank, bool) for rank in ranks
            )
            if not valid_rank_types or ranks != expected_ranks:
                self.error(
                    f"TOP ranks must be strict N->1 order: expected {expected_ranks}, got {ranks}"
                )

        intro_text, _ = self.validate_narration(
            manifest,
            kind,
            item_ids,
            schema_version,
        )
        self.validate_top_disclosure(kind, manifest.get("cover"), intro_text, items)

        for index, item in enumerate(items):
            label = f"items[{index}]"
            clip, clip_duration = self.validate_clip(item, label)
            self.validate_sources(item, label, clip, clip_duration)
            mode = item.get("audio_mode")
            if mode == "vocal":
                self.validate_vocal_evidence(item, label, clip_duration)
            elif mode == "instrumental":
                self.validate_instrumental_evidence(item, label, clip_duration)
            else:
                self.error(f"{label}.audio_mode must be vocal or instrumental")
        return self.errors


def verify_project(
    project: Path,
    manifest: str = "project-manifest.json",
    *,
    voice_registry: Any = None,
    current_model_validation: dict[str, Any] | None = None,
    require_human_review: bool = False,
) -> list[str]:
    verifier = ProjectVerifier(
        project,
        voice_registry=voice_registry,
        current_model_validation=current_model_validation,
        require_human_review=require_human_review,
    )
    if not verifier.project_valid:
        return verifier.errors
    manifest_path = verifier.safe_path(manifest, "manifest")
    if manifest_path is None:
        return verifier.errors
    return verifier.verify(manifest_path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--manifest", default="project-manifest.json")
    parser.add_argument(
        "--require-human-review",
        action="store_true",
        help="发布级严格模式：展示 REVIEW 只接受 reviewer_kind=human",
    )
    args = parser.parse_args()
    errors = verify_project(
        args.project,
        args.manifest,
        require_human_review=args.require_human_review,
    )
    if errors:
        print("PROJECT CONTRACT: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PROJECT CONTRACT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
