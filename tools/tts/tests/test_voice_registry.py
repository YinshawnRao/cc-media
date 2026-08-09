from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path


TTS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TTS_ROOT))

from voice_registry import VoiceRegistry, file_sha256, resolve_selector, resolve_task_prompt


class VoiceResolverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = VoiceRegistry.load()

    def assert_voice(self, prompt: str, voice_id: str, reason: str) -> None:
        value = resolve_task_prompt(self.registry, prompt)
        self.assertEqual(value["resolved_voice_id"], voice_id)
        self.assertEqual(value["resolution_reason"], reason)

    def test_default_is_cv002(self) -> None:
        self.assert_voice("做一期新的华语歌曲盘点视频", "CV002", "default_no_request")

    def test_structured_name(self) -> None:
        self.assert_voice("主题：经典前奏\n配音：治愈少女", "CV002", "explicit_prompt_match")

    def test_structured_id(self) -> None:
        self.assert_voice("配音：CV004", "CV004", "explicit_prompt_match")

    def test_imperative_alias(self) -> None:
        self.assert_voice("这期用元气萌妹来讲。", "CV001", "explicit_prompt_match")

    def test_unknown_falls_back(self) -> None:
        self.assert_voice("配音：CV999", "CV002", "fallback_unmatched_prompt")
        self.assert_voice("请用可爱女声配音", "CV002", "fallback_unmatched_prompt")

    def test_ambiguous_falls_back(self) -> None:
        self.assert_voice(
            "配音：元气萌妹或清冷学姐都可以",
            "CV002",
            "fallback_ambiguous_prompt",
        )

    def test_topic_words_do_not_select_voice(self) -> None:
        self.assert_voice("盘点热血少年动漫名场面", "CV002", "default_no_request")

    def test_negative_voice_is_ignored(self) -> None:
        self.assert_voice(
            "不要用热血少年配音，请用清冷学姐配音",
            "CV004",
            "explicit_prompt_match",
        )

    def test_multiple_tokens_for_same_voice_are_not_ambiguous(self) -> None:
        self.assert_voice("配音：CV002（治愈少女）", "CV002", "explicit_prompt_match")

    def test_explicit_selector_is_exact(self) -> None:
        self.assertEqual(resolve_selector(self.registry, "soft_healer")["resolved_voice_id"], "CV002")
        self.assertEqual(resolve_selector(self.registry, "CV999")["resolved_voice_id"], "CV002")
        self.assertEqual(
            resolve_selector(self.registry, "zm_yunxi")["resolved_voice_id"],
            "kokoro:zm_yunxi",
        )
        self.assertEqual(resolve_selector(self.registry, "")["resolved_voice_id"], "CV002")

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
        self.assertEqual(value["resolved_voice_id"], "CV002")
        self.assertTrue(value["fallback"])


class VoiceAssetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = VoiceRegistry.load()

    def test_ids_are_stable_and_default_exists(self) -> None:
        self.assertEqual([voice["id"] for voice in self.registry.voices], [f"CV{i:03d}" for i in range(1, 9)])
        self.assertEqual(self.registry.default_id, "CV002")

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

    def run_gate(self, project: Path, selection_path: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(TTS_ROOT / "verify_voice_usage.py"),
                "--selection",
                str(selection_path),
                "--project-root",
                str(project),
            ],
            capture_output=True,
            text=True,
        )

    def create_project(self, project: Path) -> tuple[Path, Path]:
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
        sidecar = {
            "selection": selection,
            "resolved_voice_id": "CV002",
            "engine": qwen["engine"],
            "model_id": qwen["model_id"],
            "model_revision": qwen["model_revision"],
            "model_tree_sha256": qwen["model_tree_sha256"],
            "reference_sha256": voice["reference_sha256"],
            "output": str(output),
            "output_sha256": file_sha256(output),
        }
        sidecar_path = output.with_suffix(".wav.tts.json")
        sidecar_path.write_text(
            json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        return selection_path, sidecar_path

    def test_gate_validates_full_provenance_and_wav(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            selection_path, _ = self.create_project(project)
            completed = self.run_gate(project, selection_path)
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_gate_rejects_tampered_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            selection_path, sidecar_path = self.create_project(project)
            sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
            sidecar["reference_sha256"] = "0" * 64
            sidecar_path.write_text(json.dumps(sidecar), encoding="utf-8")
            completed = self.run_gate(project, selection_path)
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("wrong reference-audio hash", completed.stdout)


class WorkspacePolicyTests(unittest.TestCase):
    def test_top_level_rules_share_the_same_default(self) -> None:
        repo = TTS_ROOT.parents[1]
        paths = [
            repo / "AGENTS.md",
            repo / "CLAUDE.md",
            repo / "CONVENTIONS.md",
            repo / "tools" / "video" / "README.md",
            TTS_ROOT / "README.md",
        ]
        for path in paths:
            text = path.read_text(encoding="utf-8")
            self.assertIn("CV002", text, path)
            self.assertIn("治愈少女", text, path)
            self.assertNotIn("默认男声", text, path)

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

    def test_global_video_defaults_are_synced(self) -> None:
        repo = TTS_ROOT.parents[1]
        paths = [
            repo / "AGENTS.md",
            repo / "CLAUDE.md",
            repo / "CONVENTIONS.md",
            repo / "tools" / "video" / "README.md",
        ]
        patterns = {
            "official MV priority": r"官方 MV.*优先",
            "TOP countdown": r"TOP.*N→1",
            "ranking suspense": r"(?:不得|禁止).*提前",
            "full narration structure": r"(?:开头|开场|intro).*每首.*(?:结尾|outro|CTA)",
            "quality before duration": r"不设.*上限",
            "singer typography": r"歌手名.*(?:相同|同字号|更大)",
            "free exploration boundary": r"完全自由探索类",
        }
        for path in paths:
            text = path.read_text(encoding="utf-8")
            for label, pattern in patterns.items():
                self.assertRegex(text, pattern, f"{path}: missing {label}")


if __name__ == "__main__":
    unittest.main()
