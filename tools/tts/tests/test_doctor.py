from __future__ import annotations

import io
import sys
import tempfile
import unittest
import wave
from contextlib import ExitStack, redirect_stdout
from pathlib import Path
from unittest.mock import patch


TTS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TTS_ROOT))

import doctor
from voice_registry import VoiceRegistry, file_sha256


class DoctorScopeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "tts"
        self.voices_root = self.root / "voices"
        self.model_root = self.root / "model"
        self.model_root.mkdir(parents=True)

        default_reference = self._write_reference("CV002/reference.wav")
        selected_reference = self._write_reference("CV004/reference.wav")
        engine = "qwen3-tts-base-mlx"
        self.registry = VoiceRegistry(
            config={
                "default_voice_id": "CV002",
                "fallback_voice_id": "CV002",
                "qwen_base": {
                    "engine": engine,
                    "mlx_audio_version": "0.4.5",
                },
                "legacy_kokoro": {
                    "engine": "kokoro-misaki-zh",
                    "voices": ["zf_xiaoyi"],
                },
            },
            registry={
                "voices": [
                    self._voice(
                        "CV001",
                        "未使用音色",
                        "unused",
                        "CV001/reference.wav",
                        "0" * 64,
                        engine,
                    ),
                    self._voice(
                        "CV002",
                        "治愈少女",
                        "soft-healer",
                        "CV002/reference.wav",
                        file_sha256(default_reference),
                        engine,
                    ),
                    self._voice(
                        "CV004",
                        "清冷学姐",
                        "cool-senpai",
                        "CV004/reference.wav",
                        file_sha256(selected_reference),
                        engine,
                    ),
                ]
            },
        )
        self.registry.validate()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _write_reference(self, relative: str) -> Path:
        path = self.voices_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(path), "wb") as handle:
            handle.setnchannels(1)
            handle.setsampwidth(2)
            handle.setframerate(24000)
            handle.writeframes(b"\x00\x00" * 240)
        return path

    @staticmethod
    def _voice(
        voice_id: str,
        name: str,
        slug: str,
        reference_audio: str,
        reference_sha256: str,
        engine: str,
    ) -> dict:
        return {
            "id": voice_id,
            "name": name,
            "slug": slug,
            "engine": engine,
            "enabled": True,
            "aliases": [],
            "reference_audio": reference_audio,
            "reference_sha256": reference_sha256,
        }

    def run_doctor(
        self,
        argv: list[str],
        *,
        pronunciation_error: Exception | None = None,
        registry_error: Exception | None = None,
        runtime_error: Exception | None = None,
    ) -> tuple[int, str, object]:
        output = io.StringIO()
        with ExitStack() as stack:
            stack.enter_context(patch.object(doctor, "TTS_ROOT", self.root))
            stack.enter_context(
                patch.object(
                    doctor.VoiceRegistry,
                    "load",
                    return_value=self.registry,
                    side_effect=registry_error,
                )
            )
            stack.enter_context(
                patch.object(
                    doctor,
                    "resolve_runtime",
                    return_value=Path("/pinned/qwen/python"),
                    side_effect=runtime_error,
                )
            )
            stack.enter_context(
                patch.object(doctor, "probe_mlx_audio_version", return_value="0.4.5")
            )
            stack.enter_context(
                patch.object(
                    doctor,
                    "first_model_directory",
                    return_value=self.model_root,
                )
            )
            stack.enter_context(
                patch.object(
                    doctor,
                    "manifest_path",
                    return_value=self.root / "model-manifest.json",
                )
            )
            stack.enter_context(
                patch.object(
                    doctor,
                    "validate_receipt",
                    return_value={
                        "model_file_count": 3,
                        "model_total_bytes": 42,
                        "full_tree_hash_verified": True,
                    },
                )
            )
            stack.enter_context(
                patch.object(doctor, "create_full_hash_receipt", return_value={})
            )
            pronunciation = stack.enter_context(
                patch.object(
                    doctor.PronunciationPolicy,
                    "load",
                    side_effect=pronunciation_error
                    or AssertionError("mixed-script policy must stay out of this scope"),
                )
            )
            with redirect_stdout(output):
                code = doctor.main(argv)
        return code, output.getvalue(), pronunciation

    def test_default_checks_only_cv002_and_skips_mixed_script_policy(self) -> None:
        code, output, pronunciation = self.run_doctor([])

        self.assertEqual(code, 0, output)
        pronunciation.assert_not_called()
        self.assertIn("voice-assets: 1/1 references verified scope=selected ids=CV002", output)
        self.assertIn("text-normalization: SKIP", output)
        self.assertIn("TTS DOCTOR: PASS default=CV002 selected=CV002", output)
        self.assertNotIn(str(self.root), output)
        self.assertNotIn("/pinned/qwen/python", output)

    def test_explicit_voice_checks_only_exact_selected_reference(self) -> None:
        code, output, pronunciation = self.run_doctor(["--voice", "清冷学姐"])

        self.assertEqual(code, 0, output)
        pronunciation.assert_not_called()
        self.assertIn("voice-assets: 1/1 references verified scope=selected ids=CV004", output)
        self.assertIn("TTS DOCTOR: PASS default=CV002 selected=CV004", output)

    def test_full_model_hash_does_not_implicitly_expand_voice_scope(self) -> None:
        code, output, pronunciation = self.run_doctor(["--full-model-hash"])

        self.assertEqual(code, 0, output)
        pronunciation.assert_not_called()
        self.assertIn("voice-assets: 1/1 references verified scope=selected ids=CV002", output)
        self.assertNotIn("missing reference: CV001", output)

    def test_full_library_detects_unused_missing_reference(self) -> None:
        code, output, pronunciation = self.run_doctor(["--full-library"])

        self.assertEqual(code, 1, output)
        pronunciation.assert_not_called()
        self.assertIn("voice-assets: 2/3 references verified scope=full-library", output)
        self.assertIn("TTS DOCTOR: FAIL", output)
        self.assertIn("missing reference: CV001", output)

    def test_mixed_script_policy_is_checked_only_when_requested(self) -> None:
        code, output, pronunciation = self.run_doctor(
            ["--check-mixed-script"],
            pronunciation_error=ValueError("synthetic broken policy"),
        )

        self.assertEqual(code, 1, output)
        pronunciation.assert_called_once_with()
        self.assertIn("invalid pronunciation policy [invalid-config]", output)
        self.assertNotIn("synthetic broken policy", output)

    def test_unknown_voice_is_not_silently_fallbacked(self) -> None:
        code, output, pronunciation = self.run_doctor(["--voice", "CV999"])

        self.assertEqual(code, 1, output)
        pronunciation.assert_not_called()
        self.assertIn("must exactly match an enabled CV voice", output)
        self.assertNotIn("TTS DOCTOR: PASS", output)

    def test_runtime_exception_payload_is_not_printed(self) -> None:
        leaked = "/Users/private/model token=super-secret"
        code, output, _pronunciation = self.run_doctor(
            [], runtime_error=OSError(leaked)
        )

        self.assertEqual(code, 1, output)
        self.assertIn("runtime verification failed [io]", output)
        self.assertNotIn(leaked, output)
        self.assertNotIn("/Users", output)
        self.assertNotIn("super-secret", output)

    def test_registry_exception_payload_is_not_printed(self) -> None:
        leaked = "/private/var/secret-registry.json api_key=super-secret"
        code, output, _pronunciation = self.run_doctor(
            [], registry_error=ValueError(leaked)
        )

        self.assertEqual(code, 1, output)
        self.assertIn("cannot load TTS config/registry [invalid-config]", output)
        self.assertNotIn("/private/var", output)
        self.assertNotIn("super-secret", output)

    def test_unknown_voice_value_is_not_echoed(self) -> None:
        leaked = "/Users/private/CV999-token-super-secret"
        code, output, _pronunciation = self.run_doctor(["--voice", leaked])

        self.assertEqual(code, 1, output)
        self.assertIn("must exactly match an enabled CV voice", output)
        self.assertNotIn(leaked, output)

    def test_cli_suppresses_unexpected_exception_payload(self) -> None:
        output = io.StringIO()
        leaked = "/private/var/model-receipt.json token=super-secret"
        with patch.object(doctor, "main", side_effect=RuntimeError(leaked)):
            with redirect_stdout(output):
                code = doctor.cli([])

        self.assertEqual(1, code)
        self.assertIn("unexpected doctor failure [unexpected]", output.getvalue())
        self.assertNotIn(leaked, output.getvalue())


if __name__ == "__main__":
    unittest.main()
