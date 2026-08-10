"""Opt-in regressions over historical real audio.

Run with the repository's audio-analysis environment:

    CC_MEDIA_AUDIO_REGRESSION=1 \
      tools/tts/venv/bin/python -m unittest \
      tools.video.tests.test_real_audio_regression

The large/media inputs deliberately stay in ignored ``sandbox/`` projects. A
normal unit-test run validates the manifest but skips decoding and inference.
Even with the opt-in flag, a checkout with no manifest fixtures skips before
loading Whisper; missing local media is not a detector failure.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import unittest
from pathlib import Path
from typing import Any, Iterable
from unittest import mock


TEST_DIR = Path(__file__).resolve().parent
REPO_ROOT = TEST_DIR.parents[2]
MANIFEST_PATH = TEST_DIR / "audio_regression_manifest.json"
RUN_REAL_AUDIO = os.environ.get("CC_MEDIA_AUDIO_REGRESSION") == "1"

LEAD_LABELS = {
    "lead",
    "lead_vocal",
    "lead-vocal",
    "solo_singing",
    "target_lead",
    "target_lead_vocal",
}

REVIEW_LABELS = {
    "singing_or_group_review",
    "live_singing_review",
    "low_confidence_lyrics_review",
    "weak_lexical_review",
}

SCORE_KEYS = {
    "lead_score",
    "lead_probability",
    "lead_vocal_score",
    "lead_vocal_probability",
    "singer_probability",
    "target_lead_score",
    "target_lead_probability",
    "target_vocal_score",
    "target_vocal_probability",
}


def _load_manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _manifest_fixture_paths(manifest: dict[str, Any]) -> list[Path]:
    rows = list(manifest.get("samples", [])) + list(manifest.get("boundary_cases", []))
    return [REPO_ROOT / row["path"] for row in rows]


def _pair(segment: Any) -> tuple[float, float] | None:
    if isinstance(segment, (list, tuple)) and len(segment) >= 2:
        return float(segment[0]), float(segment[1])
    if isinstance(segment, dict):
        start = segment.get("start", segment.get("start_sec"))
        end = segment.get("end", segment.get("end_sec"))
        if start is not None and end is not None:
            return float(start), float(end)
    return None


def _coverage(segments: Iterable[Any], window_start: float, window_end: float) -> float:
    """Union coverage, accepting either ``[start, end]`` or segment dicts."""
    spans = []
    for value in segments:
        pair = _pair(value)
        if pair is None:
            continue
        start, end = pair
        start = max(window_start, min(window_end, start))
        end = max(window_start, min(window_end, end))
        if end > start:
            spans.append((start, end))
    duration = window_end - window_start
    if not spans or duration <= 0:
        return 0.0
    spans.sort()
    merged = [list(spans[0])]
    for start, end in spans[1:]:
        if start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return sum(end - start for start, end in merged) / duration


def _numeric_scores(value: Any) -> list[float]:
    """Read common lead-score spellings from evidence/segment score objects."""
    scores: list[float] = []
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in SCORE_KEYS and isinstance(item, (int, float)) and not isinstance(item, bool):
                scores.append(float(item))
            elif normalized in {"evidence", "scores", "probabilities"}:
                scores.extend(_numeric_scores(item))
    return [max(0.0, min(1.0, score)) for score in scores]


def _labels(value: Any) -> set[str]:
    labels: set[str] = set()
    if isinstance(value, dict):
        for key in ("label", "class", "classification", "predicted_label"):
            item = value.get(key)
            if isinstance(item, str):
                labels.add(item.strip().lower().replace(" ", "_"))
        for key in ("evidence", "scores", "probabilities"):
            labels.update(_labels(value.get(key)))
    elif isinstance(value, list):
        for item in value:
            labels.update(_labels(item))
    return labels


def _view(result: Any, window_start: float, window_end: float) -> dict[str, Any]:
    """Normalize legacy and planned detector schemas without pinning one API."""
    if not isinstance(result, dict):
        raise AssertionError(f"detect() must return a mapping, got {type(result).__name__}")

    # New output should expose lead_segments. vocal_segments remains a useful
    # compatibility fallback while the detector migration is in progress.
    segments = result.get("lead_segments")
    if segments is None:
        segments = result.get("vocal_segments", [])
    if not isinstance(segments, list):
        segments = []
    vocal_candidates = result.get("vocal_segments", [])
    if not isinstance(vocal_candidates, list):
        vocal_candidates = []

    score_objects: list[Any] = []
    segment_scores = result.get("segment_scores", [])
    if isinstance(segment_scores, list):
        for row in segment_scores:
            pair = _pair(row)
            if pair is None or (pair[1] > window_start and pair[0] < window_end):
                score_objects.append(row)

    # A top-level evidence score normally summarizes the whole file and must
    # not leak into a small negative window. It is usable for a whole-file
    # fixture or when no analysis duration is reported.
    analysis_duration = result.get("duration")
    whole_file = (
        window_start <= 0.01
        and isinstance(analysis_duration, (int, float))
        and window_end >= float(analysis_duration) - 0.1
    )
    if whole_file or (analysis_duration is None and not segment_scores):
        score_objects.append(result)

    scores: list[float] = []
    labels: set[str] = set()
    for obj in score_objects:
        scores.extend(_numeric_scores(obj))
        labels.update(_labels(obj))

    return {
        "coverage": _coverage(segments, window_start, window_end),
        "candidate_coverage": _coverage(vocal_candidates, window_start, window_end),
        "lead_score": sum(scores) / len(scores) if scores else None,
        "labels": labels,
        "recognized": bool(
            "lead_segments" in result
            or "vocal_segments" in result
            or scores
            or labels
        ),
        "evidence_level": result.get("evidence_level"),
    }


class AudioRegressionManifestTests(unittest.TestCase):
    def test_manifest_contract(self) -> None:
        manifest = _load_manifest()
        self.assertEqual(1, manifest["schema_version"])
        known_labels = set(manifest["labels"])
        seen: set[str] = set()
        self.assertGreaterEqual(len(manifest["samples"]), 6)

        for sample in manifest["samples"]:
            with self.subTest(sample=sample.get("id")):
                sample_id = sample["id"]
                self.assertNotIn(sample_id, seen)
                seen.add(sample_id)
                self.assertFalse(Path(sample["path"]).is_absolute())
                self.assertNotIn("..", Path(sample["path"]).parts)
                self.assertGreater(float(sample["end_sec"]), float(sample["start_sec"]))
                expected = sample["expected"]
                self.assertIn(expected["label"], known_labels)
                self.assertIsInstance(expected["is_target_lead_vocal"], bool)
                self.assertIn(expected["auto_disposition"], {"lead", "review", "reject"})
                if sample.get("sha256") is not None:
                    self.assertRegex(sample["sha256"], r"^[0-9a-f]{64}$")

        for case in manifest.get("boundary_cases", []):
            with self.subTest(boundary=case.get("id")):
                self.assertGreater(case["bad_show_end_src"], case["show_start_src"])
                self.assertGreaterEqual(
                    case["expected_safe_end_min"],
                    case["show_start_src"] + case["min_show_sec"],
                )
                self.assertGreater(case["expected_safe_end_max"], case["expected_safe_end_min"])
                self.assertRegex(case["sha256"], r"^[0-9a-f]{64}$")

    def test_normalizer_accepts_planned_segment_scores(self) -> None:
        result = {
            "duration": 60.0,
            "lead_segments": [[10.0, 20.0]],
            "segment_scores": [
                {
                    "start_sec": 10.0,
                    "end_sec": 20.0,
                    "label": "target_lead_vocal",
                    "scores": {"lead_vocal_probability": 0.82},
                },
                {
                    "start_sec": 30.0,
                    "end_sec": 40.0,
                    "label": "crowd",
                    "scores": {"lead_vocal_probability": 0.08},
                },
            ],
            "evidence": {"lead_vocal_probability": 0.50},
        }
        lead = _view(result, 12.0, 18.0)
        crowd = _view(result, 32.0, 38.0)
        self.assertEqual(1.0, lead["coverage"])
        self.assertAlmostEqual(0.82, lead["lead_score"])
        self.assertIn("target_lead_vocal", lead["labels"])
        self.assertEqual(0.0, crowd["coverage"])
        self.assertAlmostEqual(0.08, crowd["lead_score"])
        self.assertNotIn("target_lead_vocal", crowd["labels"])

    def test_lead_segments_take_priority_over_legacy_candidates(self) -> None:
        result = {
            "duration": 10.0,
            "vocal_segments": [[0.0, 10.0]],
            "lead_segments": [],
            "segment_scores": [],
        }
        self.assertEqual(0.0, _view(result, 0.0, 10.0)["coverage"])

    def test_no_fixture_skips_before_importing_whisper(self) -> None:
        missing = REPO_ROOT / "sandbox" / "fixture-that-must-not-exist.wav"
        with (
            mock.patch(
                f"{__name__}._manifest_fixture_paths",
                return_value=[missing],
            ),
            mock.patch.object(importlib, "import_module") as import_module,
            self.assertRaisesRegex(unittest.SkipTest, "Whisper was not loaded"),
        ):
            RealAudioRegressionTests.setUpClass()
        import_module.assert_not_called()


@unittest.skipUnless(
    RUN_REAL_AUDIO,
    "set CC_MEDIA_AUDIO_REGRESSION=1 to run local real-audio inference",
)
class RealAudioRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        fixtures = _manifest_fixture_paths(_load_manifest())
        if not any(path.is_file() for path in fixtures):
            raise unittest.SkipTest(
                "none of the optional manifest audio fixtures are present; "
                "Whisper was not loaded"
            )
        try:
            module = importlib.import_module("tools.video.vocal_segments")
            model_name = os.environ.get("CC_MEDIA_WHISPER_MODEL", "small")
            model = module.load_whisper_model(model_name, "cpu")
            # Keep the closure unbound when stored on TestCase.
            cls.detector = staticmethod(lambda path: module.analyze(
                path,
                whisper_model=model,
                whisper_model_name=model_name,
                language=os.environ.get("CC_MEDIA_AUDIO_LANGUAGE", "zh"),
            ))
        except FileNotFoundError as exc:
            raise unittest.SkipTest(str(exc)) from exc
        except (ImportError, AttributeError) as exc:
            raise RuntimeError(
                "real-audio regressions require vocal_segments.detect and its audio dependencies"
            ) from exc

    def test_historical_target_lead_classification(self) -> None:
        manifest = _load_manifest()
        tested = 0
        hash_cache: dict[Path, str] = {}
        result_cache: dict[Path, dict[str, Any]] = {}

        for sample in manifest["samples"]:
            path = REPO_ROOT / sample["path"]
            if not path.exists():
                # Sandbox media is intentionally untracked. A checkout without
                # any corpus should skip rather than report detector breakage.
                continue

            with self.subTest(sample=sample["id"]):
                if sample.get("sha256"):
                    if path not in hash_cache:
                        hash_cache[path] = _sha256(path)
                    actual_hash = hash_cache[path]
                    self.assertEqual(sample["sha256"], actual_hash, "fixture content changed")

                start = float(sample["start_sec"])
                end = float(sample["end_sec"])
                # Analyze the original file once, exactly like production.
                # Cropping first changes percentile/normalization context and
                # can hide the historical false positive this corpus records.
                if path not in result_cache:
                    result_cache[path] = self.detector(path)
                result = result_cache[path]
                view = _view(result, start, end)
                self.assertTrue(view["recognized"], "no recognized lead-vocal evidence in detector output")
                expected = sample["expected"]
                has_lead_label = bool(view["labels"] & LEAD_LABELS)
                disposition = expected["auto_disposition"]

                if disposition == "lead":
                    min_coverage = float(expected.get("min_target_lead_coverage", 0.0))
                    min_score = float(expected.get("min_target_lead_score", 0.0))
                    coverage_pass = view["coverage"] >= min_coverage
                    score_pass = view["lead_score"] is not None and view["lead_score"] >= min_score
                    self.assertTrue(
                        coverage_pass or score_pass or has_lead_label,
                        f"expected target lead vocal, normalized result={view}",
                    )
                elif disposition == "review":
                    min_coverage = float(expected.get("min_target_lead_coverage", 0.0))
                    self.assertGreaterEqual(
                        view["candidate_coverage"], min_coverage,
                        f"expected detectable singing candidate for REVIEW, result={view}",
                    )
                    self.assertTrue(
                        bool(view["labels"] & REVIEW_LABELS) or
                        view["evidence_level"] == "candidate",
                        f"wide/group singing must remain REVIEW, result={view}",
                    )
                else:
                    max_coverage = float(expected.get("max_target_lead_coverage", 1.0))
                    max_score = float(expected.get("max_target_lead_score", 1.0))
                    self.assertLessEqual(
                        view["coverage"], max_coverage,
                        f"non-lead window received too much target-lead coverage: {view}",
                    )
                    if view["lead_score"] is not None:
                        self.assertLessEqual(
                            view["lead_score"], max_score,
                            f"non-lead window received a high target-lead score: {view}",
                        )
                    self.assertFalse(has_lead_label, f"non-lead window got a lead label: {view}")
                tested += 1

        if tested == 0:
            self.skipTest("none of the optional sandbox audio fixtures are present")

    def test_historical_next_syllable_cut_is_rejected(self) -> None:
        align = importlib.import_module("tools.video.showcase_align")
        tested = 0
        for case in _load_manifest().get("boundary_cases", []):
            path = REPO_ROOT / case["path"]
            if not path.exists():
                continue
            with self.subTest(case=case["id"]):
                self.assertEqual(case["sha256"], _sha256(path), "fixture content changed")
                result = self.detector(path)
                window = {
                    "narr_end_src": case["narr_end_src"],
                    "show_start_src": case["show_start_src"],
                }
                bad = align.verify_song(
                    result, show_end_src=case["bad_show_end_src"], **window)
                self.assertEqual("FAIL", bad["status"])
                self.assertEqual("active_vocal", bad["metrics"]["end_reason"])

                coerced = align._coerce_analysis(result)
                safe_end, auto_safe, _ = align._find_safe_end(
                    coerced["boundary_segments"],
                    case["show_start_src"],
                    case["min_show_sec"],
                )
                self.assertTrue(auto_safe)
                self.assertGreaterEqual(safe_end, case["expected_safe_end_min"])
                self.assertLessEqual(safe_end, case["expected_safe_end_max"])
                good = align.verify_song(
                    result, show_end_src=round(safe_end, 2), **window)
                self.assertEqual("OK", good["status"], good["reasons"])
                tested += 1
        if tested == 0:
            self.skipTest("none of the optional boundary fixtures are present")


if __name__ == "__main__":
    unittest.main()
