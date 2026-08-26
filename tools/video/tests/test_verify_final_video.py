"""Regression tests for the muxed-final-video fail-closed QA gate."""

from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.video import offline_asr
from tools.video import verify_final_video as gate


def fake_live_receipt(
    sources: list[gate.Asset], parameters: dict, kind: str
) -> dict:
    prefix = "final" if kind == "final_aac_asr" else "isolated"
    declared = [
        {
            "id": f"{prefix}-{index:03d}",
            "path": source.raw_path,
            "sha256": source.sha256,
        }
        for index, source in enumerate(sources)
    ]
    return {
        "schema_version": 1,
        "engine": "openai-whisper",
        "model": "small",
        "language": parameters["language"],
        "checkpoint_sha256": gate.PINNED_WHISPER_CHECKPOINT_SHA256,
        "openai_whisper_version": gate.PINNED_OPENAI_WHISPER_VERSION,
        "sources": declared,
        "results": [
            {
                "source_id": row["id"],
                "transcript": "你好",
                "segments": [
                    {
                        "id": f"{row['id']}:000000",
                        "start_sec": 0.2,
                        "end_sec": 0.8,
                        "text": "你好",
                    }
                ],
            }
            for row in declared
        ],
    }


class FakeMediaTools:
    def __init__(self) -> None:
        self.silences: list[gate.Interval] = []
        self.black: list[gate.Interval] = []
        self.frame_hashes: dict[str, str] = {}
        self.visual_frame_hashes: dict[tuple[str, float | None], str] = {}
        self.integrated_lufs = -14.0
        self.true_peak_dbtp = -1.0
        self.audio_sdr_db = 35.0
        self.authoring_review_modes: list[bool] = []

    def probe(self, path: Path) -> dict:
        if path.suffix == ".wav":
            return {
                "format": {"duration": "2.0", "format_name": "wav"},
                "streams": [
                    {
                        "codec_type": "audio",
                        "codec_name": "pcm_s16le",
                        "start_time": "0.0",
                        "duration": "2.0",
                        "sample_rate": "48000",
                        "channels": 2,
                    }
                ],
            }
        if path.name == "render.mp4":
            return {
                "format": {"duration": "2.0", "format_name": "mov,mp4"},
                "streams": [
                    {
                        "codec_type": "video",
                        "codec_name": "h264",
                        "start_time": "0.0",
                        "duration": "2.0",
                    }
                ],
            }
        return {
            "format": {"duration": "2.0", "format_name": "mov,mp4"},
            "streams": [
                {
                    "codec_type": "video",
                    "codec_name": "h264",
                    "start_time": "0.0",
                    "duration": "2.0",
                },
                {
                    "codec_type": "audio",
                    "codec_name": "aac",
                    "start_time": "0.0",
                    "duration": "2.0",
                    "sample_rate": "48000",
                    "channels": 2,
                    "bit_rate": "192000",
                },
            ],
        }

    def verify_authoring(
        self,
        project: Path,
        manifest: str,
        *,
        require_human_review: bool = False,
    ) -> list[str]:
        self.authoring_review_modes.append(require_human_review)
        return []

    def analyze_final(
        self, path: Path, duration_sec: float
    ) -> tuple[list[gate.Interval], list[gate.Interval]]:
        return list(self.silences), list(self.black)

    def video_decode_receipt(self, path: Path) -> gate.VideoDecodeReceipt:
        return gate.VideoDecodeReceipt(
            48,
            0.0,
            2.0,
            self.frame_hashes.get(path.name, "f" * 64),
        )

    def frame_rgb_receipt(
        self, path: Path, timestamp_sec: float | None = None
    ) -> gate.FrameReceipt:
        return gate.FrameReceipt(
            0.0 if timestamp_sec is None else timestamp_sec,
            1 / 24,
            self.visual_frame_hashes.get((path.name, timestamp_sec), "c" * 64),
        )

    def transcribe(
        self,
        sources: list[gate.Asset],
        parameters: dict,
        kind: str,
    ) -> dict:
        return fake_live_receipt(sources, parameters, kind)

    def loudness(self, path: Path) -> gate.Loudness:
        return gate.Loudness(self.integrated_lufs, self.true_peak_dbtp)

    def audio_sdr(self, master: Path, final: Path, duration_sec: float) -> float:
        return self.audio_sdr_db


class FakeAsrMediaTools(gate.MediaTools):
    """Real ffmpeg mechanics with deterministic ASR for fast media tests."""

    def transcribe(
        self,
        sources: list[gate.Asset],
        parameters: dict,
        kind: str,
    ) -> dict:
        return fake_live_receipt(sources, parameters, kind)

    def verify_authoring(
        self,
        project: Path,
        manifest: str,
        *,
        require_human_review: bool = False,
    ) -> list[str]:
        return []


class RealAsrFakeAuthoringTools(gate.MediaTools):
    """Real media/ASR mechanics with only the authoring dependency injected."""

    def verify_authoring(
        self,
        project: Path,
        manifest: str,
        *,
        require_human_review: bool = False,
    ) -> list[str]:
        return []


