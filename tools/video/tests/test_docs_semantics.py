"""Semantic regressions for the repository's active workflow documentation.

Check executable/configuration contracts and reachable documentation links.
Policy wording is intentionally not duplicated across entrypoints or tested
with sentence-matching assertions.
"""

from __future__ import annotations

import ast
import json
import re
import stat
import subprocess
import sys
import unittest
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[3]
TTS_ROOT = REPO_ROOT / "tools" / "tts"
VIDEO_ROOT = REPO_ROOT / "tools" / "video"

if str(TTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TTS_ROOT))

from voice_registry import VoiceRegistry, resolve_selector, resolve_task_prompt

import tools.video.outro_cta as cta_contract
from tools.video import verify_project as project_gate
from tools.video.outro_cta import FIXED_OUTRO_CTA


ACTIVE_DOCS = (
    REPO_ROOT / "AGENTS.md",
    REPO_ROOT / "CLAUDE.md",
    REPO_ROOT / "README.md",
    REPO_ROOT / "CONVENTIONS.md",
    VIDEO_ROOT / "README.md",
    TTS_ROOT / "README.md",
)

REQUIRED_CLIS = (
    TTS_ROOT / "resolve_voice.py",
    TTS_ROOT / "narrate.py",
    TTS_ROOT / "doctor.py",
    TTS_ROOT / "verify_voice_usage.py",
    VIDEO_ROOT / "verify_project.py",
    VIDEO_ROOT / "verify_publishing.py",
    VIDEO_ROOT / "prepare_final_qa.py",
    VIDEO_ROOT / "verify_final_video.py",
    VIDEO_ROOT / "showcase_align.py",
    VIDEO_ROOT / "yt_dlp_readonly.py",
)

SHARED_PYTHON_TEMPLATES = (
    VIDEO_ROOT / "countdown_build.py",
    VIDEO_ROOT / "narrate_segments.py",
    VIDEO_ROOT / "templates" / "ai-voice-mv" / "build.py",
    VIDEO_ROOT / "templates" / "longform-timeline" / "build.py",
)

RETIRED_SANDBOX_PATHS = {
    REPO_ROOT / "sandbox" / "tts-character-voice-lab": (
        TTS_ROOT / "research" / "qwen-character-voice-lab"
    ),
    REPO_ROOT / "sandbox" / "angela-ai-mv-covers": (
        VIDEO_ROOT / "templates" / "ai-voice-mv"
    ),
    REPO_ROOT / "sandbox" / "lirh-yangcl-timeline": (
        VIDEO_ROOT / "templates" / "longform-timeline"
    ),
}

class WorkflowIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = VoiceRegistry.load()

    def test_voice_selection_prefers_model_emotion_decision_then_random_fallback(self) -> None:
        config = self.registry.config
        pool = [
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
        self.assertEqual("CV002", config["preflight_voice_id"])
        self.assertEqual(pool, config["decision_voice_pool"])
        self.assertEqual(pool, config["random_voice_pool"])
        self.assertEqual("model_emotion_decision", config["selection_policy"]["default"])
        self.assertEqual("model_emotion_decision", config["selection_policy"]["unknown"])
        self.assertEqual("model_emotion_decision", config["selection_policy"]["ambiguous"])
        self.assertEqual("random_voice_pool", config["selection_policy"]["model_unavailable"])
        self.assertEqual({"male": 5, "female": 5}, config["decision_pool_expected_groups"])
        self.assertIs(config["selection_policy"]["fuzzy_matching"], False)

        model_args = {
            "model_choice": "CV012",
            "model_reason": "主题强调时代重量与人物命运，适合深沉纪实表达。",
            "model_confidence": "high",
        }
        default = resolve_task_prompt(
            self.registry, "做一期沉重的时代人物纪实。", **model_args
        )
        unknown = resolve_task_prompt(self.registry, "配音：CV999", **model_args)
        conflict = resolve_task_prompt(
            self.registry, "配音：CV003 或 CV004", **model_args
        )
        with patch(
            "voice_registry.secrets.choice", return_value=self.registry.by_id("CV013")
        ):
            fallback = resolve_task_prompt(
                self.registry,
                "做一期主题暂未明确的内容。",
                model_reason="项目信息不足，无法可靠判断。",
                model_confidence="low",
            )
        explicit = resolve_selector(self.registry, "CV004")

        for selection in (default, unknown, conflict):
            self.assertEqual("CV012", selection["resolved_voice_id"])
            self.assertEqual("model_emotion_match", selection["resolution_reason"])
            self.assertEqual("model_decision", selection["selection_mode"])
            self.assertEqual(pool, selection["candidate_voice_ids"])
            self.assertEqual("high", selection["model_decision_confidence"])
        self.assertEqual("CV013", fallback["resolved_voice_id"])
        self.assertEqual("fallback_model_unavailable", fallback["resolution_reason"])
        self.assertEqual("random_pool", fallback["selection_mode"])
        self.assertEqual(pool, fallback["candidate_voice_ids"])
        self.assertEqual("low", fallback["model_decision_confidence"])
        self.assertEqual("CV004", explicit["resolved_voice_id"])
        self.assertEqual("explicit", explicit["selection_mode"])
        self.assertFalse(explicit["fallback"])

    def test_canonical_cta_is_the_unique_last_template_narration(self) -> None:
        self.assertFalse(hasattr(cta_contract, "outro_cta"))
        self.assertFalse(hasattr(cta_contract, "DEFAULT_VOTE_OBJECT"))
        self.assertFalse(hasattr(cta_contract, "DEFAULT_NEXT_HOOK"))
        template_path = VIDEO_ROOT / "examples" / "project-contract" / "project-manifest.json"
        template = json.loads(template_path.read_text(encoding="utf-8"))
        rows = template["narration_sequence"]
        self.assertGreaterEqual(len(rows), 1)
        self.assertEqual("outro_cta", rows[-1]["role"])
        self.assertEqual("outro-cta", rows[-1]["id"])
        self.assertEqual(FIXED_OUTRO_CTA, rows[-1]["text"])
        self.assertEqual(1, sum(row.get("role") == "outro_cta" for row in rows))
        self.assertEqual(1, sum(row.get("text") == FIXED_OUTRO_CTA for row in rows))

    def test_project_schema_and_gate_constants_are_identical(self) -> None:
        schema = json.loads(
            (VIDEO_ROOT / "project-manifest.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            set(project_gate.SUPPORTED_SCHEMA_VERSIONS),
            set(schema["properties"]["schema_version"]["enum"]),
        )
        self.assertEqual(
            project_gate.SCHEMA_VERSION,
            json.loads(
                (
                    VIDEO_ROOT / "examples" / "project-contract" / "project-manifest.json"
                ).read_text(encoding="utf-8")
            )["schema_version"],
        )
        self.assertEqual(
            project_gate.PROJECT_KINDS,
            set(schema["properties"]["project_kind"]["enum"]),
        )
        self.assertEqual(
            project_gate.NARRATION_ROLES,
            set(schema["$defs"]["narration"]["properties"]["role"]["enum"]),
        )
        required_contracts = {
            "selectedDownloadReceipt": project_gate.SOURCE_RECEIPT_REQUIRED,
            "sourceDerivation": project_gate.SOURCE_DERIVATION_REQUIRED,
            "vocalShowcaseEvidence": project_gate.VOCAL_EVIDENCE_REQUIRED,
            "instrumentalEvidence": project_gate.INSTRUMENTAL_EVIDENCE_REQUIRED,
            "reviewApproval": project_gate.REVIEW_APPROVAL_REQUIRED,
        }
        for name, expected in required_contracts.items():
            with self.subTest(contract=name):
                definition = schema["$defs"][name]
                self.assertIs(definition.get("additionalProperties"), False)
                self.assertEqual(set(expected), set(definition["required"]))

    def test_required_clis_are_regular_files_with_main_and_help(self) -> None:
        for path in REQUIRED_CLIS:
            with self.subTest(path=path.relative_to(REPO_ROOT)):
                info = path.lstat()
                self.assertTrue(stat.S_ISREG(info.st_mode), path)
                self.assertFalse(path.is_symlink(), path)
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
                self.assertTrue(
                    any(
                        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                        and node.name == "main"
                        for node in tree.body
                    ),
                    f"{path} has no top-level main()",
                )
                completed = subprocess.run(
                    [sys.executable, str(path), "--help"],
                    cwd=REPO_ROOT,
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                output = completed.stdout + completed.stderr
                self.assertEqual(0, completed.returncode, output)
                self.assertRegex(output.casefold(), r"\busage:")

    def test_shared_python_templates_do_not_bypass_central_tts(self) -> None:
        failures: list[str] = []
        for path in SHARED_PYTHON_TEMPLATES:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name == "kokoro" or alias.name.startswith("kokoro."):
                            failures.append(f"{path.relative_to(REPO_ROOT)} imports {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    if module == "kokoro" or module.startswith("kokoro."):
                        failures.append(f"{path.relative_to(REPO_ROOT)} imports {module}")
                elif isinstance(node, ast.Call):
                    function = node.func
                    if (
                        isinstance(function, ast.Name)
                        and function.id == "KPipeline"
                    ) or (
                        isinstance(function, ast.Attribute)
                        and function.attr == "KPipeline"
                    ):
                        failures.append(
                            f"{path.relative_to(REPO_ROOT)} calls KPipeline at line {node.lineno}"
                        )
            for node in tree.body:
                targets: list[ast.expr] = []
                if isinstance(node, ast.Assign):
                    targets = node.targets
                elif isinstance(node, ast.AnnAssign):
                    targets = [node.target]
                if any(isinstance(target, ast.Name) and target.id == "VOICE" for target in targets):
                    failures.append(
                        f"{path.relative_to(REPO_ROOT)} defines top-level VOICE"
                    )
        self.assertEqual([], failures, "\n".join(failures))

    def test_listen_pages_label_kokoro_as_legacy_not_current_default(self) -> None:
        generator = (
            TTS_ROOT
            / "research"
            / "qwen-character-voice-lab"
            / "src"
            / "build_listen_page.py"
        ).read_text(encoding="utf-8")
        formal_page = (TTS_ROOT / "voices" / "listen.html").read_text(encoding="utf-8")
        stale = re.compile(r"(?:当前\s*)?默认男\s*/\s*女声")
        self.assertNotRegex(generator, stale)
        self.assertIn("Legacy Kokoro", generator)
        self.assertNotRegex(formal_page, stale)
        self.assertIn("当前标准：模型先按作品情绪与叙事表达选择", formal_page)
        self.assertIn("标准池共 10 个声音（5 男 5 女）", formal_page)
        self.assertIn("Legacy Kokoro", formal_page)

    def test_local_markdown_routes_resolve(self) -> None:
        paths = [*ACTIVE_DOCS, VIDEO_ROOT / "operations.md", VIDEO_ROOT / "skill-routing.md"]
        paths.extend((REPO_ROOT / ".agents/skills").glob("*/SKILL.md"))
        for path in paths:
            for raw in re.findall(r"\[[^\]]+\]\(([^)]+)\)", path.read_text()):
                target = raw.split("#", 1)[0]
                if not target or "://" in target or "<" in target:
                    continue
                with self.subTest(source=path, target=target):
                    self.assertTrue((path.parent / target).exists(), f"broken route: {path}: {target}")


if __name__ == "__main__":
    unittest.main()
