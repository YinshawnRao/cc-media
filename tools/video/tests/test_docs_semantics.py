"""Semantic regressions for the repository's active workflow documentation.

These tests prefer executable/configuration sources over duplicated prose.  They
also distinguish active guidance from explicitly historical/legacy notes so a
useful migration record does not become a brittle global substring failure.
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
    VIDEO_ROOT / "verify_final_video.py",
    VIDEO_ROOT / "showcase_align.py",
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

HISTORICAL_MARKERS = re.compile(
    r"历史|legacy|旧版|旧规则|已废止|废弃|归档|已踩|决策记录|"
    r"实战补充|验证补充|实验记录",
    re.IGNORECASE,
)
PROHIBITION_BEFORE = re.compile(
    r"(?:不要|禁止|不得|不允许|不表示(?:重新)?(?:执行)?|避免|不再|不可|"
    r"never|do\s+not|must\s+not)"
    r"[^。；;\n]{0,48}$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class MarkdownLine:
    path: Path
    number: int
    text: str
    historical: bool

    @property
    def label(self) -> str:
        return f"{self.path.relative_to(REPO_ROOT)}:{self.number}"


def markdown_lines(path: Path) -> list[MarkdownLine]:
    """Return lines annotated with their Markdown heading history context."""

    headings: dict[int, str] = {}
    result: list[MarkdownLine] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if match:
            level = len(match.group(1))
            headings = {key: value for key, value in headings.items() if key < level}
            headings[level] = match.group(2)
        context = " / ".join(headings[key] for key in sorted(headings))
        result.append(
            MarkdownLine(
                path=path,
                number=number,
                text=line,
                historical=bool(HISTORICAL_MARKERS.search(context)),
            )
        )
    return result


def occurrence_is_policy_prohibition(line: str, start: int) -> bool:
    return PROHIBITION_BEFORE.search(line[:start]) is not None


class MachineSourceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = VoiceRegistry.load()

    def test_default_unknown_and_conflicting_voice_requests_use_cv002(self) -> None:
        config = self.registry.config
        self.assertEqual("CV002", config["default_voice_id"])
        self.assertEqual("CV002", config["fallback_voice_id"])
        self.assertEqual("fallback_default", config["selection_policy"]["unknown"])
        self.assertEqual("fallback_default", config["selection_policy"]["ambiguous"])
        self.assertIs(config["selection_policy"]["fuzzy_matching"], False)

        default = resolve_task_prompt(self.registry, "做一期新的华语音乐盘点。")
        unknown = resolve_selector(self.registry, "CV999")
        conflict = resolve_task_prompt(self.registry, "配音：CV003 或 CV004")
        explicit = resolve_selector(self.registry, "CV004")

        self.assertEqual(("CV002", "default_no_request"), (
            default["resolved_voice_id"], default["resolution_reason"]
        ))
        self.assertEqual(("CV002", "fallback_unmatched_selector"), (
            unknown["resolved_voice_id"], unknown["resolution_reason"]
        ))
        self.assertEqual(("CV002", "fallback_ambiguous_prompt"), (
            conflict["resolved_voice_id"], conflict["resolution_reason"]
        ))
        self.assertEqual("CV004", explicit["resolved_voice_id"])
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
            project_gate.SCHEMA_VERSION,
            schema["properties"]["schema_version"]["const"],
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

    def test_retired_sandbox_projects_map_to_durable_regular_directories(self) -> None:
        for retired, durable in RETIRED_SANDBOX_PATHS.items():
            with self.subTest(retired=retired.name):
                self.assertFalse(retired.exists(), f"retired path was restored: {retired}")
                info = durable.lstat()
                self.assertTrue(stat.S_ISDIR(info.st_mode), durable)
                self.assertFalse(durable.is_symlink(), durable)
                self.assertTrue(any(path.is_file() for path in durable.rglob("*")), durable)


class ActiveDocumentationPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.lines = [line for path in ACTIVE_DOCS for line in markdown_lines(path)]
        cls.active_lines = [line for line in cls.lines if not line.historical]

    def assert_no_occurrences(
        self,
        pattern: re.Pattern[str],
        *,
        allow_policy_prohibition: bool = False,
    ) -> None:
        failures: list[str] = []
        for line in self.active_lines:
            for match in pattern.finditer(line.text):
                if allow_policy_prohibition and occurrence_is_policy_prohibition(
                    line.text, match.start()
                ):
                    continue
                failures.append(f"{line.label}: {match.group(0)!r}")
        self.assertEqual([], failures, "\n".join(failures))

    def test_active_docs_do_not_claim_the_repo_is_not_initialized(self) -> None:
        self.assert_no_occurrences(
            re.compile(
                r"not\s+yet\s+a\s+git\s+repo|not\s+a\s+git\s+repo|"
                r"(?:还|尚)?不是\s*git\s*仓库|目录还没有\s*git|"
                r"run\s+`?git\s+init`?|git\s+init\s+before",
                re.IGNORECASE,
            )
        )
        self.assert_no_occurrences(
            re.compile(r"\bgit\s+init\b", re.IGNORECASE),
            allow_policy_prohibition=True,
        )

    def test_active_docs_have_no_current_default_male_or_female_voice(self) -> None:
        self.assert_no_occurrences(
            re.compile(
                r"(?:当前\s*)?默认(?:男声|女声|男\s*/\s*女声|男\s*/\s*女)|"
                r"默认男\s*/\s*女声"
            ),
            allow_policy_prohibition=True,
        )

    def test_active_docs_do_not_run_bare_or_latest_hyperframes(self) -> None:
        self.assert_no_occurrences(
            re.compile(r"\bnpx\s+hyperframes(?=\s|$|[.`])", re.IGNORECASE),
            allow_policy_prohibition=True,
        )
        self.assert_no_occurrences(
            re.compile(r"@latest\b", re.IGNORECASE),
            allow_policy_prohibition=True,
        )

    def test_active_docs_require_local_fonts_and_no_remote_google_fonts(self) -> None:
        remote = re.compile(
            r"fonts\.(?:googleapis|gstatic)\.com|"
            r"(?:fetch|远程|联网|在线).{0,24}Google\s+Fonts|"
            r"Google\s+Fonts.{0,24}(?:fetch|远程|联网|在线)",
            re.IGNORECASE,
        )
        self.assert_no_occurrences(remote, allow_policy_prohibition=True)
        active_text = "\n".join(line.text for line in self.active_lines)
        self.assertRegex(
            active_text,
            r"(?:系统字体|本地字体|本地\s*woff2|随项目.{0,12}字体|"
            r"bundled.{0,12}font)",
        )
        self.assertRegex(
            active_text,
            r"(?:禁止|不得|不要|不允许|不依赖).{0,60}"
            r"(?:远程.{0,16}字体|Google\s+Fonts|fonts\.googleapis)",
        )

    def test_local_font_mentions_keep_the_machine_locked_boundary(self) -> None:
        failures: list[str] = []
        for line in self.active_lines:
            if "local()" not in line.text:
                continue
            if not re.search(r"本机|OS|历史|专用|跨机", line.text, re.IGNORECASE):
                failures.append(f"{line.label}: {line.text}")
        self.assertEqual([], failures, "\n".join(failures))

    def test_narrow_vertical_crop_remains_an_evidenced_user_exception(self) -> None:
        runbook = (VIDEO_ROOT / "README.md").read_text(encoding="utf-8")
        line = next(
            candidate
            for candidate in runbook.splitlines()
            if "裁切放大贴宽" in candidate
        )
        for required in ("用户明确要求", "完整候选窗", "逐帧", "design/QA"):
            self.assertIn(required, line)


class SharedTemplateAstTests(unittest.TestCase):
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
        self.assertIn("当前默认：CV002 · 治愈少女", formal_page)
        self.assertIn("Legacy Kokoro", formal_page)


if __name__ == "__main__":
    unittest.main()
