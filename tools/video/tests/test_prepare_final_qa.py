"""Regression tests for default sandbox versus explicit strict QA preparation."""

from __future__ import annotations

import json
import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from tools.video import prepare_final_qa
from tools.video import verify_final_video as gate


FINAL_SHA = "a" * 64


class LightweightMediaTools:
    def __init__(self, narration_texts: dict[str, str]):
        self.narration_texts = narration_texts
        self.authoring_review_modes: list[bool] = []
        self.calls: dict[str, int] = {
            "transcribe": 0,
            "frame_rgb_receipt": 0,
            "video_decode_receipt": 0,
            "audio_sdr": 0,
            "loudness": 0,
            "analyze_final": 0,
        }
        self.asr_kinds: list[str] = []
        self.frame_receipt_calls: list[tuple[Path, float | None]] = []
        self.video_decode_paths: list[Path] = []

    def verify_authoring(
        self,
        _project: Path,
        _manifest: str,
        *,
        require_human_review: bool = False,
    ) -> list[str]:
        self.authoring_review_modes.append(require_human_review)
        return []

    def probe(self, path: Path) -> dict:
        if path.suffix == ".wav":
            return {"streams": [{"codec_type": "audio", "codec_name": "pcm_s16le"}]}
        return {"streams": [{"codec_type": "video", "codec_name": "h264",
                             "width": 1080, "height": 1920}]}

    def audio_sdr(self, _master: Path, _final: Path, _duration: float) -> float:
        self.calls["audio_sdr"] += 1
        return 35.0

    def loudness(self, _path: Path) -> gate.Loudness:
        self.calls["loudness"] += 1
        return gate.Loudness(-14.0, -1.0)

    def analyze_final(
        self, _path: Path, _duration: float
    ) -> tuple[list[gate.Interval], list[gate.Interval]]:
        self.calls["analyze_final"] += 1
        return [], []

    def video_decode_receipt(self, _path: Path) -> gate.VideoDecodeReceipt:
        self.calls["video_decode_receipt"] += 1
        self.video_decode_paths.append(_path)
        return gate.VideoDecodeReceipt(72, 0.0, 3.0, "f" * 64)

    def frame_rgb_receipt(
        self, _path: Path, timestamp_sec: float | None = None
    ) -> gate.FrameReceipt:
        self.calls["frame_rgb_receipt"] += 1
        self.frame_receipt_calls.append((_path, timestamp_sec))
        return gate.FrameReceipt(
            0.0 if timestamp_sec is None else timestamp_sec,
            1 / 24,
            "c" * 64,
        )

    def transcribe(self, sources: list[gate.Asset], parameters: dict, kind: str) -> dict:
        self.calls["transcribe"] += 1
        self.asr_kinds.append(kind)
        prefix = "final" if kind == "final_aac_asr" else "isolated"
        declared = [
            {
                "id": f"{prefix}-{index:03d}",
                "path": source.raw_path,
                "sha256": source.sha256,
            }
            for index, source in enumerate(sources)
        ]
        if kind == "final_aac_asr":
            texts = list(self.narration_texts.values())
            results = [
                {
                    "source_id": declared[0]["id"],
                    "transcript": " ".join(texts),
                    "segments": [
                        {
                            "id": f"{declared[0]['id']}:{index:06d}",
                            "start_sec": index + 0.2,
                            "end_sec": index + 0.8,
                            "text": text,
                        }
                        for index, text in enumerate(texts)
                    ],
                }
            ]
        else:
            results = []
            for declared_source, source in zip(declared, sources):
                text = self.narration_texts[source.raw_path]
                results.append(
                    {
                        "source_id": declared_source["id"],
                        "transcript": text,
                        "segments": [
                            {
                                "id": f"{declared_source['id']}:000000",
                                "start_sec": 0.2,
                                "end_sec": 0.8,
                                "text": text,
                            }
                        ],
                    }
                )
        return {
            "schema_version": 1,
            "engine": "openai-whisper",
            "model": "small",
            "language": parameters["language"],
            "checkpoint_sha256": gate.PINNED_WHISPER_CHECKPOINT_SHA256,
            "openai_whisper_version": gate.PINNED_OPENAI_WHISPER_VERSION,
            "sources": declared,
            "results": results,
        }