class ProjectFixture:
    def __init__(self, project: Path) -> None:
        self.project = project
        self.project.mkdir()
        self.files: dict[str, Path] = {}
        for relative, payload in (
            ("renders/final.mp4", b"current muxed final"),
            ("renders/render.mp4", b"render-only container"),
            ("audio/master.wav", b"pcm master"),
            ("audio/narration-only.wav", b"isolated narration"),
            ("qa/contact-sheet.png", b"image evidence"),
            ("qa/cover.png", b"cover evidence"),
            ("qa/leakage.txt", b"human leakage notes"),
            ("qa/release.txt", b"human release notes"),
        ):
            path = project / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
            self.files[relative] = path
        self.write_authoring_contract()
        self.manifest = self._manifest()
        self.write_asr_evidence()
        self.write_manifest()

    def asset(self, relative: str) -> dict[str, str]:
        return {"path": relative, "sha256": gate.sha256_file(self.files[relative])}

    def write_authoring_contract(self) -> None:
        selection = {"resolved_voice_id": "CV002", "fixture": True}
        selection_path = self.project / "voice-selection.json"
        selection_path.write_text(json.dumps(selection), encoding="utf-8")
        self.files["voice-selection.json"] = selection_path
        sidecar_path = self.project / "audio/narration-only.wav.tts.json"
        sidecar = {
            "schema_version": "1.0.0",
            "selection": selection,
            "resolved_voice_id": "CV002",
            "output": "narration-only.wav",
            "output_sha256": gate.sha256_file(self.files["audio/narration-only.wav"]),
        }
        sidecar_path.write_text(json.dumps(sidecar), encoding="utf-8")
        self.files["audio/narration-only.wav.tts.json"] = sidecar_path
        authoring = {
            "schema_version": 1,
            "project_kind": "free_exploration",
            "rationale": "final-video gate synthetic fixture",
            "voice_selection": "voice-selection.json",
            "cover": {"text": "合成测试", "disclosed_item_ids": []},
            "narration_sequence": [
                {
                    "id": "free-line",
                    "role": "free",
                    "text": "你好",
                    "wav": "audio/narration-only.wav",
                    "sidecar": "audio/narration-only.wav.tts.json",
                }
            ],
            "items": [],
        }
        authoring_path = self.project / "project-manifest.json"
        authoring_path.write_text(
            json.dumps(authoring, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        self.files["project-manifest.json"] = authoring_path

    @staticmethod
    def human(final_sha: str, text_field: str, text: str) -> dict:
        return {
            "status": "approved",
            "reviewer_kind": "human",
            "reviewer": "fixture-reviewer",
            "reviewed_at": "2025-01-01T12:00:00+08:00",
            "final_sha256": final_sha,
            text_field: text,
        }

    @staticmethod
    def pending(final_sha: str, text_field: str, *, evidence=None) -> dict:
        row = {
            "status": "pending_human_review",
            "reviewer_kind": None,
            "reviewer": "",
            "reviewed_at": "",
            "final_sha256": final_sha,
            text_field: "",
        }
        if evidence is not None:
            row["evidence"] = evidence
        return row

    def _manifest(self) -> dict:
        final_sha = gate.sha256_file(self.files["renders/final.mp4"])
        expected = "你好"
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
        visual = self.human(final_sha, "notes", "逐章抽帧并由人工查看")
        visual["evidence"] = [
            {
                **self.asset("qa/cover.png"),
                "sample_time_sec": 0.0,
            },
            {
                **self.asset("qa/contact-sheet.png"),
                "sample_time_sec": 0.5,
            }
        ]
        leakage = self.human(final_sha, "notes", "人工检查无网址、路径或提示词泄漏")
        leakage["evidence"] = [self.asset("qa/leakage.txt")]
        release = self.human(final_sha, "notes", "人工检查发布裁剪与安全区")
        release["evidence"] = [self.asset("qa/release.txt")]
        return {
            "schema_version": 1,
            "narration_mode": "free_exploration",
            "authoring_manifest": self.asset("project-manifest.json"),
            "assets": {
                "final": self.asset("renders/final.mp4"),
                "render": self.asset("renders/render.mp4"),
                "master": self.asset("audio/master.wav"),
            },
            "chapters": [
                {
                    "id": "intro",
                    "role": "free",
                    "start_sec": 0.0,
                    "end_sec": 2.0,
                    "requires_narration": True,
                }
            ],
            "checks": {
                "expected_video_codec": "h264",
                "duration_tolerance_sec": 0.5,
            },
            "narration_expectations": [
                {
                    "id": "intro-line",
                    "role": "free",
                    "chapter_id": "intro",
                    "expected_text": expected,
                    "expected_text_sha256": gate.sha256_text(expected),
                    "authoring_narration_id": "free-line",
                    "authoring_wav_sha256": gate.sha256_file(
                        self.files["audio/narration-only.wav"]
                    ),
                    "acceptable_variants": [],
                }
            ],
            "asr_evidence": {
                "final_aac_asr": {
                    "artifact": {"path": "qa/final-aac-asr.json", "sha256": "0" * 64},
                    "sources": [self.asset("renders/final.mp4")],
                    "parameters": final_parameters,
                },
                "isolated_narration_asr": {
                    "artifact": {
                        "path": "qa/isolated-narration-asr.json",
                        "sha256": "0" * 64,
                    },
                    "sources": [self.asset("audio/narration-only.wav")],
                    "parameters": isolated_parameters,
                },
            },
            "reviews": {
                "visual_frames": visual,
                "leakage": leakage,
                "release_safety": release,
                "silence": [],
                "black": [],
            },
        }

    def evidence_payload(self, kind: str) -> dict:
        row = self.manifest["asr_evidence"][kind]
        sources = [
            gate.Asset(
                label=f"fixture {source['path']}",
                raw_path=source["path"],
                path=self.files[source["path"]],
                sha256=source["sha256"],
            )
            for source in row["sources"]
        ]
        receipt = fake_live_receipt(sources, row["parameters"], kind)
        segment_prefix = "final" if kind == "final_aac_asr" else "isolated"
        return {
            "schema_version": 1,
            "kind": kind,
            "final_sha256": self.manifest["assets"]["final"]["sha256"],
            "live_receipt": receipt,
            "assertions": [
                {
                    "expectation_id": "intro-line",
                    "segment_ids": [f"{segment_prefix}-000:000000"],
                    "disposition": "exact",
                }
            ],
        }

    def write_asr_evidence(self) -> None:
        for kind, relative in (
            ("final_aac_asr", "qa/final-aac-asr.json"),
            ("isolated_narration_asr", "qa/isolated-narration-asr.json"),
        ):
            path = self.project / relative
            path.write_text(
                json.dumps(self.evidence_payload(kind), ensure_ascii=False),
                encoding="utf-8",
            )
            self.files[relative] = path
            self.manifest["asr_evidence"][kind]["artifact"]["sha256"] = gate.sha256_file(path)

    def write_manifest(self) -> None:
        path = self.project / "qa/final-video-qa.json"
        path.write_text(
            json.dumps(self.manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        self.files["qa/final-video-qa.json"] = path

    def add_interval_review(self, key: str, interval: gate.Interval) -> None:
        final_sha = self.manifest["assets"]["final"]["sha256"]
        row = self.human(final_sha, "context", f"人工确认 {key} 为章节边界上下文")
        row.update({"start_sec": interval.start, "end_sec": interval.end})
        self.manifest["reviews"][key].append(row)
        self.write_manifest()

    def add_pending_interval(self, key: str, interval: gate.Interval) -> None:
        final_sha = self.manifest["assets"]["final"]["sha256"]
        row = self.pending(final_sha, "context")
        row.update({"start_sec": interval.start, "end_sec": interval.end})
        self.manifest["reviews"][key].append(row)
        self.write_manifest()

    def set_global_reviews_pending(self) -> None:
        final_sha = self.manifest["assets"]["final"]["sha256"]
        visual_evidence = self.manifest["reviews"]["visual_frames"]["evidence"]
        self.manifest["reviews"]["visual_frames"] = self.pending(
            final_sha,
            "notes",
            evidence=visual_evidence,
        )
        for key in ("leakage", "release_safety"):
            self.manifest["reviews"][key] = self.pending(
                final_sha,
                "notes",
                evidence=[],
            )
        self.write_manifest()

    def set_asr_reviews_pending(self) -> None:
        for kind, relative in (
            ("final_aac_asr", "qa/final-aac-asr.json"),
            ("isolated_narration_asr", "qa/isolated-narration-asr.json"),
        ):
            path = self.files[relative]
            evidence = json.loads(path.read_text(encoding="utf-8"))
            for assertion in evidence["assertions"]:
                assertion["disposition"] = "human_review"
                assertion.pop("review", None)
            path.write_text(json.dumps(evidence, ensure_ascii=False), encoding="utf-8")
            self.manifest["asr_evidence"][kind]["artifact"]["sha256"] = gate.sha256_file(path)
        self.write_manifest()

    def set_visual_samples(self, timestamps: list[float]) -> None:
        if not any(abs(timestamp) <= 0.000001 for timestamp in timestamps):
            timestamps = [0.0, *timestamps]
        evidence: list[dict] = []
        for index, timestamp in enumerate(timestamps):
            relative = f"qa/frame-{index}.png"
            path = self.project / relative
            path.write_bytes(f"fixture frame {index}".encode("utf-8"))
            self.files[relative] = path
            evidence.append(
                {**self.asset(relative), "sample_time_sec": timestamp}
            )
        self.manifest["reviews"]["visual_frames"]["evidence"] = evidence
        self.write_manifest()


class FinalVideoGateUnitTests(unittest.TestCase):
    def make_fixture(self, temporary: str) -> ProjectFixture:
        return ProjectFixture(Path(temporary) / "project")

    def test_pending_human_and_asr_records_are_local_advisories(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = self.make_fixture(temporary)
            fixture.set_global_reviews_pending()
            fixture.set_asr_reviews_pending()

            local_tools = FakeMediaTools()
            result = gate.verify_project(fixture.project, tools=local_tools)
            self.assertEqual([False, False], local_tools.authoring_review_modes)
            self.assertEqual(5, len(result.human_review_advisories))
            self.assertIn("reviews.visual_frames", result.human_review_advisories)
            self.assertTrue(
                any("final_aac_asr" in label for label in result.human_review_advisories)
            )

            release_tools = FakeMediaTools()
            with self.assertRaises(gate.HumanReviewRequired) as captured:
                gate.verify_project(
                    fixture.project,
                    tools=release_tools,
                    require_human_review=True,
                )
            self.assertEqual([True, True], release_tools.authoring_review_modes)
            self.assertEqual(result.human_review_advisories, captured.exception.labels)

    def test_heavy_ffmpeg_commands_have_explicit_thread_budget_and_fast_seek(self) -> None:
        tools = gate.MediaTools.__new__(gate.MediaTools)
        commands: list[list[str]] = []

        def fake_run(command: list[str], _label: str):
            commands.append(command)
            if "framemd5" in command:
                return subprocess.CompletedProcess(
                    command,
                    0,
                    stdout=(
                        "#format: frame checksums\n"
                        "#tb 0: 1/24\n"
                        "0, 0, 300, 1, 3, " + "a" * 64 + "\n"
                    ),
                    stderr="",
                )
            if "loudnorm=I=-14:LRA=11:TP=-1:print_format=json" in command:
                return subprocess.CompletedProcess(
                    command,
                    0,
                    stdout="",
                    stderr='{"input_i":"-14.0","input_tp":"-1.0"}',
                )
            if any("asdr" in token for token in command):
                return subprocess.CompletedProcess(
                    command, 0, stdout="", stderr="SDR ch0: 30.0 dB"
                )
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        tools._run = fake_run  # type: ignore[method-assign]
        with mock.patch.dict(
            os.environ,
            {gate.resource_budget.FFMPEG_THREADS_ENV: "2"},
        ):
            tools.analyze_final(Path("final.mp4"), 2.0)
            tools.video_decode_receipt(Path("final.mp4"))
            receipt = tools.frame_rgb_receipt(Path("final.mp4"), 12.5)
            tools.loudness(Path("final.mp4"))
            tools.audio_sdr(Path("master.wav"), Path("final.mp4"), 2.0)

        self.assertAlmostEqual(12.5, receipt.pts_sec)
        for command in commands:
            self.assertIn("-threads", command)
            self.assertEqual("2", command[command.index("-threads") + 1])
            self.assertIn("-filter_threads", command)
            self.assertEqual("2", command[command.index("-filter_threads") + 1])
        frame_command = next(
            command for command in commands if "-ss" in command and "framemd5" in command
        )
        self.assertLess(frame_command.index("-ss"), frame_command.index("-i"))
        self.assertIn("-copyts", frame_command)
        for command in (commands[0], commands[-1]):
            self.assertIn("-filter_complex_threads", command)
            self.assertEqual(
                "2", command[command.index("-filter_complex_threads") + 1]
            )
        self.assertEqual(2, commands[-1].count("-threads"))

    def test_human_approved_authoring_and_final_pass_both_modes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = self.make_fixture(temporary)
            local_tools = FakeMediaTools()
            gate.verify_project(fixture.project, tools=local_tools)
            self.assertEqual([False, False], local_tools.authoring_review_modes)

            release_tools = FakeMediaTools()
            result = gate.verify_project(
                fixture.project,
                tools=release_tools,
                require_human_review=True,
            )
            self.assertEqual([True, True], release_tools.authoring_review_modes)
            self.assertEqual((), result.human_review_advisories)

    def test_pending_reviews_cannot_impersonate_a_human_or_skip_frame_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = self.make_fixture(temporary)
            fixture.set_global_reviews_pending()
            fixture.manifest["reviews"]["visual_frames"]["reviewer_kind"] = "human"
            fixture.write_manifest()
            with self.assertRaisesRegex(gate.GateFailure, "must be null"):
                gate.verify_project(fixture.project, tools=FakeMediaTools())

            fixture = ProjectFixture(Path(temporary) / "agent-approved")
            fixture.manifest["reviews"]["visual_frames"]["reviewer_kind"] = "agent"
            fixture.write_manifest()
            with self.assertRaisesRegex(gate.GateFailure, "machine approval is not accepted"):
                gate.verify_project(fixture.project, tools=FakeMediaTools())

            fixture = ProjectFixture(Path(temporary) / "stale-pending-frame")
            fixture.set_global_reviews_pending()
            fixture.manifest["reviews"]["visual_frames"]["evidence"][0]["sha256"] = "0" * 64
            fixture.write_manifest()
            with self.assertRaisesRegex(gate.GateFailure, "SHA-256 mismatch"):
                gate.verify_project(fixture.project, tools=FakeMediaTools())

    def test_pending_soft_intervals_are_advisory_but_hard_silence_still_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = self.make_fixture(temporary)
            silence = gate.Interval(0.2, 1.4)
            black = gate.Interval(1.1, 1.8)
            fixture.add_pending_interval("silence", silence)
            fixture.add_pending_interval("black", black)
            tools = FakeMediaTools()
            tools.silences = [silence]
            tools.black = [black]

            result = gate.verify_project(fixture.project, tools=tools)
            self.assertEqual(0, result.reviewed_silences)
            self.assertEqual(0, result.reviewed_black_intervals)
            self.assertIn("reviews.silence[0]", result.human_review_advisories)
            self.assertIn("reviews.black[0]", result.human_review_advisories)
            with self.assertRaises(gate.HumanReviewRequired):
                gate.verify_project(
                    fixture.project,
                    tools=tools,
                    require_human_review=True,
                )

            tools.silences = [gate.Interval(0.1, 1.7)]
            with self.assertRaisesRegex(gate.GateFailure, "hard silence"):
                gate.verify_project(fixture.project, tools=tools)

    def test_cli_distinguishes_local_pass_from_required_human_review(self) -> None:
        summary = gate.VerificationSummary(
            final_path="renders/video.mp4",
            final_sha256="f" * 64,
            duration_sec=12.0,
            video_codec="h264",
            integrated_lufs=-14.0,
            true_peak_dbtp=-1.0,
            master_aac_sdr_db=30.0,
            reviewed_silences=0,
            reviewed_black_intervals=0,
            human_review_advisories=("reviews.visual_frames",),
        )
        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            mock.patch.object(gate, "verify_project", return_value=summary) as verifier,
            mock.patch("sys.stdout", stdout),
            mock.patch("sys.stderr", stderr),
        ):
            self.assertEqual(0, gate.main(["--project", "project"]))
        verifier.assert_called_once_with(
            Path("project"),
            "qa/final-video-qa.json",
            require_human_review=False,
        )
        self.assertIn("FINAL VIDEO QA: PASS", stdout.getvalue())
        self.assertIn("advisories=1", stdout.getvalue())
        self.assertNotIn("human_review=", stdout.getvalue())
        self.assertNotIn("HUMAN REVIEW", stdout.getvalue())
        self.assertNotIn("--require-human-review", stdout.getvalue())
        self.assertNotIn("local delivery", stdout.getvalue())
        self.assertNotIn("授权", stdout.getvalue())
        self.assertNotIn("版权", stdout.getvalue())
        self.assertEqual("", stderr.getvalue())

        stdout = io.StringIO()
        stderr = io.StringIO()
        pending = gate.HumanReviewRequired(("reviews.visual_frames",))
        with (
            mock.patch.object(gate, "verify_project", side_effect=pending) as verifier,
            mock.patch("sys.stdout", stdout),
            mock.patch("sys.stderr", stderr),
        ):
            self.assertEqual(
                2,
                gate.main(["--project", "project", "--require-human-review"]),
            )
        verifier.assert_called_once_with(
            Path("project"),
            "qa/final-video-qa.json",
            require_human_review=True,
        )
        self.assertEqual("", stdout.getvalue())
        self.assertIn("FINAL VIDEO QA: REVIEW_REQUIRED", stderr.getvalue())

    def test_offline_asr_toolchain_identity_is_pinned_without_reading_real_model(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            checkpoint = Path(temporary) / "small.pt"
            checkpoint.write_bytes(b"synthetic checkpoint")
            identity = offline_asr.verify_toolchain_identity(
                checkpoint,
                hash_reader=lambda _: offline_asr.CHECKPOINT_SHA256,
                version_reader=lambda name: (
                    offline_asr.WHISPER_VERSION
                    if name == offline_asr.WHISPER_DISTRIBUTION
                    else "unexpected"
                ),
            )
            self.assertEqual(
                {
                    "checkpoint_sha256": gate.PINNED_WHISPER_CHECKPOINT_SHA256,
                    "openai_whisper_version": gate.PINNED_OPENAI_WHISPER_VERSION,
                },
                identity,
            )
            with self.assertRaisesRegex(ValueError, "checkpoint SHA-256 mismatch"):
                offline_asr.verify_toolchain_identity(
                    checkpoint,
                    hash_reader=lambda _: "0" * 64,
                    version_reader=lambda _: offline_asr.WHISPER_VERSION,
                )
            with self.assertRaisesRegex(ValueError, "version mismatch"):
                offline_asr.verify_toolchain_identity(
                    checkpoint,
                    hash_reader=lambda _: offline_asr.CHECKPOINT_SHA256,
                    version_reader=lambda _: "old-version",
                )

    def test_offline_asr_verifies_identity_before_loading_synthetic_model(self) -> None:
        class SyntheticModel:
            def transcribe(self, *_args, **_kwargs):
                return {
                    "text": "你好",
                    "segments": [{"start": 0.1, "end": 0.4, "text": "你好"}],
                }

        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source.wav"
            checkpoint = Path(temporary) / "small.pt"
            source.write_bytes(b"synthetic audio")
            checkpoint.write_bytes(b"synthetic checkpoint")
            events: list[str] = []

            def identity_loader(_path: Path) -> dict[str, str]:
                events.append("identity")
                return {
                    "checkpoint_sha256": offline_asr.CHECKPOINT_SHA256,
                    "openai_whisper_version": offline_asr.WHISPER_VERSION,
                }

            def model_loader(_path: Path) -> SyntheticModel:
                events.append("model")
                return SyntheticModel()

            result = offline_asr.run(
                {
                    "model": "small",
                    "language": "zh",
                    "jobs": [{"id": "synthetic", "path": str(source)}],
                },
                checkpoint=checkpoint,
                identity_loader=identity_loader,
                model_loader=model_loader,
            )
            self.assertEqual(["identity", "model"], events)
            self.assertEqual(offline_asr.CHECKPOINT_SHA256, result["checkpoint_sha256"])
            self.assertEqual(offline_asr.WHISPER_VERSION, result["openai_whisper_version"])

    def test_offline_asr_drops_segments_that_cannot_be_evidence(self) -> None:
        class SyntheticModel:
            def transcribe(self, *_args, **_kwargs):
                return {
                    "text": "有效片段",
                    "segments": [
                        {"start": 0.1, "end": 0.4, "text": "有效"},
                        {"start": 0.4, "end": 0.4, "text": ""},
                        {"start": 0.4, "end": 0.4, "text": "重复长音"},
                        {"start": 0.4, "end": 0.8, "text": "   "},
                        {"start": 0.8, "end": 1.2, "text": "片段"},
                    ],
                }

        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source.wav"
            checkpoint = Path(temporary) / "small.pt"
            source.write_bytes(b"synthetic audio")
            checkpoint.write_bytes(b"synthetic checkpoint")
            result = offline_asr.run(
                {
                    "model": "small",
                    "language": "zh",
                    "jobs": [{"id": "synthetic", "path": str(source)}],
                },
                checkpoint=checkpoint,
                identity_loader=lambda _: {
                    "checkpoint_sha256": offline_asr.CHECKPOINT_SHA256,
                    "openai_whisper_version": offline_asr.WHISPER_VERSION,
                },
                model_loader=lambda _: SyntheticModel(),
            )
            self.assertEqual(
                ["synthetic:000000", "synthetic:000004"],
                [row["id"] for row in result["results"][0]["segments"]],
            )

    def test_offline_asr_uses_fixed_windows_for_long_media(self) -> None:
        class SyntheticModel:
            def transcribe(self, *_args, **_kwargs):
                raise AssertionError("long media must use the fixed-window path")

        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "long.mp4"
            checkpoint = Path(temporary) / "small.pt"
            source.write_bytes(b"synthetic long media")
            checkpoint.write_bytes(b"synthetic checkpoint")
            model = SyntheticModel()
            with (
                mock.patch.object(offline_asr, "_media_duration", return_value=120.0),
                mock.patch.object(
                    offline_asr,
                    "_transcribe_long_source",
                    return_value={
                        "text": "长片旁白",
                        "segments": [
                            {"start": 25.1, "end": 26.0, "text": "长片旁白"}
                        ],
                    },
                ) as transcribe_long,
            ):
                result = offline_asr.run(
                    {
                        "model": "small",
                        "language": "zh",
                        "jobs": [{"id": "long", "path": str(source)}],
                    },
                    checkpoint=checkpoint,
                    identity_loader=lambda _: {
                        "checkpoint_sha256": offline_asr.CHECKPOINT_SHA256,
                        "openai_whisper_version": offline_asr.WHISPER_VERSION,
                    },
                    model_loader=lambda _: model,
                )
            transcribe_long.assert_called_once_with(model, source, "zh")
            self.assertEqual("long:000000", result["results"][0]["segments"][0]["id"])

    def test_live_asr_receipt_rejects_replaced_checkpoint_or_distribution(self) -> None:
        receipt = fake_live_receipt([], {"language": "zh"}, "isolated_narration_asr")
        for field, replacement in (
            ("checkpoint_sha256", "0" * 64),
            ("openai_whisper_version", "old-version"),
        ):
            with self.subTest(field=field):
                changed = {**receipt, field: replacement}
                with self.assertRaisesRegex(gate.GateFailure, "pinned offline ASR toolchain"):
                    gate.validate_live_asr_identity(changed, "asr_evidence.synthetic")

    def test_valid_current_manifest_passes_without_claiming_visual_understanding(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = self.make_fixture(temporary)
            result = gate.verify_project(fixture.project, tools=FakeMediaTools())
            self.assertEqual("h264", result.video_codec)
            self.assertEqual(
                gate.sha256_file(fixture.files["renders/final.mp4"]),
                result.final_sha256,
            )

    def test_final_and_render_must_start_with_lowercase_renders(self) -> None:
        for asset_key in ("final", "render"):
            for invalid in (
                f"{asset_key}.mp4",
                f"final/{asset_key}.mp4",
                f"output/{asset_key}.mp4",
                f"Renders/{asset_key}.mp4",
            ):
                with (
                    self.subTest(asset=asset_key, invalid=invalid),
                    tempfile.TemporaryDirectory() as temporary,
                ):
                    fixture = self.make_fixture(temporary)
                    source = fixture.files[f"renders/{asset_key}.mp4"]
                    invalid_path = fixture.project / invalid
                    invalid_path.parent.mkdir(parents=True, exist_ok=True)
                    invalid_path.write_bytes(source.read_bytes())
                    fixture.files[invalid] = invalid_path
                    fixture.manifest["assets"][asset_key] = fixture.asset(invalid)
                    fixture.write_manifest()

                    with self.assertRaisesRegex(
                        gate.GateFailure,
                        rf"assets\.{asset_key}\.path first path component must be "
                        r"lowercase 'renders'",
                    ):
                        gate.verify_project(fixture.project, tools=FakeMediaTools())

    def test_current_final_sha_is_mandatory_before_media_tools_run(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = self.make_fixture(temporary)
            fixture.files["renders/final.mp4"].write_bytes(b"changed after QA")
            with self.assertRaisesRegex(gate.GateFailure, "manifest is stale"):
                gate.verify_project(fixture.project, tools=FakeMediaTools())

    def test_manifest_rejects_duplicate_keys_and_nonstandard_numbers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = self.make_fixture(temporary)
            manifest_path = fixture.files["qa/final-video-qa.json"]
            raw = manifest_path.read_text(encoding="utf-8")
            manifest_path.write_text(
                raw.replace(
                    '"schema_version": 1,',
                    '"schema_version": 1,\n  "schema_version": 1,',
                    1,
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(gate.GateFailure, "duplicate object key"):
                gate.verify_project(fixture.project, tools=FakeMediaTools())

            fixture = ProjectFixture(Path(temporary) / "second-project")
            manifest_path = fixture.files["qa/final-video-qa.json"]
            raw = manifest_path.read_text(encoding="utf-8")
            manifest_path.write_text(
                raw.replace('"duration_tolerance_sec": 0.5', '"duration_tolerance_sec": NaN'),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(gate.GateFailure, "non-standard numeric constant"):
                gate.verify_project(fixture.project, tools=FakeMediaTools())

    def test_offline_asr_subprocess_timeout_is_a_clean_gate_failure(self) -> None:
        with mock.patch(
            "tools.video.verify_final_video.subprocess.run",
            side_effect=subprocess.TimeoutExpired(["offline-asr"], 600),
        ):
            with self.assertRaisesRegex(gate.GateFailure, "timed out after 600s"):
                gate.run_offline_asr_process(["offline-asr"], "{}", 600)

    def test_project_file_symlink_is_rejected_even_when_content_hash_matches(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = self.make_fixture(temporary)
            final_path = fixture.files["renders/final.mp4"]
            outside = Path(temporary) / "outside.mp4"
            outside.write_bytes(final_path.read_bytes())
            final_path.unlink()
            final_path.symlink_to(outside)
            with self.assertRaisesRegex(gate.GateFailure, "must not be a symlink"):
                gate.verify_project(fixture.project, tools=FakeMediaTools())

    def test_codec_is_manifest_selected_not_generic_hevc_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = self.make_fixture(temporary)
            fixture.manifest["checks"]["expected_video_codec"] = "hevc"
            fixture.write_manifest()
            with self.assertRaisesRegex(gate.GateFailure, "manifest-selected hevc"):
                gate.verify_project(fixture.project, tools=FakeMediaTools())

    def test_final_render_and_master_reject_any_extra_stream(self) -> None:
        class ExtraStreamTools(FakeMediaTools):
            def __init__(self, target: str) -> None:
                super().__init__()
                self.target = target

            def probe(self, path: Path) -> dict:
                result = super().probe(path)
                if path.name == self.target:
                    result["streams"].append(
                        {"codec_type": "subtitle", "codec_name": "mov_text"}
                    )
                return result

        with tempfile.TemporaryDirectory() as temporary:
            fixture = self.make_fixture(temporary)
            cases = (
                ("final.mp4", "exactly one video stream and one audio stream"),
                ("render.mp4", "exactly one video stream and no other streams"),
                ("master.wav", "exactly one audio stream and no other streams"),
            )
            for target, message in cases:
                with self.subTest(target=target):
                    with self.assertRaisesRegex(gate.GateFailure, message):
                        gate.verify_project(
                            fixture.project,
                            tools=ExtraStreamTools(target),
                        )

    def test_stream_start_time_must_be_explicit(self) -> None:
        class MissingStartTools(FakeMediaTools):
            def probe(self, path: Path) -> dict:
                result = super().probe(path)
                if path.name == "final.mp4":
                    video = next(
                        row
                        for row in result["streams"]
                        if row["codec_type"] == "video"
                    )
                    video.pop("start_time")
                return result

        with tempfile.TemporaryDirectory() as temporary:
            fixture = self.make_fixture(temporary)
            with self.assertRaisesRegex(gate.GateFailure, "no finite start_time"):
                gate.verify_project(fixture.project, tools=MissingStartTools())

    def test_small_chapter_gaps_cannot_accumulate_past_frame_epsilon(self) -> None:
        chapters = [
            gate.Chapter("a", "free", 0.0, 0.60, False),
            gate.Chapter("b", "free", 0.63, 1.30, False),
            gate.Chapter("c", "free", 1.33, 2.0, False),
        ]
        with self.assertRaisesRegex(gate.GateFailure, "cumulatively"):
            gate.validate_chapter_coverage(chapters, 2.0)

    def test_decoded_render_frames_and_master_audio_must_match_final(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = self.make_fixture(temporary)
            tools = FakeMediaTools()
            tools.frame_hashes = {"final.mp4": "a" * 64, "render.mp4": "b" * 64}
            with self.assertRaisesRegex(gate.GateFailure, "frame hashes do not match"):
                gate.verify_project(fixture.project, tools=tools)

            tools.frame_hashes = {}
            tools.audio_sdr_db = 5.0
            with self.assertRaisesRegex(gate.GateFailure, "does not match master"):
                gate.verify_project(fixture.project, tools=tools)

    def test_same_chapter_silence_over_1_5_seconds_is_hard_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = self.make_fixture(temporary)
            tools = FakeMediaTools()
            tools.silences = [gate.Interval(0.1, 1.7)]
            with self.assertRaisesRegex(gate.GateFailure, "hard silence inside chapter"):
                gate.verify_project(fixture.project, tools=tools)

    def test_boundary_silence_and_black_require_current_human_context(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = self.make_fixture(temporary)
            fixture.manifest["chapters"] = [
                {
                    "id": "intro",
                    "role": "free",
                    "start_sec": 0.0,
                    "end_sec": 1.0,
                    "requires_narration": True,
                },
                {
                    "id": "body",
                    "role": "song",
                    "start_sec": 1.0,
                    "end_sec": 2.0,
                    "requires_narration": False,
                },
            ]
            fixture.set_visual_samples([0.5, 1.5])
            tools = FakeMediaTools()
            silence = gate.Interval(0.8, 2.0)
            black = gate.Interval(0.9, 1.6)
            tools.silences = [silence]
            tools.black = [black]
            with self.assertRaisesRegex(gate.GateFailure, "silence REVIEW"):
                gate.verify_project(fixture.project, tools=tools)
            fixture.add_interval_review("silence", silence)
            with self.assertRaisesRegex(gate.GateFailure, "blackdetect REVIEW"):
                gate.verify_project(fixture.project, tools=tools)
            fixture.add_interval_review("black", black)
            result = gate.verify_project(fixture.project, tools=tools)
            self.assertEqual(1, result.reviewed_silences)
            self.assertEqual(1, result.reviewed_black_intervals)

    def test_silence_over_1_5_seconds_cannot_be_downgraded_by_a_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = self.make_fixture(temporary)
            fixture.manifest["chapters"] = [
                {
                    "id": "intro",
                    "role": "free",
                    "start_sec": 0.0,
                    "end_sec": 1.0,
                    "requires_narration": True,
                },
                {
                    "id": "body",
                    "role": "song",
                    "start_sec": 1.0,
                    "end_sec": 2.0,
                    "requires_narration": False,
                },
            ]
            fixture.set_visual_samples([0.5, 1.5])
            tools = FakeMediaTools()
            tools.silences = [gate.Interval(0.1, 1.9)]
            with self.assertRaisesRegex(gate.GateFailure, "hard silence crosses"):
                gate.verify_project(fixture.project, tools=tools)

    def test_visual_samples_must_be_strictly_inside_one_chapter(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = self.make_fixture(temporary)
            fixture.manifest["chapters"] = [
                {
                    "id": "intro",
                    "role": "free",
                    "start_sec": 0.0,
                    "end_sec": 1.0,
                    "requires_narration": True,
                },
                {
                    "id": "body",
                    "role": "song",
                    "start_sec": 1.0,
                    "end_sec": 2.0,
                    "requires_narration": False,
                },
            ]
            fixture.set_visual_samples([0.5, 1.0])
            with self.assertRaisesRegex(gate.GateFailure, "strictly inside exactly one"):
                gate.verify_project(fixture.project, tools=FakeMediaTools())

            fixture.set_visual_samples([0.5, 1.5])
            gate.verify_project(fixture.project, tools=FakeMediaTools())

    def test_visual_evidence_requires_cover_frame_zero(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = self.make_fixture(temporary)
            fixture.manifest["reviews"]["visual_frames"]["evidence"] = [
                fixture.manifest["reviews"]["visual_frames"]["evidence"][1]
            ]
            fixture.write_manifest()
            with self.assertRaisesRegex(gate.GateFailure, "frame 0"):
                gate.verify_project(fixture.project, tools=FakeMediaTools())

    def test_visual_evidence_pixels_must_match_current_final_frame(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = self.make_fixture(temporary)
            tools = FakeMediaTools()
            tools.visual_frame_hashes[("contact-sheet.png", None)] = "d" * 64
            with self.assertRaisesRegex(gate.GateFailure, "pixels do not match"):
                gate.verify_project(fixture.project, tools=tools)

    def test_ai_content_and_source_silence_escape_hatches_are_not_in_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = self.make_fixture(temporary)
            fixture.manifest["content_kind"] = "ai_voice_clone"
            fixture.write_manifest()
            with self.assertRaisesRegex(gate.GateFailure, "unsupported top-level"):
                gate.verify_project(fixture.project, tools=FakeMediaTools())

    def test_loudness_defaults_are_enforced_and_manifest_can_only_narrow(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = self.make_fixture(temporary)
            tools = FakeMediaTools()
            tools.true_peak_dbtp = 0.0
            with self.assertRaisesRegex(gate.GateFailure, "true peak"):
                gate.verify_project(fixture.project, tools=tools)
            fixture.manifest["checks"]["loudness"] = {"integrated_lufs_min": -21.0}
            fixture.write_manifest()
            with self.assertRaisesRegex(gate.GateFailure, "must not be below -20"):
                gate.verify_project(fixture.project, tools=FakeMediaTools())

    def test_asr_parameters_and_every_expected_assertion_are_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = self.make_fixture(temporary)
            fixture.manifest["asr_evidence"]["final_aac_asr"]["parameters"]["model"] = "large"
            fixture.write_manifest()
            with self.assertRaisesRegex(gate.GateFailure, "fixed offline ASR contract"):
                gate.verify_project(fixture.project, tools=FakeMediaTools())

            fixture = ProjectFixture(Path(temporary) / "second-project")
            evidence_path = fixture.files["qa/final-aac-asr.json"]
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            evidence["assertions"] = []
            evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
            fixture.manifest["asr_evidence"]["final_aac_asr"]["artifact"][
                "sha256"
            ] = gate.sha256_file(evidence_path)
            fixture.write_manifest()
            with self.assertRaisesRegex(gate.GateFailure, "assertions mismatch"):
                gate.verify_project(fixture.project, tools=FakeMediaTools())

    def test_stored_asr_receipt_must_equal_a_current_offline_run(self) -> None:
        class ChangedAsrTools(FakeMediaTools):
            def transcribe(self, sources, parameters, kind):
                receipt = super().transcribe(sources, parameters, kind)
                receipt["results"][0]["transcript"] = "不是旧记录"
                receipt["results"][0]["segments"][0]["text"] = "不是旧记录"
                return receipt

        with tempfile.TemporaryDirectory() as temporary:
            fixture = self.make_fixture(temporary)
            with self.assertRaisesRegex(gate.GateFailure, "current offline ASR run"):
                gate.verify_project(fixture.project, tools=ChangedAsrTools())

    def test_empty_normalized_live_text_cannot_pass_exact_or_human_review(self) -> None:
        author_wav = gate.Asset("wav", "audio/line.wav", Path("line.wav"), "a" * 64)
        expectation = {
            "line": {
                "expected_text": "你好",
                "expected_text_sha256": gate.sha256_text("你好"),
                "acceptable_variants": [],
                "chapter_start_sec": 0.0,
                "chapter_end_sec": 1.0,
                "authoring_wav": author_wav,
            }
        }
        receipt = {
            "sources": [
                {"id": "final-000", "path": "renders/final.mp4", "sha256": "f" * 64}
            ],
            "results": [
                {
                    "source_id": "final-000",
                    "transcript": "。",
                    "segments": [
                        {
                            "id": "final-000:000000",
                            "start_sec": 0.2,
                            "end_sec": 0.8,
                            "text": "。",
                        }
                    ],
                }
            ],
        }
        evidence = {
            "assertions": [
                {
                    "expectation_id": "line",
                    "segment_ids": ["final-000:000000"],
                    "disposition": "exact",
                }
            ]
        }
        with self.assertRaisesRegex(gate.GateFailure, "becomes empty"):
            gate.validate_asr_assertions(
                evidence,
                receipt,
                expectation,
                "f" * 64,
                "asr",
                kind="final_aac_asr",
            )

    def test_expectation_must_bind_current_authoring_text_and_wav_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = self.make_fixture(temporary)
            row = fixture.manifest["narration_expectations"][0]
            row["expected_text"] = "被 QA 自行改写"
            row["expected_text_sha256"] = gate.sha256_text(row["expected_text"])
            fixture.write_manifest()
            with self.assertRaisesRegex(gate.GateFailure, "authoring narration"):
                gate.verify_project(fixture.project, tools=FakeMediaTools())

    def test_aac_bitrate_and_master_format_must_match(self) -> None:
        class BadAudioTools(FakeMediaTools):
            def __init__(self, bitrate: str, channels: int) -> None:
                super().__init__()
                self.bitrate = bitrate
                self.channels = channels

            def probe(self, path: Path) -> dict:
                result = super().probe(path)
                if path.name == "final.mp4":
                    audio = next(row for row in result["streams"] if row["codec_type"] == "audio")
                    audio["bit_rate"] = self.bitrate
                    audio["channels"] = self.channels
                return result

        with tempfile.TemporaryDirectory() as temporary:
            fixture = self.make_fixture(temporary)
            with self.assertRaisesRegex(gate.GateFailure, "at least 160 kbps"):
                gate.verify_project(fixture.project, tools=BadAudioTools("128000", 2))
            with self.assertRaisesRegex(gate.GateFailure, "must match the PCM master"):
                gate.verify_project(fixture.project, tools=BadAudioTools("192000", 1))

    def test_visual_path_pts_and_actual_extracted_pts_are_unique_and_bound(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = self.make_fixture(temporary)
            evidence = fixture.manifest["reviews"]["visual_frames"]["evidence"]
            evidence[1]["path"] = evidence[0]["path"]
            evidence[1]["sha256"] = evidence[0]["sha256"]
            fixture.write_manifest()
            with self.assertRaisesRegex(gate.GateFailure, "paths must be unique"):
                gate.verify_project(fixture.project, tools=FakeMediaTools())

            fixture = ProjectFixture(Path(temporary) / "second-project")

            class WrongPtsTools(FakeMediaTools):
                def frame_rgb_receipt(self, path, timestamp_sec=None):
                    receipt = super().frame_rgb_receipt(path, timestamp_sec)
                    if path.name == "final.mp4" and timestamp_sec == 0.5:
                        return gate.FrameReceipt(0.8, receipt.duration_sec, receipt.rgb_sha256)
                    return receipt

            with self.assertRaisesRegex(gate.GateFailure, "returned PTS"):
                gate.verify_project(fixture.project, tools=WrongPtsTools())

    def test_future_human_review_and_runtime_evidence_mutation_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = self.make_fixture(temporary)
            fixture.manifest["reviews"]["visual_frames"]["reviewed_at"] = (
                "2999-01-01T00:00:00+00:00"
            )
            fixture.write_manifest()
            with self.assertRaisesRegex(gate.GateFailure, "must not be in the future"):
                gate.verify_project(fixture.project, tools=FakeMediaTools())

            fixture = ProjectFixture(Path(temporary) / "second-project")

            class MutatingEvidenceTools(FakeMediaTools):
                def loudness(self, path: Path) -> gate.Loudness:
                    fixture.files["qa/leakage.txt"].write_text("changed", encoding="utf-8")
                    return super().loudness(path)

            with self.assertRaisesRegex(gate.GateFailure, "changed while"):
                gate.verify_project(fixture.project, tools=MutatingEvidenceTools())

    def test_both_asr_artifacts_bind_current_final_and_expected_text_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = self.make_fixture(temporary)
            evidence_path = fixture.files["qa/isolated-narration-asr.json"]
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            evidence["final_sha256"] = "a" * 64
            evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
            fixture.manifest["asr_evidence"]["isolated_narration_asr"]["artifact"][
                "sha256"
            ] = gate.sha256_file(evidence_path)
            fixture.write_manifest()
            with self.assertRaisesRegex(gate.GateFailure, "artifact is stale"):
                gate.verify_project(fixture.project, tools=FakeMediaTools())

            fixture = ProjectFixture(Path(temporary) / "third-project")
            evidence_path = fixture.files["qa/final-aac-asr.json"]
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            evidence["assertions"][0]["observed_text"] = "错误文案"
            evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
            fixture.manifest["asr_evidence"]["final_aac_asr"]["artifact"][
                "sha256"
            ] = gate.sha256_file(evidence_path)
            fixture.write_manifest()
            with self.assertRaisesRegex(gate.GateFailure, "untrusted derived fields"):
                gate.verify_project(fixture.project, tools=FakeMediaTools())

    def test_final_aac_assertions_cannot_reuse_one_global_short_word_window(self) -> None:
        expected_text = "你好"
        expected_hash = gate.sha256_text(expected_text)
        author_wav = gate.Asset("author wav", "audio/line.wav", Path("line.wav"), "a" * 64)
        expectations = {
            "intro-line": {
                "expected_text": expected_text,
                "expected_text_sha256": expected_hash,
                "acceptable_variants": [],
                "chapter_start_sec": 0.0,
                "chapter_end_sec": 1.0,
                "authoring_wav": author_wav,
            },
            "cta-line": {
                "expected_text": expected_text,
                "expected_text_sha256": expected_hash,
                "acceptable_variants": [],
                "chapter_start_sec": 0.0,
                "chapter_end_sec": 1.0,
                "authoring_wav": author_wav,
            },
        }
        receipt = {
            "sources": [
                {"id": "final-000", "path": "renders/final.mp4", "sha256": "f" * 64}
            ],
            "results": [
                {
                    "source_id": "final-000",
                    "transcript": expected_text,
                    "segments": [
                        {
                            "id": "final-000:000000",
                            "start_sec": 0.2,
                            "end_sec": 0.8,
                            "text": expected_text,
                        }
                    ],
                }
            ],
        }
        evidence = {
            "assertions": [
                {
                    "expectation_id": "intro-line",
                    "segment_ids": ["final-000:000000"],
                    "disposition": "exact",
                },
                {
                    "expectation_id": "cta-line",
                    "segment_ids": ["final-000:000000"],
                    "disposition": "exact",
                },
            ],
        }
        with self.assertRaisesRegex(gate.GateFailure, "consumed by only one"):
            gate.validate_asr_assertions(
                evidence,
                receipt,
                expectations,
                "f" * 64,
                "asr",
                kind="final_aac_asr",
            )

    def test_asr_segment_ids_cannot_be_reordered_to_forge_expected_text(self) -> None:
        expected = "世界你好"
        author_wav = gate.Asset("wav", "audio/line.wav", Path("line.wav"), "a" * 64)
        expectations = {
            "line": {
                "expected_text": expected,
                "expected_text_sha256": gate.sha256_text(expected),
                "acceptable_variants": [],
                "chapter_start_sec": 0.0,
                "chapter_end_sec": 1.0,
                "authoring_wav": author_wav,
            }
        }
        receipt = {
            "sources": [
                {"id": "final-000", "path": "renders/final.mp4", "sha256": "f" * 64}
            ],
            "results": [
                {
                    "source_id": "final-000",
                    "transcript": "你好世界",
                    "segments": [
                        {"id": "s1", "start_sec": 0.1, "end_sec": 0.3, "text": "你好"},
                        {"id": "s2", "start_sec": 0.4, "end_sec": 0.6, "text": "世界"},
                    ],
                }
            ],
        }
        evidence = {
            "assertions": [
                {
                    "expectation_id": "line",
                    "segment_ids": ["s2", "s1"],
                    "disposition": "exact",
                }
            ]
        }
        with self.assertRaisesRegex(gate.GateFailure, "chronological order"):
            gate.validate_asr_assertions(
                evidence,
                receipt,
                expectations,
                "f" * 64,
                "asr",
                kind="final_aac_asr",
            )

    def test_assets_are_rehashed_after_all_media_checks(self) -> None:
        class MutatingTools(FakeMediaTools):
            def __init__(self, final_path: Path) -> None:
                super().__init__()
                self.final_path = final_path

            def loudness(self, path: Path) -> gate.Loudness:
                self.final_path.write_bytes(b"changed during verification")
                return super().loudness(path)

        with tempfile.TemporaryDirectory() as temporary:
            fixture = self.make_fixture(temporary)
            with self.assertRaisesRegex(gate.GateFailure, "changed while"):
                gate.verify_project(
                    fixture.project,
                    tools=MutatingTools(fixture.files["renders/final.mp4"]),
                )

    def test_structured_mode_cannot_omit_outro_or_cta_expectations(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = self.make_fixture(temporary)
            fixture.manifest["narration_mode"] = "structured"
            fixture.write_manifest()
            with self.assertRaisesRegex(gate.GateFailure, "requires a top_ranking or narrative"):
                gate.verify_project(fixture.project, tools=FakeMediaTools())


@unittest.skipUnless(
    shutil.which("ffmpeg") and shutil.which("ffprobe"),
    "ffmpeg/ffprobe are required for the synthetic integration fixture",
)
class FinalVideoGateFfmpegIntegrationTest(unittest.TestCase):
    def test_fast_seek_receipt_matches_prefix_decode_for_dynamic_video(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "dynamic.mp4"
            subprocess.run(
                [
                    "ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                    "testsrc2=size=160x90:rate=24:duration=3", "-an", "-c:v",
                    "libx264", "-g", "48", "-pix_fmt", "yuv420p", str(source),
                ],
                check=True,
            )
            tools = gate.MediaTools()
            fast = tools.frame_rgb_receipt(source, 1.5)
            baseline = subprocess.run(
                [
                    "ffmpeg", "-hide_banner", "-nostats", "-v", "error", "-xerror",
                    "-threads", "2", "-filter_threads", "2", "-i", str(source),
                    "-vf", "select=gte(t\\,1.500000),format=rgb24", "-map", "0:v:0",
                    "-frames:v", "1", "-fps_mode", "passthrough", "-f", "framemd5",
                    "-hash", "sha256", "-",
                ],
                check=True,
                text=True,
                capture_output=True,
            )
            baseline_receipt = gate.parse_framemd5(
                baseline.stdout, "prefix-decode baseline"
            )[0]
            self.assertAlmostEqual(baseline_receipt[0], fast.pts_sec, places=6)
            self.assertEqual(baseline_receipt[2], fast.rgb_sha256)

    def test_synthetic_h264_aac_mux_passes_full_decode_and_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            project.mkdir()
            render = project / "renders/render.mp4"
            master = project / "audio/master.wav"
            final = project / "renders/final.mp4"
            narration = project / "audio/narration-only.wav"
            for path in (render, master, final):
                path.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                [
                    "ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                    "color=c=blue:s=320x240:r=24:d=2", "-an", "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", str(render),
                ],
                check=True,
            )
            subprocess.run(
                [
                    "ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                    "sine=frequency=440:duration=2,volume=2", "-ac", "2", "-ar", "48000",
                    "-c:a", "pcm_s16le", str(master),
                ],
                check=True,
            )
            shutil.copyfile(master, narration)
            subprocess.run(
                [
                    "ffmpeg", "-v", "error", "-y", "-i", str(render), "-i", str(master),
                    "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "192k", "-shortest", str(final),
                ],
                check=True,
            )

            fixture = ProjectFixture.__new__(ProjectFixture)
            fixture.project = project
            fixture.files = {
                "renders/final.mp4": final,
                "renders/render.mp4": render,
                "audio/master.wav": master,
                "audio/narration-only.wav": narration,
            }
            fixture.write_authoring_contract()
            for relative, timestamp in (
                ("qa/cover.png", 0.0),
                ("qa/contact-sheet.png", 0.5),
            ):
                frame = project / relative
                frame.parent.mkdir(parents=True, exist_ok=True)
                subprocess.run(
                    [
                        "ffmpeg", "-v", "error", "-y", "-i", str(final),
                        "-ss", str(timestamp), "-frames:v", "1", "-vf", "format=rgb24",
                        str(frame),
                    ],
                    check=True,
                )
                fixture.files[relative] = frame
            for relative, payload in (
                ("qa/leakage.txt", b"synthetic manual evidence"),
                ("qa/release.txt", b"synthetic manual evidence"),
            ):
                path = project / relative
                path.write_bytes(payload)
                fixture.files[relative] = path
            fixture.manifest = fixture._manifest()
            fixture.write_asr_evidence()
            fixture.write_manifest()

            result = gate.verify_project(project, tools=FakeAsrMediaTools())
            self.assertEqual("h264", result.video_codec)
            self.assertLess(result.true_peak_dbtp, 0.0)
            self.assertGreater(result.master_aac_sdr_db, 12.0)

            half = project / "audio/half-volume.wav"
            silence = project / "audio/silence.wav"
            subprocess.run(
                [
                    "ffmpeg", "-v", "error", "-y", "-i", str(master),
                    "-af", "volume=0.5", "-c:a", "pcm_s16le", str(half),
                ],
                check=True,
            )
            subprocess.run(
                [
                    "ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                    "anullsrc=channel_layout=stereo:sample_rate=48000:d=2",
                    "-c:a", "pcm_s16le", str(silence),
                ],
                check=True,
            )
            media_tools = gate.MediaTools()
            self.assertLess(media_tools.audio_sdr(master, half, 2.0), 12.0)
            self.assertLess(media_tools.audio_sdr(master, silence, 2.0), 12.0)

    @unittest.skipUnless(
        (Path(__file__).resolve().parents[2] / "tts/venv/bin/python").is_file()
        and (Path.home() / ".cache/whisper/small.pt").is_file(),
        "fixed local Whisper small runtime/model are required",
    )
    def test_real_offline_asr_rejects_sine_with_handwritten_nihao_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = ProjectFixture(Path(temporary) / "project")
            render = fixture.files["renders/render.mp4"]
            master = fixture.files["audio/master.wav"]
            final = fixture.files["renders/final.mp4"]
            narration = fixture.files["audio/narration-only.wav"]
            subprocess.run(
                [
                    "ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                    "color=c=blue:s=320x240:r=24:d=2", "-an", "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", str(render),
                ],
                check=True,
            )
            subprocess.run(
                [
                    "ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                    "sine=frequency=440:duration=2,volume=2", "-ac", "2", "-ar", "48000",
                    "-c:a", "pcm_s16le", str(master),
                ],
                check=True,
            )
            shutil.copyfile(master, narration)
            subprocess.run(
                [
                    "ffmpeg", "-v", "error", "-y", "-i", str(render), "-i", str(master),
                    "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "192k", "-shortest", str(final),
                ],
                check=True,
            )
            for relative, timestamp in (("qa/cover.png", 0.0), ("qa/contact-sheet.png", 0.5)):
                subprocess.run(
                    [
                        "ffmpeg", "-v", "error", "-y", "-i", str(final), "-ss", str(timestamp),
                        "-frames:v", "1", "-vf", "format=rgb24", str(fixture.files[relative]),
                    ],
                    check=True,
                )
            fixture.write_authoring_contract()
            fixture.manifest = fixture._manifest()
            fixture.write_asr_evidence()  # Intentionally claims the sine says "你好".
            fixture.write_manifest()

            with self.assertRaisesRegex(gate.GateFailure, "current offline ASR run"):
                gate.verify_project(fixture.project, tools=RealAsrFakeAuthoringTools())

    def test_short_video_stream_cannot_hide_behind_two_second_container(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            render = root / "render.mp4"
            master = root / "master.wav"
            final = root / "final.mp4"
            subprocess.run(
                [
                    "ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                    "color=c=blue:s=320x240:r=24:d=1.04", "-an", "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", str(render),
                ],
                check=True,
            )
            subprocess.run(
                [
                    "ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                    "sine=frequency=440:duration=2", "-ac", "2", "-ar", "48000",
                    "-c:a", "pcm_s16le", str(master),
                ],
                check=True,
            )
            subprocess.run(
                [
                    "ffmpeg", "-v", "error", "-y", "-i", str(render), "-i", str(master),
                    "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "192k", str(final),
                ],
                check=True,
            )
            tools = gate.MediaTools()
            assets = {
                "final": gate.Asset("assets.final", "final.mp4", final, gate.sha256_file(final)),
                "render": gate.Asset("assets.render", "render.mp4", render, gate.sha256_file(render)),
                "master": gate.Asset("assets.master", "master.wav", master, gate.sha256_file(master)),
            }
            probes = {key: tools.probe(asset.path) for key, asset in assets.items()}
            checks = gate.parse_checks(
                {"expected_video_codec": "h264", "duration_tolerance_sec": 1.0}
            )
            self.assertAlmostEqual(2.0, gate.probe_duration(probes["final"], "final"), places=2)
            with self.assertRaisesRegex(gate.GateFailure, "video stream does not cover"):
                gate.validate_media_structure(assets, probes, checks)


if __name__ == "__main__":
    unittest.main()
