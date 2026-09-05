from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch


TTS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TTS_ROOT))

from model_provenance import canonical_sha256
from narrate import load_selection_file
from qwen_contract import (
    _selection_contract_errors,
    derived_seed,
    fingerprint,
    fingerprint_inputs,
)
from text_normalizer import PronunciationPolicy, normalize_tts_text
from verify_standard_pool import normalized_text
from verify_voice_usage import VerificationResult, sidecar_input_text, verify_project_voice
from voice_registry import (
    VoiceRegistry,
    file_sha256,
    resolve_selector,
    resolve_task_prompt,
    text_sha256,
)


class VoiceResolverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = VoiceRegistry.load()

    def assert_voice(self, prompt: str, voice_id: str, reason: str) -> None:
        value = resolve_task_prompt(self.registry, prompt)
        self.assertEqual(value["resolved_voice_id"], voice_id)
        self.assertEqual(value["resolution_reason"], reason)

    def assert_random_voice(
        self,
        prompt: str,
        reason: str = "fallback_model_unavailable",
        selected_voice_id: str = "CV009",
    ) -> None:
        with patch(
            "voice_registry.secrets.choice",
            return_value=self.registry.by_id(selected_voice_id),
        ):
            value = resolve_task_prompt(self.registry, prompt)
        self.assertEqual(value["resolved_voice_id"], selected_voice_id)
        self.assertEqual(value["resolution_reason"], reason)
        self.assertEqual(value["selection_mode"], "random_pool")
        self.assertEqual(value["matched_by"], "random_pool")
        self.assertEqual(value["candidate_voice_ids"], self.registry.random_pool_ids)
        self.assertEqual(value["model_decision_confidence"], "low")
        self.assertTrue(value["model_decision_reason"])

    def test_standard_pool_asr_comparison_folds_traditional_chinese(self) -> None:
        self.assertEqual(
            normalized_text("這是標準配音生產煉路穩定性檢查。"),
            normalized_text("这是标准配音生产链路稳定性检查。"),
        )

    def test_default_uses_random_standard_pool_only_when_model_is_unavailable(self) -> None:
        self.assert_random_voice("做一期新的华语歌曲盘点视频")

    def test_model_decides_by_project_emotion(self) -> None:
        value = resolve_task_prompt(
            self.registry,
            "做一期沉重的时代人物纪实。",
            model_choice="深沉纪实男声",
            model_reason="主题强调时代重量与人物命运，深沉纪实表达最匹配。",
            model_confidence="high",
        )
        self.assertEqual(value["resolved_voice_id"], "CV012")
        self.assertEqual(value["resolution_reason"], "model_emotion_match")
        self.assertEqual(value["selection_mode"], "model_decision")
        self.assertEqual(value["matched_by"], "model_decision")
        self.assertEqual(value["candidate_voice_ids"], self.registry.decision_pool_ids)
        self.assertEqual(value["model_decision_confidence"], "high")
        self.assertIn("时代重量", value["model_decision_reason"])
        self.assertFalse(value["fallback"])
        self.assertEqual(
            [],
            _selection_contract_errors(
                value,
                qwen=self.registry.config["qwen_base"],
                voice_id="CV012",
                voice_name="深沉纪实男声",
            ),
        )

    def test_new_expansion_voices_use_their_matching_reference_transcript(self) -> None:
        legacy_text = self.registry.registry["reference_text"]
        expansion_text = "你好，这是一个全新的原创声音。请听听它是否自然、清楚，也适合长时间讲故事。"
        for voice_id in (
            "CV009",
            "CV010",
            "CV011",
            "CV012",
            "CV013",
            "CV014",
            "CV015",
            "CV016",
            "CV017",
        ):
            with self.subTest(voice_id=voice_id):
                voice = self.registry.by_id(voice_id)
                self.assertIsNotNone(voice)
                self.assertEqual(expansion_text, self.registry.reference_text_for(voice))
                self.assertNotEqual(legacy_text, self.registry.reference_text_for(voice))
        self.assertEqual(
            legacy_text,
            self.registry.reference_text_for(self.registry.by_id("CV002")),
        )

    def test_low_confidence_model_decision_randomly_falls_back(self) -> None:
        with patch(
            "voice_registry.secrets.choice",
            return_value=self.registry.by_id("CV013"),
        ):
            value = resolve_task_prompt(
                self.registry,
                "做一期还没确定主题的内容。",
                model_choice="柔和青年男声",
                model_reason="主题和情绪信息不足，无法可靠判断。",
                model_confidence="low",
            )
        self.assertEqual(value["resolved_voice_id"], "CV013")
        self.assertEqual(value["resolution_reason"], "fallback_model_unavailable")
        self.assertEqual(value["selection_mode"], "random_pool")
        self.assertEqual(value["model_decision_confidence"], "low")
        self.assertTrue(value["fallback"])
        self.assertEqual(
            [],
            _selection_contract_errors(
                value,
                qwen=self.registry.config["qwen_base"],
                voice_id="CV013",
                voice_name="柔和青年男声",
            ),
        )

    def test_explicit_voice_overrides_model_decision(self) -> None:
        value = resolve_task_prompt(
            self.registry,
            "配音：清冷学姐",
            model_choice="清亮校园女声",
            model_reason="作品有青春气息。",
            model_confidence="high",
        )
        self.assertEqual(value["resolved_voice_id"], "CV004")
        self.assertEqual(value["selection_mode"], "explicit")
        self.assertIsNone(value["model_decision_reason"])
        self.assertIsNone(value["model_decision_confidence"])

    def test_structured_name(self) -> None:
        self.assert_voice("主题：经典前奏\n配音：治愈少女", "CV002", "explicit_prompt_match")

    def test_structured_id(self) -> None:
        self.assert_voice("配音：CV004", "CV004", "explicit_prompt_match")

    def test_imperative_alias(self) -> None:
        self.assert_voice("这期用元气萌妹来讲。", "CV001", "explicit_prompt_match")

    def test_unknown_falls_back(self) -> None:
        self.assert_random_voice("配音：CV999")
        self.assert_random_voice("请用可爱女声配音")
        self.assert_random_voice("配音：默认配音")

    def test_ambiguous_falls_back(self) -> None:
        self.assert_random_voice(
            "配音：元气萌妹或清冷学姐都可以",
        )

    def test_topic_words_do_not_select_voice(self) -> None:
        self.assert_random_voice("盘点热血少年动漫名场面")

    def test_negative_voice_is_ignored(self) -> None:
        self.assert_voice(
            "不要用热血少年配音，请用清冷学姐配音",
            "CV004",
            "explicit_prompt_match",
        )

    def test_structured_negative_id_uses_default(self) -> None:
        self.assert_random_voice("配音：不要用 CV004")

    def test_body_negative_id_uses_default_without_bare_id_bypass(self) -> None:
        self.assert_random_voice("这期不要使用 CV004")

    def test_positive_replacement_after_negative_id_still_wins(self) -> None:
        self.assert_voice(
            "不要使用 CV004，请改用 CV003 配音",
            "CV003",
            "explicit_prompt_match",
        )
        self.assert_voice(
            "不要使用 CV004 请改用 CV003 配音",
            "CV003",
            "explicit_prompt_match",
        )
        self.assert_voice(
            "不要用 CV004 而是 CV003",
            "CV003",
            "explicit_prompt_match",
        )

    def test_all_supported_negative_forms_fall_back_without_selecting(self) -> None:
        for prompt in (
            "配音：不使用 CV004",
            "配音：请勿使用 CV004",
            "配音：不是 CV004",
            "配音：不能用 CV004",
            "配音：不可用 CV004",
            "配音：避免 CV004",
            "配音：除了 CV004",
            "配音：CV004 除外",
            "配音：CV004 不用",
            "配音：CV004 不能用",
            "配音：CV004 不行",
            "配音：我不想用 CV004",
            "配音：拒绝使用 CV004",
            "配音：不考虑 CV004",
            "配音：CV004 不考虑",
            "配音：CV004 不要了",
            "配音：清冷学姐不考虑",
            "配音：不要用 CV004，CV003 也不要",
        ):
            with self.subTest(prompt=prompt):
                self.assert_random_voice(prompt)

    def test_negative_alias_does_not_override_positive_replacement(self) -> None:
        self.assert_voice(
            "不要用热血少年，改用清冷学姐配音",
            "CV004",
            "explicit_prompt_match",
        )

    def test_common_positive_replacements_after_negation_are_unambiguous(self) -> None:
        for prompt in (
            "不用 CV004，就用 CV003",
            "CV004 不行，选择 CV003",
            "我不想用 CV004，请改用 CV003 配音",
            "拒绝使用 CV004，使用 CV003 配音",
            "不考虑 CV004，选择 CV003",
            "CV004 不考虑，选择 CV003",
            "CV004 不要了，改用 CV003 配音",
        ):
            with self.subTest(prompt=prompt):
                self.assert_voice(prompt, "CV003", "explicit_prompt_match")
        self.assert_random_voice("不用 CV004，CV003 也不要")

    def test_multiple_tokens_for_same_voice_are_not_ambiguous(self) -> None:
        self.assert_voice("配音：CV002（治愈少女）", "CV002", "explicit_prompt_match")

    def test_explicit_selector_is_exact(self) -> None:
        self.assertEqual(resolve_selector(self.registry, "soft_healer")["resolved_voice_id"], "CV002")
        with patch(
            "voice_registry.secrets.choice", return_value=self.registry.by_id("CV003")
        ):
            unknown = resolve_selector(self.registry, "CV999")
            empty = resolve_selector(self.registry, "")
        self.assertEqual(unknown["resolved_voice_id"], "CV003")
        self.assertEqual(unknown["selection_mode"], "random_pool")
        self.assertEqual(
            resolve_selector(self.registry, "zm_yunxi")["resolved_voice_id"],
            "kokoro:zm_yunxi",
        )
        self.assertEqual(empty["resolved_voice_id"], "CV003")

    def test_cli_resolve_only(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(TTS_ROOT / "narrate.py"),
                "--resolve-only",
                "--voice",
                "不存在的声音",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        value = json.loads(completed.stdout)
        self.assertIn(value["resolved_voice_id"], self.registry.random_pool_ids)
        self.assertEqual(value["selection_mode"], "random_pool")
        self.assertEqual(value["candidate_voice_ids"], self.registry.random_pool_ids)
        self.assertTrue(value["fallback"])

    def test_pre_random_pool_selection_hash_pair_remains_reusable(self) -> None:
        compatible = self.registry.config["compatible_selection_hashes"][0]
        value = {
            "schema_version": "1.0.0",
            "resolved_voice_id": "CV002",
            "config_sha256": compatible["config_sha256"],
            "registry_sha256": compatible["registry_sha256"],
        }
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "voice-selection.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            self.assertEqual(load_selection_file(path, self.registry), value)

        stale = {**value, "config_sha256": "0" * 64}
        self.assertFalse(self.registry.accepts_selection_hashes(stale))

    def test_pre_refresh_standard_pool_selection_remains_reusable(self) -> None:
        compatible = self.registry.config["compatible_selection_hashes"][-1]
        value = {
            "schema_version": "1.2.0",
            "resolved_voice_id": "CV013",
            "config_sha256": compatible["config_sha256"],
            "registry_sha256": compatible["registry_sha256"],
        }
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "voice-selection.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            self.assertEqual(load_selection_file(path, self.registry), value)


class VoiceAssetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = VoiceRegistry.load()

    def test_ids_are_stable_and_random_pool_exists(self) -> None:
        self.assertEqual(
            [voice["id"] for voice in self.registry.voices],
            [f"CV{i:03d}" for i in range(1, 18)],
        )
        self.assertEqual(self.registry.preflight_id, "CV002")
        expected_pool = [
            "CV012",
            "CV013",
            "CV014",
            "CV015",
            "CV016",
            "CV002",
            "CV003",
            "CV008",
            "CV009",
            "CV017",
        ]
        self.assertEqual(self.registry.decision_pool_ids, expected_pool)
        self.assertEqual(self.registry.random_pool_ids, expected_pool)
        groups = [voice["group"] for voice in self.registry.decision_pool]
        self.assertEqual(groups.count("female"), 5)
        self.assertEqual(groups.count("male"), 5)
        self.assertTrue(
            all(voice.get("decision_profile") for voice in self.registry.decision_pool)
        )

    def test_reference_assets(self) -> None:
        root = TTS_ROOT / "voices"
        for voice in self.registry.voices:
            reference = root / voice["reference_audio"]
            self.assertTrue(reference.is_file(), reference)
            self.assertEqual(file_sha256(reference), voice["reference_sha256"])
            with wave.open(str(reference), "rb") as handle:
                self.assertEqual(handle.getnchannels(), 1)
                self.assertEqual(handle.getframerate(), 24000)
                self.assertGreater(handle.getnframes(), 24000)
            for example in voice["examples"].values():
                self.assertTrue((root / example).is_file(), example)


class VoiceGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = VoiceRegistry.load()

    def current_validation(self, *, receipt_sha256: str = "b" * 64) -> dict:
        qwen = self.registry.config["qwen_base"]
        manifest_path = TTS_ROOT / qwen["model_file_manifest"]
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        claim = {
            "portable_claim_kind": "qwen-model-portable-claim-v1",
            "verification_kind": "qwen-full-model-hash-receipt-v1",
            "model_id": qwen["model_id"],
            "model_revision": qwen["model_revision"],
            "qwen_config_sha256": canonical_sha256(qwen),
            "manifest_sha256": file_sha256(manifest_path),
            "verified_model_tree_sha256": qwen["model_tree_sha256"],
            "model_file_count": manifest["file_count"],
            "model_total_bytes": manifest["total_bytes"],
            "mlx_audio_version": qwen["mlx_audio_version"],
        }
        return {
            **claim,
            "portable_claim_sha256": canonical_sha256(claim),
            "receipt_sha256": receipt_sha256,
            "full_tree_hash_verified": True,
        }

    def run_gate(
        self,
        project: Path,
        selection_path: Path,
        *,
        allow_legacy_qwen_sidecars: bool = False,
        validation: dict | None = None,
    ) -> VerificationResult:
        return verify_project_voice(
            project,
            selection_path,
            registry=self.registry,
            current_model_validation=validation or self.current_validation(),
            allow_legacy_qwen_sidecars=allow_legacy_qwen_sidecars,
        )

    def create_project(
        self,
        project: Path,
        *,
        legacy_absolute_output: bool = False,
        normalized: bool = False,
    ) -> tuple[Path, Path]:
        selection = resolve_selector(self.registry, "CV002")
        selection_path = project / "voice-selection.json"
        selection_path.write_text(
            json.dumps(selection, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        output = project / "narration" / "intro.wav"
        output.parent.mkdir(parents=True)
        with wave.open(str(output), "wb") as handle:
            handle.setnchannels(1)
            handle.setsampwidth(2)
            handle.setframerate(24000)
            handle.writeframes(b"\0\0" * 2400)
        voice = self.registry.by_id("CV002")
        qwen = self.registry.config["qwen_base"]
        model_validation = self.current_validation(receipt_sha256="a" * 64)
        if normalized:
            normalization_result = normalize_tts_text(
                "今天重听BEYOND。", policy=PronunciationPolicy.load()
            )
            text = normalization_result.normalized_text
            item = {
                "id": "intro",
                "text": text,
                "source_text": normalization_result.source_text,
                "text_normalization": normalization_result.metadata(),
            }
        else:
            text = "今天盘点五首作品。"
            item = {"id": "intro", "text": text}
        language = qwen["language"]
        speed = 1.0
        fp_inputs = fingerprint_inputs(
            qwen=qwen,
            selection=selection,
            voice_id="CV002",
            reference_sha256=voice["reference_sha256"],
            reference_text=self.registry.registry["reference_text"],
            item=item,
            language=language,
            speed=speed,
        )
        with wave.open(str(output), "rb") as handle:
            frames = handle.getnframes()
            sample_rate = handle.getframerate()
            wav = {
                "channels": handle.getnchannels(),
                "sample_rate_hz": sample_rate,
                "sample_width_bytes": handle.getsampwidth(),
                "frames": frames,
                "duration_seconds": frames / sample_rate,
            }
        sidecar = {
            "schema_version": "1.1.0" if normalized else "1.0.0",
            "item_id": "intro",
            "text": text,
            "text_sha256": text_sha256(text),
            "selection": selection,
            "resolved_voice_id": "CV002",
            "engine": qwen["engine"],
            "model_id": qwen["model_id"],
            "model_revision": qwen["model_revision"],
            "model_tree_sha256": qwen["model_tree_sha256"],
            "model_validation": model_validation,
            "reference_audio": f"voices/{voice['reference_audio']}",
            "reference_sha256": voice["reference_sha256"],
            "language": language,
            "speed": speed,
            "seed": derived_seed(qwen["generation"]["seed"], "CV002", text, language),
            "generation_seconds": 0.1,
            "model_load_seconds": 0.2,
            "model_metrics": [
                {
                    "processing_seconds": 0.1,
                    "peak_memory_gb": 0.25,
                    "token_count": 10,
                }
            ],
            "fingerprint": fingerprint(fp_inputs),
            "fingerprint_inputs": fp_inputs,
            "output": str(output) if legacy_absolute_output else output.name,
            "output_sha256": file_sha256(output),
            "wav": wav,
        }
        if normalized:
            sidecar.update(
                {
                    "source_text": item["source_text"],
                    "normalized_text": text,
                    "text_normalization": item["text_normalization"],
                }
            )
        sidecar_path = output.with_suffix(".wav.tts.json")
        sidecar_path.write_text(
            json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        return selection_path, sidecar_path

    def test_gate_validates_full_provenance_and_wav(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary).resolve()
            selection_path, _ = self.create_project(project)
            result = self.run_gate(project, selection_path)
            self.assertTrue(result.ok, result.errors)
            self.assertEqual(result.provenance_modes, ("qwen_portable_current",))
            self.assertEqual(result.sidecars[0].input_text, "今天盘点五首作品。")
            self.assertAlmostEqual(result.sidecars[0].duration_seconds, 0.1)

    def test_gate_accepts_worker_normalized_1_1_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary).resolve()
            selection_path, _ = self.create_project(project, normalized=True)
            result = self.run_gate(project, selection_path)
            self.assertTrue(result.ok, result.errors)
            self.assertEqual(result.sidecars[0].input_text, "今天重听BEYOND。")

    def test_gate_rejects_arbitrary_wav_with_handwritten_minimal_sidecar(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary).resolve()
            selection_path, sidecar_path = self.create_project(project)
            sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
            keep = {
                "selection",
                "resolved_voice_id",
                "engine",
                "model_id",
                "model_revision",
                "model_tree_sha256",
                "model_validation",
                "reference_sha256",
                "text",
                "output",
                "output_sha256",
            }
            sidecar = {key: value for key, value in sidecar.items() if key in keep}
            sidecar_path.write_text(json.dumps(sidecar), encoding="utf-8")
            result = self.run_gate(project, selection_path)
            self.assertFalse(result.ok)
            self.assertTrue(
                any("Qwen sidecar contract" in item for item in result.errors),
                result.errors,
            )

    def test_gate_rejects_qwen_contract_tampering_and_extra_derived_fields(self) -> None:
        mutations = {
            "fingerprint": lambda value: value.__setitem__("fingerprint", "0" * 64),
            "fingerprint generation": lambda value: value["fingerprint_inputs"][
                "generation"
            ].__setitem__("temperature", 0.1),
            "seed": lambda value: value.__setitem__("seed", value["seed"] + 1),
            "text sha": lambda value: value.__setitem__("text_sha256", "0" * 64),
            "wav metadata": lambda value: value["wav"].__setitem__(
                "frames", value["wav"]["frames"] + 1
            ),
            "language": lambda value: value.__setitem__("language", "English"),
            "speed type": lambda value: value.__setitem__("speed", 1),
            "extra derived field": lambda value: value.__setitem__(
                "claimed_voice_embedding_sha256", "0" * 64
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                project = Path(temporary).resolve()
                selection_path, sidecar_path = self.create_project(project)
                sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
                mutate(sidecar)
                sidecar_path.write_text(json.dumps(sidecar), encoding="utf-8")
                result = self.run_gate(project, selection_path)
                self.assertFalse(result.ok, result.errors)
                self.assertTrue(
                    any("Qwen sidecar contract" in item for item in result.errors),
                    result.errors,
                )

    def test_gate_rejects_tampered_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary).resolve()
            selection_path, sidecar_path = self.create_project(project)
            sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
            sidecar["reference_sha256"] = "0" * 64
            sidecar_path.write_text(json.dumps(sidecar), encoding="utf-8")
            result = self.run_gate(project, selection_path)
            self.assertFalse(result.ok)
            self.assertTrue(any("wrong reference-audio hash" in item for item in result.errors))

    def test_gate_rejects_generation_that_hits_max_tokens(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary).resolve()
            selection_path, sidecar_path = self.create_project(project)
            sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
            sidecar["model_metrics"][0]["token_count"] = self.registry.config[
                "qwen_base"
            ]["generation"]["max_tokens"]
            sidecar_path.write_text(json.dumps(sidecar), encoding="utf-8")
            result = self.run_gate(project, selection_path)
            self.assertFalse(result.ok)
            self.assertTrue(
                any("reached max_tokens" in item for item in result.errors),
                result.errors,
            )

    def test_gate_rejects_new_relative_sidecar_without_model_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary).resolve()
            selection_path, sidecar_path = self.create_project(project)
            sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
            sidecar.pop("model_validation")
            sidecar_path.write_text(json.dumps(sidecar), encoding="utf-8")
            result = self.run_gate(project, selection_path)
            self.assertFalse(result.ok)
            self.assertTrue(any("lacks current model validation" in item for item in result.errors))

    def test_gate_accepts_legacy_absolute_output_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary).resolve()
            selection_path, sidecar_path = self.create_project(
                project, legacy_absolute_output=True
            )
            sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
            sidecar.pop("model_validation")
            sidecar_path.write_text(
                json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            result = self.run_gate(
                project,
                selection_path,
                allow_legacy_qwen_sidecars=True,
            )
            self.assertTrue(result.ok, result.errors)
            self.assertEqual(result.provenance_modes, ("legacy_explicit",))
            self.assertTrue(result.warnings)

    def test_relative_output_path_survives_project_move(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary).resolve() / "source"
            source.mkdir()
            self.create_project(source)
            moved = source.parent / "moved"
            shutil.copytree(source, moved)
            result = self.run_gate(moved, moved / "voice-selection.json")
            self.assertTrue(result.ok, result.errors)

    def test_raw_receipt_hash_is_audit_only_when_portable_claim_matches(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary).resolve()
            selection_path, sidecar_path = self.create_project(project)
            sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
            self.assertNotEqual(
                sidecar["model_validation"]["receipt_sha256"],
                self.current_validation()["receipt_sha256"],
            )
            result = self.run_gate(project, selection_path)
            self.assertTrue(result.ok, result.errors)

    def test_portable_claim_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary).resolve()
            selection_path, sidecar_path = self.create_project(project)
            sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
            sidecar["model_validation"]["qwen_config_sha256"] = "0" * 64
            sidecar_path.write_text(json.dumps(sidecar), encoding="utf-8")
            result = self.run_gate(project, selection_path)
            self.assertFalse(result.ok)
            self.assertTrue(any("qwen_config_sha256" in item for item in result.errors))

    def test_external_selection_and_sidecar_symlinks_fail_before_read(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            project = base / "project"
            project.mkdir()
            selection_path, sidecar_path = self.create_project(project)
            outside_selection = base / "outside-selection.json"
            shutil.copy2(selection_path, outside_selection)
            outside_sidecar = base / "outside-sidecar.json"
            shutil.copy2(sidecar_path, outside_sidecar)
            self.assertFalse(self.run_gate(project, outside_selection).ok)
            sidecar_path.unlink()
            sidecar_path.symlink_to(outside_sidecar)
            result = self.run_gate(project, selection_path)
            self.assertFalse(result.ok)
            self.assertTrue(any("must not be a symlink" in item for item in result.errors))

    def test_output_symlink_outside_project_fails_before_read(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            project = base / "project"
            project.mkdir()
            selection_path, sidecar_path = self.create_project(project)
            output = sidecar_path.with_suffix("").with_suffix("")
            outside = base / "outside.wav"
            output.replace(outside)
            output.symlink_to(outside)
            result = self.run_gate(project, selection_path)
            self.assertFalse(result.ok)
            self.assertTrue(any("must not be a symlink" in item for item in result.errors))

    def test_canonical_input_text_prefers_source_text(self) -> None:
        self.assertEqual(
            sidecar_input_text({"source_text": "BEYOND 的作品", "text": "Beyond 的作品"}),
            "BEYOND 的作品",
        )


class WorkspacePolicyTests(unittest.TestCase):
    def test_decision_pool_comes_from_registry(self) -> None:
        repo = TTS_ROOT.parents[1]
        registry = VoiceRegistry.load()

        self.assertEqual("CV002", registry.config["preflight_voice_id"])
        expected_pool = [
            "CV012",
            "CV013",
            "CV014",
            "CV015",
            "CV016",
            "CV002",
            "CV003",
            "CV008",
            "CV009",
            "CV017",
        ]
        self.assertEqual(expected_pool, registry.config["decision_voice_pool"])
        self.assertEqual(expected_pool, registry.config["random_voice_pool"])
        self.assertEqual(
            "model_emotion_decision", registry.config["selection_policy"]["default"]
        )
        self.assertIn(
            resolve_task_prompt(registry, "配音：CV999")["resolved_voice_id"],
            registry.random_pool_ids,
        )
    def test_shared_video_template_cannot_bypass_dispatcher(self) -> None:
        repo = TTS_ROOT.parents[1]
        text = (repo / "tools" / "video" / "narrate_segments.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("from kokoro import", text)
        self.assertNotIn("KPipeline(", text)
        self.assertNotRegex(text, r"(?m)^\s*VOICE\s*=")
        self.assertIn("voice-selection.json", text)

    def test_formal_listen_page_has_all_audio(self) -> None:
        from collections import Counter
        import re

        page = TTS_ROOT / "voices" / "listen.html"
        text = page.read_text(encoding="utf-8")
        references = re.findall(r'<audio[^>]+src="([^"]+)"', text)
        registry = json.loads((TTS_ROOT / "voices" / "registry.json").read_text())
        config = json.loads((TTS_ROOT / "config.json").read_text())
        kokoro_count = len(list((TTS_ROOT / "voices" / "baselines" / "kokoro").glob("*.wav")))
        self.assertEqual(len(references), len(registry["voices"]) * 3 + kokoro_count)
        self.assertFalse([value for value in references if not (page.parent / value).is_file()])

        current_section = text.split('<details class="archive">', 1)[0]
        current_ids = re.findall(r"<h3>(CV\d{3}) ·", current_section)
        self.assertEqual(
            Counter(current_ids),
            Counter({voice_id: 3 for voice_id in config["decision_voice_pool"]}),
        )

    def test_research_was_removed_from_sandbox(self) -> None:
        repo = TTS_ROOT.parents[1]
        self.assertFalse((repo / "sandbox" / "tts-character-voice-lab").exists())
        self.assertTrue((TTS_ROOT / "research" / "qwen-character-voice-lab").is_dir())




if __name__ == "__main__":
    unittest.main()