class PrepareFinalQaPolicyTests(unittest.TestCase):
    def parse(self, *extra: str):
        return prepare_final_qa.build_parser().parse_args(
            [
                "--project",
                "project",
                "--final",
                "renders/final.mp4",
                "--render",
                "renders/render.mp4",
                *extra,
            ]
        )

    def test_sandbox_is_default_and_has_a_final_manifest(self) -> None:
        args = self.parse()
        self.assertFalse(args.require_human_review)
        self.assertIsNone(args.human_review_input)
        self.assertEqual("qa/final-video-qa.json", args.final_manifest)

    def test_release_human_review_is_explicit_opt_in(self) -> None:
        args = self.parse("--require-human-review")
        self.assertTrue(args.require_human_review)

    def test_main_rejects_final_and_render_outside_lowercase_renders(self) -> None:
        for option in ("--final", "--render"):
            for invalid in (
                "final.mp4",
                "final/final.mp4",
                "output/final.mp4",
                "Renders/final.mp4",
            ):
                with (
                    self.subTest(option=option, invalid=invalid),
                    tempfile.TemporaryDirectory() as temporary,
                ):
                    project = Path(temporary)
                    arguments = [
                        "--project",
                        str(project),
                        "--final",
                        "renders/final.mp4",
                        "--render",
                        "renders/render.mp4",
                    ]
                    arguments[arguments.index(option) + 1] = invalid
                    with self.assertRaisesRegex(
                        SystemExit,
                        rf"{option} first path component must be lowercase 'renders'",
                    ):
                        prepare_final_qa.main(arguments)

    def test_generated_review_records_never_impersonate_a_human(self) -> None:
        visual = prepare_final_qa.pending_record(
            FINAL_SHA,
            text_field="notes",
            evidence=[{"path": "qa/frame.png", "sha256": "b" * 64}],
        )
        reviews = {
            "visual_frames": visual,
            "leakage": prepare_final_qa.pending_record(
                FINAL_SHA, text_field="notes", evidence=[]
            ),
            "release_safety": prepare_final_qa.pending_record(
                FINAL_SHA, text_field="notes", evidence=[]
            ),
            "silence": [],
            "black": [],
        }
        artifacts = {
            "final_aac_asr": {
                "assertions": [
                    {"expectation_id": "intro", "disposition": "human_review"}
                ]
            },
            "isolated_narration_asr": {"assertions": []},
        }
        template = prepare_final_qa.build_human_template(
            FINAL_SHA, reviews, artifacts
        )

        self.assertEqual("pending_human_review", visual["status"])
        self.assertIsNone(visual["reviewer_kind"])
        self.assertEqual("", visual["reviewer"])
        self.assertEqual("", visual["reviewed_at"])
        pending_asr = template["asr_reviews"]["final_aac_asr"]["intro"]
        self.assertEqual("pending_human_review", pending_asr["status"])
        self.assertIsNone(pending_asr["reviewer_kind"])

    def test_prepared_run_cache_is_exact_and_never_falls_back_to_live_work(self) -> None:
        source = gate.Asset("source", "audio/line.wav", Path("line.wav"), "a" * 64)
        parameters = {"engine": "openai-whisper", "model": "small", "language": "zh"}
        receipt = {"schema_version": 1, "results": []}

        class Delegate:
            def __getattr__(self, name):
                raise AssertionError(f"unexpected delegate call: {name}")

        tools = prepare_final_qa.PreparedRunMediaTools(
            Delegate(),  # type: ignore[arg-type]
            asr_receipts={
                "isolated_narration_asr": (
                    ((source.raw_path, source.sha256),),
                    parameters,
                    receipt,
                )
            },
            frame_receipts={},
            final_analysis=(Path("final.mp4"), 1.0, ([], [])),
        )
        self.assertEqual(
            receipt,
            tools.transcribe([source], parameters, "isolated_narration_asr"),
        )
        with self.assertRaisesRegex(SystemExit, "ASR evidence changed"):
            tools.transcribe(
                [gate.Asset("source", source.raw_path, source.path, "b" * 64)],
                parameters,
                "isolated_narration_asr",
            )

    @staticmethod
    def approved(final_sha: str, text_field: str, text: str, *, evidence=None) -> dict:
        row = {
            "status": "approved",
            "reviewer_kind": "human",
            "reviewer": "fixture-reviewer",
            "reviewed_at": "2026-01-01T12:00:00+08:00",
            "final_sha256": final_sha,
            text_field: text,
        }
        if evidence is not None:
            row["evidence"] = evidence
        return row

    def merge_fixture(
        self,
        root: Path,
        *,
        pending_global: bool,
        pending_second_asr: bool,
    ) -> dict:
        project = root / "project"
        qa = project / "qa"
        qa.mkdir(parents=True)
        frame = qa / "frame.png"
        leakage = qa / "leakage.txt"
        release = qa / "release.txt"
        frame.write_bytes(b"frame")
        leakage.write_text("leakage review", encoding="utf-8")
        release.write_text("release review", encoding="utf-8")
        visual_evidence = [
            {
                "path": "qa/frame.png",
                "sha256": gate.sha256_file(frame),
                "sample_time_sec": 0.0,
            }
        ]
        if pending_global:
            reviews = {
                "visual_frames": prepare_final_qa.pending_record(
                    FINAL_SHA,
                    text_field="notes",
                    evidence=visual_evidence,
                ),
                "leakage": prepare_final_qa.pending_record(
                    FINAL_SHA, text_field="notes", evidence=[]
                ),
                "release_safety": prepare_final_qa.pending_record(
                    FINAL_SHA, text_field="notes", evidence=[]
                ),
                "silence": [],
                "black": [],
            }
        else:
            reviews = {
                "visual_frames": self.approved(
                    FINAL_SHA,
                    "notes",
                    "visual approved",
                    evidence=visual_evidence,
                ),
                "leakage": self.approved(
                    FINAL_SHA,
                    "notes",
                    "leakage approved",
                    evidence=[
                        {
                            "path": "qa/leakage.txt",
                            "sha256": gate.sha256_file(leakage),
                        }
                    ],
                ),
                "release_safety": self.approved(
                    FINAL_SHA,
                    "notes",
                    "release approved",
                    evidence=[
                        {
                            "path": "qa/release.txt",
                            "sha256": gate.sha256_file(release),
                        }
                    ],
                ),
                "silence": [],
                "black": [],
            }
        artifacts = {
            "final_aac_asr": {
                "assertions": (
                    [
                        {
                            "expectation_id": "intro",
                            "disposition": "human_review",
                        }
                    ]
                    if pending_second_asr
                    else []
                )
            },
            "isolated_narration_asr": {
                "assertions": (
                    [
                        {
                            "expectation_id": "intro",
                            "disposition": "human_review",
                        }
                    ]
                    if pending_second_asr
                    else []
                )
            },
        }
        asr_reviews = {"final_aac_asr": {}, "isolated_narration_asr": {}}
        if pending_second_asr:
            asr_reviews["final_aac_asr"]["intro"] = self.approved(
                FINAL_SHA, "reason", "final ASR approved"
            )
            asr_reviews["isolated_narration_asr"]["intro"] = prepare_final_qa.pending_record(
                FINAL_SHA, text_field="reason"
            )
        supplied = {
            "schema_version": 1,
            "final_sha256": FINAL_SHA,
            "reviews": reviews,
            "asr_reviews": asr_reviews,
        }
        input_path = project / "human-review.json"
        input_path.write_text(json.dumps(supplied, ensure_ascii=False), encoding="utf-8")
        return {
            "project": project,
            "input_path": input_path,
            "reviews": reviews,
            "artifacts": artifacts,
            "staging_manifest": {
                "reviews": reviews,
                "asr_evidence": {
                    "final_aac_asr": {"artifact": {}},
                    "isolated_narration_asr": {"artifact": {}},
                },
            },
            "artifact_paths": {
                "final_aac_asr": qa / "final-aac-asr.json",
                "isolated_narration_asr": qa / "isolated-narration-asr.json",
            },
        }

    def test_strict_merge_rejects_pending_global_reviews_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = self.merge_fixture(
                Path(temporary),
                pending_global=True,
                pending_second_asr=False,
            )
            with mock.patch.object(prepare_final_qa, "write_json_atomic") as writer:
                with self.assertRaisesRegex(SystemExit, "still contains pending"):
                    prepare_final_qa.merge_human_input(
                        project=fixture["project"],
                        input_path=fixture["input_path"],
                        final_sha256=FINAL_SHA,
                        staging_manifest=fixture["staging_manifest"],
                        artifacts=fixture["artifacts"],
                        artifact_paths=fixture["artifact_paths"],
                        silences=[],
                        black=[],
                    )
            writer.assert_not_called()

    def test_invalid_second_asr_review_cannot_half_update_first_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = self.merge_fixture(
                Path(temporary),
                pending_global=False,
                pending_second_asr=True,
            )
            with mock.patch.object(prepare_final_qa, "write_json_atomic") as writer:
                with self.assertRaisesRegex(SystemExit, "status must be approved"):
                    prepare_final_qa.merge_human_input(
                        project=fixture["project"],
                        input_path=fixture["input_path"],
                        final_sha256=FINAL_SHA,
                        staging_manifest=fixture["staging_manifest"],
                        artifacts=fixture["artifacts"],
                        artifact_paths=fixture["artifact_paths"],
                        silences=[],
                        black=[],
                    )
            writer.assert_not_called()
            for path in fixture["artifact_paths"].values():
                self.assertFalse(path.exists())

    def test_complete_strict_merge_writes_all_artifacts_after_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = self.merge_fixture(
                Path(temporary),
                pending_global=False,
                pending_second_asr=False,
            )
            merged = prepare_final_qa.merge_human_input(
                project=fixture["project"],
                input_path=fixture["input_path"],
                final_sha256=FINAL_SHA,
                staging_manifest=fixture["staging_manifest"],
                artifacts=fixture["artifacts"],
                artifact_paths=fixture["artifact_paths"],
                silences=[],
                black=[],
            )
            self.assertEqual("approved", merged["reviews"]["visual_frames"]["status"])
            for kind, path in fixture["artifact_paths"].items():
                self.assertTrue(path.is_file())
                self.assertEqual(
                    gate.sha256_file(path),
                    merged["asr_evidence"][kind]["artifact"]["sha256"],
                )

    def test_path_collision_is_rejected_without_modifying_input_sentinel(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            project.mkdir()
            sentinel = project / "final.mp4"
            sentinel.write_bytes(b"do-not-touch")
            with self.assertRaisesRegex(SystemExit, "output/input path collision"):
                prepare_final_qa.validate_path_plan(
                    {"final video": sentinel},
                    {"final QA manifest": sentinel},
                )
            self.assertEqual(b"do-not-touch", sentinel.read_bytes())

            alias = project / "alias.json"
            os.link(sentinel, alias)
            with self.assertRaisesRegex(SystemExit, "output/input path collision"):
                prepare_final_qa.validate_path_plan(
                    {"final video": sentinel},
                    {"final QA manifest": alias},
                )
            self.assertEqual(b"do-not-touch", sentinel.read_bytes())

    def test_project_symlink_is_rejected_before_media_work(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "target"
            target.mkdir()
            link = Path(temporary) / "project-link"
            link.symlink_to(target, target_is_directory=True)
            with self.assertRaisesRegex(SystemExit, "must not be a symlink"):
                prepare_final_qa.main(
                    [
                        "--project",
                        str(link),
                        "--final",
                        "final.mp4",
                        "--render",
                        "render.mp4",
                    ]
                )

    def test_strict_json_rejects_duplicate_keys_and_nan(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "value.json"
            path.write_text('{"value": 1, "value": 2}', encoding="utf-8")
            with self.assertRaisesRegex(SystemExit, "duplicate object key"):
                prepare_final_qa.load_json(path, "fixture")
            path.write_text('{"value": NaN}', encoding="utf-8")
            with self.assertRaisesRegex(SystemExit, "non-standard numeric constant"):
                prepare_final_qa.load_json(path, "fixture")

    def test_read_and_resolve_errors_do_not_echo_exception_payloads(self) -> None:
        leaked = "/private/var/input.json token=super-secret"
        with mock.patch.object(Path, "read_text", side_effect=OSError(leaked)):
            with self.assertRaises(SystemExit) as raised:
                prepare_final_qa.load_json(Path("unused.json"), "timeline")
        message = str(raised.exception)
        self.assertIn("timeline cannot be read [io-or-encoding-error]", message)
        self.assertNotIn("/private/var", message)
        self.assertNotIn("super-secret", message)

        with mock.patch.object(
            prepare_final_qa.gate,
            "resolve_project_file",
            side_effect=gate.GateFailure(leaked),
        ):
            with self.assertRaises(SystemExit) as raised:
                prepare_final_qa.inside_existing(Path("project"), "input.json", "final")
        message = str(raised.exception)
        self.assertIn("existing regular project-relative file", message)
        self.assertNotIn("/private/var", message)
        self.assertNotIn("super-secret", message)

    def test_output_path_errors_do_not_echo_absolute_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            project.mkdir()
            target = project / "target"
            target.mkdir()
            link = project / "private-link"
            link.symlink_to(target, target_is_directory=True)
            with self.assertRaises(SystemExit) as raised:
                prepare_final_qa.plan_output(
                    project,
                    "private-link/output.json",
                    "final manifest",
                )
        message = str(raised.exception)
        self.assertIn("parent must not be a symlink", message)
        self.assertNotIn(temporary, message)

    def test_cli_suppresses_unexpected_exception_payload(self) -> None:
        stderr = io.StringIO()
        leaked = "/Users/private/final.mp4 bearer=super-secret"
        with mock.patch.object(
            prepare_final_qa,
            "main",
            side_effect=RuntimeError(leaked),
        ):
            with redirect_stderr(stderr):
                code = prepare_final_qa.cli([])

        self.assertEqual(1, code)
        self.assertIn("FINAL QA PREP: FAIL [unexpected]", stderr.getvalue())
        self.assertNotIn("/Users", stderr.getvalue())
        self.assertNotIn("super-secret", stderr.getvalue())

    def test_atomic_outputs_do_not_follow_existing_hardlinks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            project.mkdir()
            sentinel = project / "sentinel.bin"
            sentinel.write_bytes(b"original")
            json_output = project / "output.json"
            os.link(sentinel, json_output)
            prepare_final_qa.write_json_atomic(
                project,
                json_output,
                {"safe": True},
                "JSON output",
            )
            self.assertEqual(b"original", sentinel.read_bytes())
            self.assertEqual({"safe": True}, json.loads(json_output.read_text()))

            frame_output = project / "frame.png"
            os.link(sentinel, frame_output)

            def fake_run(command, **_kwargs):
                self.assertIn("-threads", command)
                self.assertEqual("2", command[command.index("-threads") + 1])
                self.assertIn("-filter_threads", command)
                self.assertIn("-ss", command)
                self.assertLess(command.index("-ss"), command.index("-i"))
                self.assertIn("-copyts", command)
                Path(command[-1]).write_bytes(b"png-frame")
                return SimpleNamespace(returncode=0)

            with (
                mock.patch.dict(
                    os.environ,
                    {gate.resource_budget.FFMPEG_THREADS_ENV: "2"},
                ),
                mock.patch.object(
                    prepare_final_qa.subprocess,
                    "run",
                    side_effect=fake_run,
                ),
            ):
                prepare_final_qa.extract_frame(
                    project,
                    project / "final.mp4",
                    0.0,
                    frame_output,
                )
            self.assertEqual(b"original", sentinel.read_bytes())
            self.assertEqual(b"png-frame", frame_output.read_bytes())

    def run_lightweight_main(
        self,
        root: Path,
        *extra: str,
        customize=None,
    ) -> tuple[int, Path, LightweightMediaTools]:
        project = root / "project"
        (project / "audio").mkdir(parents=True)
        (project / "renders").mkdir()
        narration_texts = {
            "audio/intro.wav": "开场旁白",
            "audio/outro.wav": "作品总结",
            "audio/cta.wav": gate.FIXED_OUTRO_CTA,
        }
        timeline = {
            "duration_sec": 3.0,
            "master_audio": "master.wav",
            "segments": [
                {"key": "intro", "role": "intro", "start_sec": 0.0, "end_sec": 1.0},
                {
                    "key": "work-outro",
                    "role": "outro",
                    "start_sec": 1.0,
                    "end_sec": 2.0,
                },
                {
                    "key": "outro-cta",
                    "role": "cta",
                    "start_sec": 2.0,
                    "end_sec": 3.0,
                },
            ],
        }
        authoring = {
            "project_kind": "narrative",
            "narration_sequence": [
                {
                    "id": "intro",
                    "role": "intro",
                    "text": narration_texts["audio/intro.wav"],
                    "wav": "audio/intro.wav",
                },
                {
                    "id": "work-outro",
                    "role": "work_outro",
                    "text": narration_texts["audio/outro.wav"],
                    "wav": "audio/outro.wav",
                },
                {
                    "id": "outro-cta",
                    "role": "outro_cta",
                    "text": narration_texts["audio/cta.wav"],
                    "wav": "audio/cta.wav",
                },
            ],
        }
        if customize is not None:
            customize(authoring, timeline, narration_texts)
        (project / "timeline.json").write_text(
            json.dumps(timeline, ensure_ascii=False), encoding="utf-8"
        )
        (project / "project-manifest.json").write_text(
            json.dumps(authoring, ensure_ascii=False), encoding="utf-8"
        )
        for raw, payload in (
            ("renders/final.mp4", b"final"),
            ("renders/render.mp4", b"render"),
            ("master.wav", b"master"),
            ("audio/intro.wav", b"intro"),
            ("audio/outro.wav", b"outro"),
            ("audio/cta.wav", b"cta"),
        ):
            (project / raw).write_bytes(payload)

        tools = LightweightMediaTools(narration_texts)

        def fake_visual(project_root, final_asset, planned_outputs, media_tools):
            evidence = []
            receipts = {}
            for output, timestamp in planned_outputs:
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(f"frame-{timestamp}".encode())
                current = media_tools.frame_rgb_receipt(final_asset.path, timestamp)
                extracted = media_tools.frame_rgb_receipt(output)
                receipts[(final_asset.path, timestamp)] = current
                receipts[(output, None)] = extracted
                evidence.append(
                    {
                        "path": output.relative_to(project_root).as_posix(),
                        "sha256": gate.sha256_file(output),
                        "sample_time_sec": round(timestamp, 6),
                    }
                )
            return evidence, receipts

        with (
            mock.patch.object(prepare_final_qa.gate, "MediaTools", return_value=tools),
            mock.patch.object(
                prepare_final_qa.gate,
                "validate_media_structure",
                return_value=(3.0, "h264"),
            ),
            mock.patch.object(
                prepare_final_qa,
                "build_visual_evidence",
                side_effect=fake_visual,
            ),
        ):
            code = prepare_final_qa.main(
                [
                    "--project",
                    str(project),
                    "--final",
                    "renders/final.mp4",
                    "--render",
                    "renders/render.mp4",
                    *extra,
                ]
            )
        return code, project, tools

    def test_editorial_variants_keep_live_final_checks(self) -> None:
        for variant in ("custom_cta", "omit_cta", "intro_only", "no_narration", "legacy_cta"):
            with self.subTest(variant=variant), tempfile.TemporaryDirectory() as temporary:
                def customize(authoring, timeline, texts):
                    if variant == "legacy_cta":
                        authoring["editorial"] = {
                            "cta": "fixed", "cta_text_version": "legacy-v1",
                            "reason": "保留历史长版旁白",
                        }
                        texts["audio/cta.wav"] = gate.fixed_cta_text("legacy-v1")
                        authoring["narration_sequence"][-1]["text"] = texts["audio/cta.wav"]
                        return
                    authoring["editorial"] = {
                        "narration": "standard" if variant in {"custom_cta", "omit_cta"} else "custom",
                        "cta": "custom" if variant == "custom_cta" else "omit",
                        "reason": "用户要求当期调整旁白结构",
                        "cta_user_request": "这期结尾只问想听的下一个主题。" if variant == "custom_cta" else "这期不要引流配音。",
                    }
                    if variant == "custom_cta":
                        texts["audio/cta.wav"] = "留下你想听的下一个主题。"
                        authoring["narration_sequence"][-1]["text"] = texts["audio/cta.wav"]
                    else:
                        count = {"omit_cta": 2, "intro_only": 1, "no_narration": 0}[variant]
                        authoring["narration_sequence"] = authoring["narration_sequence"][:count]
                        for path in list(texts)[count:]:
                            texts.pop(path)
                        for row in timeline["segments"][count:]:
                            row["requires_narration"] = False
                            row["role"] = "free"

                with redirect_stdout(io.StringIO()):
                    code, project, media = self.run_lightweight_main(
                        Path(temporary), customize=customize,
                    )
                self.assertEqual(0, code)
                manifest = prepare_final_qa.load_json(project / "qa/final-video-qa.json", "QA")
                self.assertEqual("structured" if variant == "legacy_cta" else "custom", manifest["narration_mode"])
                self.assertEqual(2, media.calls["video_decode_receipt"])
                for name in ("audio_sdr", "loudness", "analyze_final"):
                    self.assertEqual(1, media.calls[name])
                self.assertIn("final_aac_asr", media.asr_kinds)

    def test_preparer_rejects_landscape_before_asr_or_frame_extraction(self) -> None:
        original_probe = LightweightMediaTools.probe
        def landscape_probe(tools, path):
            result = original_probe(tools, path)
            for stream in result["streams"]:
                if stream["codec_type"] == "video":
                    stream.update(width=1920, height=1080)
            return result

        with tempfile.TemporaryDirectory() as temporary, \
                mock.patch.object(LightweightMediaTools, "probe", landscape_probe), \
                mock.patch.object(LightweightMediaTools, "transcribe") as transcribe:
            with self.assertRaisesRegex(gate.GateFailure, "dimensions must match"):
                self.run_lightweight_main(Path(temporary))
            transcribe.assert_not_called()

    def test_main_local_writes_pending_final_manifest_without_human_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code, project, tools = self.run_lightweight_main(Path(temporary))
            self.assertEqual(0, code)
            self.assertEqual([False, False, False], tools.authoring_review_modes)
            # Two ASR jobs and one exact-frame decode pair per visual sample are
            # produced once by the preparer, then reused in-process by the gate.
            self.assertEqual(2, tools.calls["transcribe"])
            self.assertEqual(
                ["final_aac_asr", "isolated_narration_asr"],
                tools.asr_kinds,
            )
            self.assertEqual(8, tools.calls["frame_rgb_receipt"])
            final_frame_calls = [
                row
                for row in tools.frame_receipt_calls
                if row[0].name == "final.mp4"
            ]
            self.assertEqual(4, len(final_frame_calls))
            self.assertEqual(
                [0.0, 0.5, 1.5, 2.5],
                [row[1] for row in final_frame_calls],
            )
            # Mechanical red lines remain live, but execute only in the central
            # verifier rather than once in each phase.
            self.assertEqual(2, tools.calls["video_decode_receipt"])
            self.assertEqual(
                ["final.mp4", "render.mp4"],
                [path.name for path in tools.video_decode_paths],
            )
            self.assertEqual(1, tools.calls["audio_sdr"])
            self.assertEqual(1, tools.calls["loudness"])
            self.assertEqual(1, tools.calls["analyze_final"])
            manifest_path = project / "qa/final-video-qa.json"
            self.assertTrue(manifest_path.is_file())
            self.assertFalse(
                (project / "qa/human-review-input.template.json").exists()
            )
            manifest = prepare_final_qa.load_json(manifest_path, "local manifest")
            for key in ("visual_frames", "leakage", "release_safety"):
                review = manifest["reviews"][key]
                self.assertEqual("pending_human_review", review["status"])
                self.assertIsNone(review["reviewer_kind"])
                self.assertEqual("", review["reviewer"])
                self.assertEqual("", review["reviewed_at"])
            self.assertNotIn(str(project), stdout.getvalue())
            self.assertIn("FINAL VIDEO QA: PASS", stdout.getvalue())
            self.assertNotIn("--project <project-relative-path>", stdout.getvalue())
            self.assertNotIn("profile=local_test", stdout.getvalue())
            self.assertNotIn("human_review=", stdout.getvalue())
            self.assertNotIn("Pending human review", stdout.getvalue())
            self.assertNotIn("RELEASE", stdout.getvalue())
            self.assertNotIn("授权", stdout.getvalue())
            self.assertNotIn("版权", stdout.getvalue())

    def test_main_strict_without_input_returns_two_and_omits_final_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code, project, tools = self.run_lightweight_main(
                    Path(temporary), "--require-human-review"
                )
            self.assertEqual(2, code)
            self.assertEqual([True], tools.authoring_review_modes)
            self.assertFalse((project / "qa/final-video-qa.json").exists())
            self.assertTrue((project / "qa/final-video-qa.staging.json").is_file())
            self.assertTrue((project / "qa/human-review-input.template.json").is_file())
            self.assertIn("RELEASE REVIEW REQUIRED", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
