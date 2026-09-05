"""Focused contracts for the reusable, media-free video templates."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[3]


def load_template(module_name: str, relative_path: str):
    path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load template module: {path}")
    module = importlib.util.module_from_spec(spec)
    # Dataclass resolves annotations through sys.modules while the module is
    # executed, so register this private test name first.
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


AI_MV = load_template(
    "_cc_media_ai_voice_mv_template",
    "tools/video/templates/ai-voice-mv/build.py",
)
LONGFORM = load_template(
    "_cc_media_longform_timeline_template",
    "tools/video/templates/longform-timeline/build.py",
)


class TemplatePathSafetyTests(unittest.TestCase):
    def test_rejects_parent_absolute_and_escaping_symlink_paths(self) -> None:
        for module in (AI_MV, LONGFORM):
            with self.subTest(template=module.__name__), tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary)
                project = base / "project"
                outside = base / "outside"
                project.mkdir()
                outside.mkdir()

                with self.assertRaisesRegex(SystemExit, "stay inside the project"):
                    module.resolve_inside(project, "../outside/file", "fixture")
                with self.assertRaisesRegex(SystemExit, "stay inside the project"):
                    module.resolve_inside(project, str(outside / "file"), "fixture")

                (project / "final").symlink_to(outside, target_is_directory=True)
                with self.assertRaisesRegex(SystemExit, "resolves outside the project"):
                    module.resolve_inside(project, "final/2026-08-10/output.mp4", "output")

    def test_rejects_safe_target_reached_through_output_symlink(self) -> None:
        for module in (AI_MV, LONGFORM):
            with self.subTest(template=module.__name__), tempfile.TemporaryDirectory() as temporary:
                project = Path(temporary).resolve()
                actual = project / "actual-output"
                actual.mkdir()
                (project / "final").symlink_to(actual, target_is_directory=True)

                output = module.resolve_inside(project, "final/date/output.mp4", "output")
                with self.assertRaisesRegex(SystemExit, "must not be a symlink"):
                    module.ensure_safe_output(project, output)


class TemplateResourceBudgetTests(unittest.TestCase):
    class FakeLease:
        threads = 3

        def __init__(self) -> None:
            self.entered = False
            self.exited = False

        def __enter__(self):
            self.entered = True
            return self

        def __exit__(self, _exc_type, _exc, _traceback) -> None:
            self.exited = True

    def test_each_template_holds_an_adaptive_lease_for_each_ffmpeg_process(self) -> None:
        for module in (AI_MV, LONGFORM):
            with self.subTest(template=module.__name__):
                lease = self.FakeLease()
                completed = mock.Mock(returncode=0)
                with (
                    mock.patch.object(
                        module.resource_budget,
                        "resolve_ffmpeg_threads",
                        return_value=lease,
                    ) as resolve,
                    mock.patch.object(module.subprocess, "run", return_value=completed) as run,
                ):
                    result = module.run(
                        ["ffmpeg", "-v", "error", "-i", "input.mp4", "output.mp4"],
                        "fixture",
                        REPO_ROOT,
                    )

                self.assertIs(completed, result)
                resolve.assert_called_once_with()
                self.assertTrue(lease.entered)
                self.assertTrue(lease.exited)
                command = run.call_args.args[0]
                self.assertEqual("ffmpeg", command[0])
                self.assertEqual(2, command.count("-threads"))
                self.assertEqual("3", command[command.index("-filter_threads") + 1])
                self.assertEqual(
                    "3",
                    command[command.index("-filter_complex_threads") + 1],
                )
                self.assertEqual("output.mp4", command[-1])
                self.assertEqual("3", command[-2])
                self.assertEqual("-threads", command[-3])

    def test_ffprobe_does_not_register_as_heavy_work(self) -> None:
        fixtures = (
            (
                AI_MV,
                lambda module: module.probe_json(Path("fixture.mp4"), "format=duration"),
            ),
            (
                LONGFORM,
                lambda module: module.probe(Path("fixture.mp4"), "format=duration"),
            ),
        )
        for module, invoke in fixtures:
            with self.subTest(template=module.__name__), mock.patch.object(
                module.resource_budget,
                "resolve_ffmpeg_threads",
            ) as resolve, mock.patch.object(
                module.subprocess,
                "check_output",
                return_value='{"format":{"duration":"1.0"}}',
            ):
                invoke(module)
            resolve.assert_not_called()

    def test_ai_speech_probe_uses_the_same_budgeted_runner(self) -> None:
        completed = mock.Mock(returncode=0, stderr="")
        with (
            mock.patch.object(AI_MV, "duration", return_value=2.0),
            mock.patch.object(AI_MV, "run", return_value=completed) as run,
        ):
            self.assertEqual((0.0, 2.0), AI_MV.speech_window(Path("voice.wav")))
        command = run.call_args.args[0]
        self.assertEqual("ffmpeg", command[0])
        self.assertTrue(run.call_args.kwargs["capture_output"])
        self.assertTrue(run.call_args.kwargs["text"])


class AiVoiceTemplateTests(unittest.TestCase):
    @staticmethod
    def config(*, output_dir: str | None = None) -> dict:
        value = {
            "schema_version": 1,
            "voice_selection": "voice-selection.json",
            "watermark_png": "assets/watermark.png",
            "songs": [
                {
                    "key": "song",
                    "title": "Song",
                    "video": "raw/song.mp4",
                    "song_audio": "audio/song.wav",
                    "intro_voice": "voice/intro.wav",
                    "output": "song.mp4",
                    "crop": None,
                    "audio_gain": 1.0,
                }
            ],
        }
        if output_dir is not None:
            value["output_dir"] = output_dir
        return value

    def test_output_dir_defaults_to_and_only_allows_renders(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary).resolve()
            songs, settings = AI_MV.parse_config(project, self.config())
            self.assertEqual(project / "renders", settings["output_dir"])
            dated_output = settings["output_dir"] / "2026-08-12" / songs[0].output_name
            self.assertEqual(
                Path("renders/2026-08-12/song.mp4"),
                dated_output.relative_to(project),
            )

            songs, settings = AI_MV.parse_config(
                project,
                self.config(output_dir="renders"),
            )
            self.assertEqual(project / "renders", settings["output_dir"])
            self.assertEqual("song.mp4", songs[0].output_name)

            for invalid in (
                "final",
                "output",
                "Renders",
                "./renders",
                "renders/",
                "renders/nested",
            ):
                with self.subTest(invalid=invalid), self.assertRaisesRegex(
                    SystemExit,
                    "output_dir must be exactly 'renders'",
                ):
                    AI_MV.parse_config(
                        project,
                        self.config(output_dir=invalid),
                    )

    def test_trimmed_voice_cache_symlink_is_rejected_before_write(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            project = (base / "project").resolve()
            cache = project / "tmp" / "ai-voice-mv"
            cache.mkdir(parents=True)
            outside = base / "outside.wav"
            outside.write_bytes(b"must remain untouched")
            (cache / "song-intro-trimmed.wav").symlink_to(outside)
            song = AI_MV.Song(
                key="song",
                title="Song",
                video=project / "video.mp4",
                song_audio=project / "song.wav",
                intro_voice=project / "intro.wav",
                output_name="song.mp4",
                crop=None,
                audio_gain=1.0,
            )

            with (
                mock.patch.object(AI_MV, "speech_window") as speech_window,
                mock.patch.object(AI_MV, "run") as run,
                self.assertRaisesRegex(SystemExit, "must not be a symlink"),
            ):
                AI_MV.trim_voice(song, cache, project)
            speech_window.assert_not_called()
            run.assert_not_called()
            self.assertEqual(b"must remain untouched", outside.read_bytes())

    def test_intro_sidecar_selection_mismatch_fails_before_media_probe(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary).resolve()
            selection = {"resolved_voice_id": "CV002", "marker": "current-project"}
            selection_path = project / "voice-selection.json"
            selection_path.write_text(json.dumps(selection), encoding="utf-8")

            watermark = project / "watermark.png"
            video = project / "video.mp4"
            song_audio = project / "song.wav"
            intro_voice = project / "intro.wav"
            for path in (watermark, video, song_audio, intro_voice):
                path.write_bytes(b"fixture")
            Path(f"{intro_voice}.tts.json").write_text(
                json.dumps(
                    {
                        "selection": {
                            "resolved_voice_id": "CV002",
                            "marker": "copied-from-another-project",
                        },
                        "resolved_voice_id": "CV002",
                        "output_sha256": AI_MV.sha256_file(intro_voice),
                    }
                ),
                encoding="utf-8",
            )

            song = AI_MV.Song(
                key="song",
                title="Song",
                video=video,
                song_audio=song_audio,
                intro_voice=intro_voice,
                output_name="song.mp4",
                crop=None,
                audio_gain=1.0,
            )
            with self.assertRaisesRegex(SystemExit, "selection does not match"):
                AI_MV.validate_inputs(
                    [song],
                    {
                        "selection": selection_path,
                        "watermark_png": watermark,
                    },
                    project,
                )

    def test_empty_project_voice_id_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary).resolve()
            selection = {"resolved_voice_id": ""}
            selection_path = project / "voice-selection.json"
            selection_path.write_text(json.dumps(selection), encoding="utf-8")
            watermark = project / "watermark.png"
            video = project / "video.mp4"
            song_audio = project / "song.wav"
            intro_voice = project / "intro.wav"
            for path in (watermark, video, song_audio, intro_voice):
                path.write_bytes(b"fixture")
            Path(f"{intro_voice}.tts.json").write_text(
                json.dumps(
                    {
                        "selection": selection,
                        "resolved_voice_id": "",
                        "output_sha256": AI_MV.sha256_file(intro_voice),
                    }
                ),
                encoding="utf-8",
            )
            song = AI_MV.Song(
                key="song",
                title="Song",
                video=video,
                song_audio=song_audio,
                intro_voice=intro_voice,
                output_name="song.mp4",
                crop=None,
                audio_gain=1.0,
            )
            with self.assertRaisesRegex(SystemExit, "resolved_voice_id must be non-empty"):
                AI_MV.validate_inputs(
                    [song],
                    {"selection": selection_path, "watermark_png": watermark},
                    project,
                )

    def test_external_intro_sidecar_symlink_is_rejected_before_read(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            project = (base / "project").resolve()
            project.mkdir()
            selection_path = project / "voice-selection.json"
            selection_path.write_text(
                json.dumps({"resolved_voice_id": "CV002"}),
                encoding="utf-8",
            )
            watermark = project / "watermark.png"
            video = project / "video.mp4"
            song_audio = project / "song.wav"
            intro_voice = project / "intro.wav"
            for path in (watermark, video, song_audio, intro_voice):
                path.write_bytes(b"fixture")
            outside = base / "outside-sidecar.json"
            outside.write_text("{invalid external sentinel", encoding="utf-8")
            Path(f"{intro_voice}.tts.json").symlink_to(outside)
            song = AI_MV.Song(
                key="song",
                title="Song",
                video=video,
                song_audio=song_audio,
                intro_voice=intro_voice,
                output_name="song.mp4",
                crop=None,
                audio_gain=1.0,
            )

            with self.assertRaisesRegex(SystemExit, "TTS sidecar must not be a symlink"):
                AI_MV.validate_inputs(
                    [song],
                    {"selection": selection_path, "watermark_png": watermark},
                    project,
                )
            self.assertEqual("{invalid external sentinel", outside.read_text(encoding="utf-8"))


class LongformTimelineTemplateTests(unittest.TestCase):
    def test_song_without_narration_needs_no_voice_selection_and_keeps_media_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary).resolve()
            raw = self.config("showcase_align")
            raw.pop("voice_selection")
            raw["segments"][0].update(requires_narration=False, narration_wavs=[])
            parsed = LONGFORM.parse_config(project, raw)
            segment = parsed["segments"][0]
            for key in ("clip", "audio_segment"):
                segment[key].parent.mkdir(parents=True, exist_ok=True)
                segment[key].write_bytes(b"media fixture")
            segment["audio_segment_sha256"] = LONGFORM.sha256_file(segment["audio_segment"])
            with (
                mock.patch.object(LONGFORM, "media_duration", return_value=420.0),
                mock.patch.object(LONGFORM, "probe", return_value={"streams": [{"width": 1080, "height": 1920}]}),
                mock.patch.object(LONGFORM, "run"),
            ):
                LONGFORM.validate_inputs(parsed, project)
                LONGFORM.build(parsed, project)
                segment["audio_segment"].write_bytes(b"changed media")
                with self.assertRaisesRegex(SystemExit, "SHA-256 mismatch"):
                    LONGFORM.validate_inputs(parsed, project)
            timeline = json.loads(parsed["outputs"]["timeline"].read_text(encoding="utf-8"))
            self.assertNotIn("voice_selection", timeline)
            self.assertFalse(timeline["segments"][0]["requires_narration"])
            self.assertEqual([], timeline["segments"][0]["narration_wavs"])

    @staticmethod
    def config(acceptance: str | None) -> dict:
        song = {
            "key": "long-song",
            "role": "song",
            "clip": "clips/long-song.mp4",
            "source_seek_sec": 0.0,
            "duration_sec": 420.0,
            "narration_wavs": ["voice/long-song.wav"],
            "audio_segment": "audio/segments/long-song.wav",
            "audio_segment_sha256": "0" * 64,
        }
        if acceptance is not None:
            song["acceptance"] = acceptance
        return {
            "schema_version": 1,
            "voice_selection": "voice-selection.json",
            "outputs": {
                "master_audio": "master.wav",
                "footage_track": "footage.mp4",
                "timeline": "timeline.json",
            },
            "video": {"width": 1080, "height": 1920, "fps": 30},
            "segments": [song],
        }

    def prepare_inputs(self, project: Path) -> dict:
        parsed = LONGFORM.parse_config(project, self.config("showcase_align"))
        selection = {"resolved_voice_id": "CV002", "marker": "current-project"}
        parsed["selection"].write_text(json.dumps(selection), encoding="utf-8")

        segment = parsed["segments"][0]
        narration = segment["narration_wavs"][0]
        for path, content in (
            (narration, b"narration fixture"),
            (segment["clip"], b"video fixture"),
            (segment["audio_segment"], b"audio fixture"),
        ):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        Path(f"{narration}.tts.json").write_text(
            json.dumps(
                {
                    "selection": selection,
                    "resolved_voice_id": "CV002",
                    "output_sha256": LONGFORM.sha256_file(narration),
                }
            ),
            encoding="utf-8",
        )
        segment["audio_segment_sha256"] = LONGFORM.sha256_file(segment["audio_segment"])
        return parsed

    def test_accepts_long_song_with_explicit_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            parsed = LONGFORM.parse_config(
                Path(temporary),
                self.config("showcase_align"),
            )
        self.assertEqual(420.0, parsed["segments"][0]["duration_sec"])
        self.assertEqual("showcase_align", parsed["segments"][0]["acceptance"])

    def test_rejects_song_without_explicit_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(
                SystemExit,
                "requires showcase_align or instrumental_plan",
            ):
                LONGFORM.parse_config(Path(temporary), self.config(None))

    def test_narration_mapping_is_per_segment_and_free_may_be_empty(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            missing_mapping = self.config("showcase_align")
            missing_mapping["segments"][0].pop("narration_wavs")
            with self.assertRaisesRegex(SystemExit, "explicit array"):
                LONGFORM.parse_config(project, missing_mapping)

            stale_top_level = self.config("showcase_align")
            stale_top_level["narration_wavs"] = ["voice/orphan.wav"]
            with self.assertRaisesRegex(SystemExit, "top-level narration_wavs"):
                LONGFORM.parse_config(project, stale_top_level)

            free = self.config("showcase_align")
            free["segments"][0]["role"] = "free"
            free["segments"][0]["acceptance"] = "not_applicable"
            free["segments"][0]["narration_wavs"] = []
            parsed = LONGFORM.parse_config(project, free)
            self.assertEqual([], parsed["segments"][0]["narration_wavs"])

    def test_narration_sidecar_mismatches_fail_before_media_probe(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary).resolve()
            parsed = self.prepare_inputs(project)
            selection = json.loads(parsed["selection"].read_text(encoding="utf-8"))
            narration = parsed["segments"][0]["narration_wavs"][0]
            sidecar_path = Path(f"{narration}.tts.json")
            valid = {
                "selection": selection,
                "resolved_voice_id": "CV002",
                "output_sha256": LONGFORM.sha256_file(narration),
            }
            cases = (
                (
                    "selection",
                    {**valid, "selection": {**selection, "marker": "another-project"}},
                    "selection does not match",
                ),
                (
                    "resolved voice",
                    {**valid, "resolved_voice_id": "CV003"},
                    "resolved voice does not match",
                ),
                (
                    "output hash",
                    {**valid, "output_sha256": "0" * 64},
                    "output hash does not match",
                ),
            )
            for label, sidecar, message in cases:
                with self.subTest(mismatch=label):
                    sidecar_path.write_text(json.dumps(sidecar), encoding="utf-8")
                    with self.assertRaisesRegex(SystemExit, message):
                        LONGFORM.validate_inputs(parsed, project)

    def test_audio_segment_sha_mismatch_fails_before_probe(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary).resolve()
            parsed = self.prepare_inputs(project)
            parsed["segments"][0]["audio_segment_sha256"] = "0" * 64
            with (
                mock.patch.object(LONGFORM, "probe") as probe,
                self.assertRaisesRegex(SystemExit, "audio_segment SHA-256 mismatch"),
            ):
                LONGFORM.validate_inputs(parsed, project)
            probe.assert_not_called()

    def test_short_audio_segment_is_not_silently_padded(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary).resolve()
            parsed = self.prepare_inputs(project)
            audio_segment = parsed["segments"][0]["audio_segment"]

            def fake_duration(path: Path) -> float:
                return 1.0 if path == audio_segment else 500.0

            with (
                mock.patch.object(
                    LONGFORM,
                    "probe",
                    return_value={"streams": [{"width": 1080, "height": 1920}]},
                ),
                mock.patch.object(LONGFORM, "media_duration", side_effect=fake_duration),
                self.assertRaisesRegex(SystemExit, "instead of padding"),
            ):
                LONGFORM.validate_inputs(parsed, project)

    def test_empty_project_voice_id_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary).resolve()
            parsed = self.prepare_inputs(project)
            parsed["selection"].write_text(
                json.dumps({"resolved_voice_id": ""}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(SystemExit, "resolved_voice_id must be non-empty"):
                LONGFORM.validate_inputs(parsed, project)

    def test_external_narration_sidecar_symlink_is_rejected_before_read(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            project = (base / "project").resolve()
            project.mkdir()
            parsed = self.prepare_inputs(project)
            narration = parsed["segments"][0]["narration_wavs"][0]
            sidecar = Path(f"{narration}.tts.json")
            sidecar.unlink()
            outside = base / "outside-sidecar.json"
            outside.write_text("{invalid external sentinel", encoding="utf-8")
            sidecar.symlink_to(outside)

            with self.assertRaisesRegex(SystemExit, "TTS sidecar must not be a symlink"):
                LONGFORM.validate_inputs(parsed, project)
            self.assertEqual("{invalid external sentinel", outside.read_text(encoding="utf-8"))

    def test_timeline_records_segment_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary).resolve()
            parsed = self.prepare_inputs(project)
            with (
                mock.patch.object(LONGFORM, "media_duration", return_value=420.0),
                mock.patch.object(LONGFORM, "run"),
            ):
                LONGFORM.build(parsed, project)

            timeline = json.loads(parsed["outputs"]["timeline"].read_text(encoding="utf-8"))
            segment = timeline["segments"][0]
            self.assertEqual("CV002", timeline["voice_selection"]["resolved_voice_id"])
            self.assertEqual(
                parsed["segments"][0]["audio_segment_sha256"],
                segment["audio_segment_sha256"],
            )
            self.assertEqual("voice/long-song.wav", segment["narration_wavs"][0]["path"])
            self.assertEqual("CV002", segment["narration_wavs"][0]["resolved_voice_id"])

    def test_fixed_temporary_symlinks_are_rejected_before_write(self) -> None:
        targets = (
            "video/000-long-song.mp4",
            "audio/000-long-song.wav",
            "video/concat.txt",
            "audio/concat.txt",
        )
        for target_name in targets:
            with self.subTest(target=target_name), tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary)
                project = (base / "project").resolve()
                project.mkdir()
                parsed = self.prepare_inputs(project)
                target = project / "tmp" / "longform-timeline" / target_name
                target.parent.mkdir(parents=True, exist_ok=True)
                outside = base / "outside"
                outside.write_bytes(b"must remain untouched")
                target.symlink_to(outside)

                with (
                    mock.patch.object(LONGFORM, "media_duration", return_value=420.0),
                    mock.patch.object(LONGFORM, "run"),
                    self.assertRaisesRegex(SystemExit, "must not be a symlink"),
                ):
                    LONGFORM.build(parsed, project)
                self.assertEqual(b"must remain untouched", outside.read_bytes())


if __name__ == "__main__":
    unittest.main()
