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
from qwen_contract import derived_seed, fingerprint, fingerprint_inputs
from text_normalizer import PronunciationPolicy, normalize_tts_text
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
        self, prompt: str, reason: str, selected_voice_id: str = "CV005"
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

    def test_default_uses_random_female_pool(self) -> None:
        self.assert_random_voice("做一期新的华语歌曲盘点视频", "default_no_request")

    def test_structured_name(self) -> None:
        self.assert_voice("主题：经典前奏\n配音：治愈少女", "CV002", "explicit_prompt_match")

    def test_structured_id(self) -> None:
        self.assert_voice("配音：CV004", "CV004", "explicit_prompt_match")

    def test_imperative_alias(self) -> None:
        self.assert_voice("这期用元气萌妹来讲。", "CV001", "explicit_prompt_match")

    def test_unknown_falls_back(self) -> None:
        self.assert_random_voice("配音：CV999", "fallback_unmatched_prompt")
        self.assert_random_voice("请用可爱女声配音", "fallback_unmatched_prompt")
        self.assert_random_voice("配音：默认配音", "fallback_unmatched_prompt")

    def test_ambiguous_falls_back(self) -> None:
        self.assert_random_voice(
            "配音：元气萌妹或清冷学姐都可以",
            "fallback_ambiguous_prompt",
        )

    def test_topic_words_do_not_select_voice(self) -> None:
        self.assert_random_voice("盘点热血少年动漫名场面", "default_no_request")

    def test_negative_voice_is_ignored(self) -> None:
        self.assert_voice(
            "不要用热血少年配音，请用清冷学姐配音",
            "CV004",
            "explicit_prompt_match",
        )

    def test_structured_negative_id_uses_default(self) -> None:
        self.assert_random_voice("配音：不要用 CV004", "default_no_request")

    def test_body_negative_id_uses_default_without_bare_id_bypass(self) -> None:
        self.assert_random_voice("这期不要使用 CV004", "default_no_request")

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
                self.assert_random_voice(prompt, "default_no_request")

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
        self.assert_random_voice("不用 CV004，CV003 也不要", "default_no_request")

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
        value = {
            "schema_version": "1.0.0",
            "resolved_voice_id": "CV002",
            **self.registry.config["compatible_selection_hashes"][0],
        }
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "voice-selection.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            self.assertEqual(load_selection_file(path, self.registry), value)

        stale = {**value, "config_sha256": "0" * 64}
        self.assertFalse(self.registry.accepts_selection_hashes(stale))


class VoiceAssetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = VoiceRegistry.load()

    def test_ids_are_stable_and_random_pool_exists(self) -> None:
        self.assertEqual([voice["id"] for voice in self.registry.voices], [f"CV{i:03d}" for i in range(1, 9)])
        self.assertEqual(self.registry.preflight_id, "CV002")
        self.assertEqual(
            self.registry.random_pool_ids,
            ["CV001", "CV002", "CV003", "CV004", "CV005", "CV008"],
        )
        self.assertTrue(all(voice["group"] == "female" for voice in self.registry.random_pool))

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
    def test_random_pool_comes_from_registry_and_claude_delegates_to_agents(self) -> None:
        repo = TTS_ROOT.parents[1]
        registry = VoiceRegistry.load()
        agents = (repo / "AGENTS.md").read_text(encoding="utf-8")
        claude = (repo / "CLAUDE.md").read_text(encoding="utf-8")

        self.assertEqual("CV002", registry.config["preflight_voice_id"])
        self.assertEqual(
            ["CV001", "CV002", "CV003", "CV004", "CV005", "CV008"],
            registry.config["random_voice_pool"],
        )
        self.assertIn(
            resolve_task_prompt(registry, "配音：CV999")["resolved_voice_id"],
            registry.random_pool_ids,
        )
        self.assertIn("single top-level source of agent instructions", agents)
        self.assertIn("CV002", agents)
        self.assertIn("CV008", agents)

        for reference in (
            "[`AGENTS.md`](AGENTS.md)",
            "[`CONVENTIONS.md`](CONVENTIONS.md)",
            "[`tools/video/README.md`](tools/video/README.md)",
        ):
            self.assertIn(reference, claude)
        self.assertNotIn("CV002", claude)
        self.assertNotIn("治愈少女", claude)
        self.assertNotIn("BEYOND", claude)

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
        import re

        page = TTS_ROOT / "voices" / "listen.html"
        text = page.read_text(encoding="utf-8")
        references = re.findall(r'<audio[^>]+src="([^"]+)"', text)
        self.assertEqual(len(references), 32)
        self.assertFalse([value for value in references if not (page.parent / value).is_file()])

    def test_research_was_removed_from_sandbox(self) -> None:
        repo = TTS_ROOT.parents[1]
        self.assertFalse((repo / "sandbox" / "tts-character-voice-lab").exists())
        self.assertTrue((TTS_ROOT / "research" / "qwen-character-voice-lab").is_dir())

    def test_new_video_constraints_are_top_level(self) -> None:
        repo = TTS_ROOT.parents[1]
        agents = (repo / "AGENTS.md").read_text(encoding="utf-8")
        for phrase in (
            "翻唱版本必须匹配",
            "禁用“接下来”",
            "完整乐句",
            "封面排版与安全区",
        ):
            self.assertIn(phrase, agents)

    def test_agents_is_the_single_top_level_video_policy_source(self) -> None:
        repo = TTS_ROOT.parents[1]
        agents = (repo / "AGENTS.md").read_text(encoding="utf-8")
        claude = (repo / "CLAUDE.md").read_text(encoding="utf-8")
        patterns = {
            "official MV priority": r"官方 MV.*优先",
            "TOP countdown": r"TOP.*N→1",
            "ranking suspense": r"(?:不得|禁止).*提前",
            "full narration structure": r"(?:开头|开场|intro).*每首.*(?:结尾|outro|CTA)",
            "quality before duration": r"不设.*上限",
            "singer typography": r"歌手\s*/\s*组合名.*唯一最大字号",
            "free exploration boundary": r"完全自由探索类",
        }
        self.assertIn("single top-level source of agent instructions", agents)
        for label, pattern in patterns.items():
            self.assertRegex(agents, pattern, f"AGENTS.md: missing {label}")

        for reference in (
            "[`AGENTS.md`](AGENTS.md)",
            "[`CONVENTIONS.md`](CONVENTIONS.md)",
            "[`tools/video/README.md`](tools/video/README.md)",
        ):
            self.assertIn(reference, claude)
        for duplicated_rule in (
            "官方 MV",
            "N→1",
            "完全自由探索类",
            "CV002",
            "BEYOND",
        ):
            self.assertNotIn(duplicated_rule, claude)


if __name__ == "__main__":
    unittest.main()
