from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock


TTS_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TTS_ROOT.parents[1]
sys.path.insert(0, str(TTS_ROOT))

from narrate import normalize_qwen_items
from text_normalizer import PronunciationPolicy, normalize_tts_text


class LatinPronunciationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = PronunciationPolicy.load()

    def normalized(self, text: str, overrides: dict[str, str] | None = None) -> str:
        return normalize_tts_text(
            text,
            policy=self.policy,
            overrides=overrides,
        ).normalized_text

    def test_beyond_is_read_as_a_word_even_next_to_chinese(self) -> None:
        self.assertEqual(
            self.normalized("今天重听BEYOND五首被低估的作品。"),
            "今天重听Beyond五首被低估的作品。",
        )

    def test_normal_word_case_is_left_unchanged(self) -> None:
        self.assertEqual(
            self.normalized("Beyond 和 One Piece 都保留正常词形。"),
            "Beyond 和 One Piece 都保留正常词形。",
        )

    def test_pure_chinese_is_byte_for_byte_unchanged(self) -> None:
        text = "第五名，《命运是你家》。旋律、词意和演唱都很完整，二零二六年再听仍然有力量。"
        result = normalize_tts_text(text, policy=self.policy)
        self.assertEqual(result.normalized_text, text)
        self.assertFalse(result.changed)
        self.assertEqual(result.decisions, ())

    def test_known_initialisms_are_spelled_as_letters(self) -> None:
        self.assertEqual(
            self.normalized("BTS、NBA、AI、MP3"),
            "B T S、N B A、A I、M P 3",
        )

    def test_explicit_dotted_initialism_is_spelled_as_letters(self) -> None:
        self.assertEqual(self.normalized("S.H.E.和G.E.M."), "S H E和G E M")

    def test_obvious_short_word_uses_word_pronunciation(self) -> None:
        self.assertEqual(self.normalized("TOP ONE"), "Top One")

    def test_nonword_without_a_pronounceable_vowel_uses_letters(self) -> None:
        self.assertEqual(self.normalized("XQRT"), "X Q R T")

    def test_literal_and_project_overrides(self) -> None:
        self.assertEqual(self.normalized("AC/DC 和 KPOP"), "A C D C 和 K-pop")
        self.assertEqual(
            self.normalized("BTOB", overrides={"BTOB": "B to B"}),
            "B to B",
        )

    def test_metadata_keeps_source_and_decision(self) -> None:
        result = normalize_tts_text("BEYOND", policy=self.policy)
        self.assertTrue(result.changed)
        self.assertEqual(result.source_text, "BEYOND")
        self.assertEqual(result.normalized_text, "Beyond")
        self.assertEqual(result.decisions[0]["mode"], "word_candidate")
        self.assertEqual(result.policy_id, "latin-word-first-v1")

    def test_dispatcher_attaches_auditable_normalization(self) -> None:
        items = [
            {
                "id": "intro",
                "text": "重听BEYOND。",
                "pronunciation_overrides": {},
            }
        ]
        normalize_qwen_items(items)
        self.assertEqual(items[0]["source_text"], "重听BEYOND。")
        self.assertEqual(items[0]["text"], "重听Beyond。")
        self.assertTrue(items[0]["text_normalization"]["changed"])

    def test_dispatcher_does_not_touch_pure_chinese_request_shape(self) -> None:
        text = "第一名，《无泪的遗憾》。这段旋律值得压轴。"
        items = [
            {
                "id": "p1",
                "text": text,
                "pronunciation_overrides": {},
            }
        ]
        normalize_qwen_items(items)
        self.assertEqual(items, [{"id": "p1", "text": text}])

    def test_pure_chinese_does_not_depend_on_pronunciation_policy(self) -> None:
        text = "这是纯中文旁白，标点和二零二六年都必须保持原样。"
        items = [
            {
                "id": "pure-zh",
                "text": text,
                "pronunciation_overrides": {},
            }
        ]
        with mock.patch.object(
            PronunciationPolicy,
            "load",
            side_effect=AssertionError("pure Chinese must not load pronunciation policy"),
        ):
            normalize_qwen_items(items)
        self.assertEqual(items, [{"id": "pure-zh", "text": text}])

    def test_preview_cli_outputs_json(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(TTS_ROOT / "text_normalizer.py"),
                "BEYOND与BTS",
                "--json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        value = json.loads(completed.stdout)
        self.assertEqual(value["normalized_text"], "Beyond与B T S")
        self.assertEqual(len(value["decisions"]), 2)


class PronunciationPolicyDocumentationTests(unittest.TestCase):
    def test_global_docs_state_word_first_rule(self) -> None:
        paths = [
            REPO_ROOT / "AGENTS.md",
            REPO_ROOT / "CLAUDE.md",
            REPO_ROOT / "CONVENTIONS.md",
            REPO_ROOT / "tools" / "video" / "README.md",
            TTS_ROOT / "README.md",
        ]
        for path in paths:
            text = path.read_text(encoding="utf-8")
            self.assertIn("BEYOND", text, path)
            self.assertRegex(text, r"单词.*优先.*按词|优先.*单词.*发音", path)
            self.assertRegex(text, r"缩写|首字母", path)
            self.assertRegex(text, r"纯中文.*原样|纯中文.*透传", path)

    def test_qwen_sidecar_records_source_and_normalized_text(self) -> None:
        worker = (TTS_ROOT / "engines" / "qwen_mlx.py").read_text(encoding="utf-8")
        self.assertIn('"source_text"', worker)
        self.assertIn('"normalized_text"', worker)
        self.assertIn('"text_normalization"', worker)
        self.assertIn('if "source_text" in item:', worker)


if __name__ == "__main__":
    unittest.main()
