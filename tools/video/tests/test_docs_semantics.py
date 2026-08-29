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

    def test_voice_selection_prefers_model_emotion_decision_then_random_fallback(self) -> None:
        config = self.registry.config
        pool = [
            "CV001",
            "CV002",
            "CV003",
            "CV004",
            "CV008",
            "CV009",
            "CV010",
            "CV011",
            "CV012",
            "CV013",
        ]
        self.assertEqual("CV002", config["preflight_voice_id"])
        self.assertEqual(pool, config["decision_voice_pool"])
        self.assertEqual(pool, config["random_voice_pool"])
        self.assertEqual("model_emotion_decision", config["selection_policy"]["default"])
        self.assertEqual("model_emotion_decision", config["selection_policy"]["unknown"])
        self.assertEqual("model_emotion_decision", config["selection_policy"]["ambiguous"])
        self.assertEqual("random_voice_pool", config["selection_policy"]["model_unavailable"])
        self.assertEqual({"female": 8, "male": 2}, config["decision_pool_expected_groups"])
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

    def test_endpoint_weighted_narration_limits_are_machine_bound_and_documented(self) -> None:
        self.assertEqual(
            {"top_ranking": 8.0, "narrative": 10.0},
            project_gate.TRANSITION_NARRATION_MAX_SECONDS,
        )
        for relative in ("AGENTS.md", "CONVENTIONS.md", "tools/video/README.md"):
            document = (REPO_ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(document=relative):
                self.assertIn("schema v2", document)
                self.assertIn("硬上限 8 秒", document)
                self.assertIn("硬上限 10 秒", document)

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

    def test_goal_video_tasks_default_to_one_shot_final_delivery(self) -> None:
        agents = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        conventions = (REPO_ROOT / "CONVENTIONS.md").read_text(encoding="utf-8")
        runbook = (VIDEO_ROOT / "README.md").read_text(encoding="utf-8")
        root_readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("goal / 视频制作默认一次交付整片", agents)
        self.assertIn("goal / 视频制作默认一次完成", conventions)
        self.assertIn("默认一次完成整片", runbook)
        self.assertIn("一次完成整片", root_readme)
        for document in (agents, conventions, runbook, root_readme):
            self.assertIn("用户明确要求", document)
            self.assertIn("renders/<slug>.mp4", document)
            self.assertIn("publishing/xiaohongshu.md", document)
            self.assertIn("四道门禁", document)
            for gate in ("VOICE", "PROJECT", "PUBLISHING", "FINAL"):
                self.assertIn(gate, document)
        active_text = "\n".join(line.text for line in self.active_lines)
        self.assertNotIn("样片先行铁律", active_text)
        self.assertNotIn("确认后再批量", active_text)

    def test_new_sandbox_media_outputs_are_fixed_under_renders(self) -> None:
        documents = (
            REPO_ROOT / "AGENTS.md",
            REPO_ROOT / "CONVENTIONS.md",
            REPO_ROOT / "README.md",
            VIDEO_ROOT / "README.md",
            VIDEO_ROOT / "templates" / "README.md",
        )
        invalid_directory = re.compile(r"(?<![\w-])(?:final|output)/", re.IGNORECASE)
        invalid_commands = (
            re.compile(r"--output\s+(?!renders/)", re.IGNORECASE),
            re.compile(r"--final\s+(?!renders/)", re.IGNORECASE),
            re.compile(r"-shortest\s+(?!renders/)[^\s`]+\.mp4", re.IGNORECASE),
        )
        failures: list[str] = []

        for path in documents:
            lines = markdown_lines(path)
            text = path.read_text(encoding="utf-8")
            self.assertIn("renders/", text, path)
            for line in lines:
                if line.historical:
                    continue
                for match in invalid_directory.finditer(line.text):
                    if occurrence_is_policy_prohibition(line.text, match.start()):
                        continue
                    failures.append(f"{line.label}: active output directory {match.group(0)!r}")
                for pattern in invalid_commands:
                    if (
                        "filter_cookie_jar.py" in line.text
                        and "candidate" in line.text
                        and "仓库外" in line.text
                    ):
                        continue
                    for match in pattern.finditer(line.text):
                        if occurrence_is_policy_prohibition(line.text, match.start()):
                            continue
                        failures.append(f"{line.label}: unsafe output command {match.group(0)!r}")

        self.assertEqual([], failures, "\n".join(failures))

        delivery_docs = {
            "AGENTS.md": (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8"),
            "CONVENTIONS.md": (REPO_ROOT / "CONVENTIONS.md").read_text(encoding="utf-8"),
            "README.md": (REPO_ROOT / "README.md").read_text(encoding="utf-8"),
            "tools/video/README.md": (VIDEO_ROOT / "README.md").read_text(encoding="utf-8"),
        }
        for label, document in delivery_docs.items():
            with self.subTest(document=label):
                self.assertIn("renders/<slug>.mp4", document)
                self.assertRegex(document, r"raw render.{0,100}renders/")
                self.assertRegex(document, r"mux.{0,120}renders/")
                self.assertRegex(
                    document,
                    r"(?:禁止|不得).{0,80}final/.{0,40}output/.{0,80}项目根",
                )

    def test_publishing_copy_is_a_post_build_pre_final_delivery_gate(self) -> None:
        documents = {
            "AGENTS.md": (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8"),
            "CONVENTIONS.md": (REPO_ROOT / "CONVENTIONS.md").read_text(encoding="utf-8"),
            "README.md": (REPO_ROOT / "README.md").read_text(encoding="utf-8"),
            "tools/video/README.md": (VIDEO_ROOT / "README.md").read_text(encoding="utf-8"),
        }
        cli = "python3 tools/video/verify_publishing.py --project sandbox/<slug>"
        for label, document in documents.items():
            with self.subTest(document=label):
                self.assertIn("publishing/xiaohongshu.md", document)
                self.assertIn(cli, document)
                self.assertIn("project-manifest.json", document)
                self.assertRegex(document, r"(?:build|post-mux).{0,100}(?:后|完成后)")
                self.assertRegex(document, r"(?:FINAL 前|才进入 FINAL|进入 FINAL)")
                self.assertRegex(
                    document,
                    r"(?:不属于|不得提前|不改变).{0,100}project-manifest\.json",
                )
                self.assertRegex(document, r"1[–-]5 个")
                self.assertRegex(document, r"默认(?:给)?\s*3 个")
                self.assertRegex(document, r"第一条.{0,12}首选")
                self.assertRegex(document, r"最后一行.{0,16}hashtags")
                self.assertRegex(document, r"不得出现.{0,20}歌曲名称")
                for required in ("真实主题", "歌手", "选题角度", "泛化", "杜撰"):
                    self.assertIn(required, document)
                self.assertIn("renders/<slug>.mp4", document)
                self.assertIn("四道门禁", document)

        runbook = documents["tools/video/README.md"]
        self.assertLess(runbook.index("## 8. 渲染 + MUX"), runbook.index("## 9. 小红书发布文案"))
        self.assertLess(runbook.index("## 9. 小红书发布文案"), runbook.index("## 10. 终片 QA"))
        for fixed_markdown in (
            "# 小红书发布文案",
            "## 标题候选（第一条为首选）",
            "## 正文",
            "8–10 个 hashtags",
        ):
            self.assertIn(fixed_markdown, runbook)

    def test_internal_failure_repairs_and_reruns_before_goal_can_pause(self) -> None:
        documents = {
            "AGENTS.md": (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8"),
            "CONVENTIONS.md": (REPO_ROOT / "CONVENTIONS.md").read_text(encoding="utf-8"),
            "README.md": (REPO_ROOT / "README.md").read_text(encoding="utf-8"),
            "tools/video/README.md": (VIDEO_ROOT / "README.md").read_text(encoding="utf-8"),
        }

        for label, document in documents.items():
            with self.subTest(document=label):
                self.assertIn(
                    "内部步骤首次失败只停止当前步骤，不停止整个 goal",
                    document,
                )
                self.assertIn("诊断 → 修复 → 重跑", document)
                self.assertIn("最近失败步骤", document)
                self.assertIn("受影响下游门禁", document)
                self.assertIn(
                    "不得因可自行修复的内部失败暂停、等待用户确认或标记 `blocked`",
                    document,
                )
                self.assertRegex(
                    document,
                    r"机械红线.{0,80}(?:不得|不能).{0,30}(?:降级|放松)",
                )

        combined = "\n".join(documents.values())
        self.assertNotIn("其他阻断项", combined)
        self.assertIn("同一外部阻断连续三次 goal turn", combined)
        self.assertRegex(
            combined,
            r"首次出现.{0,80}(?:不得立即|不立即|只请求).{0,80}blocked",
        )
        for required in (
            "用户明确要求小样",
            "用户独占的必需输入",
            "AI WAV",
            "穷尽安全替代",
            "新凭据",
            "权限",
            "外部能力",
            "歌单",
            "排名",
            "歌手版本",
            "平台排除",
            "硬时长",
            "显式发布",
            "真人终验",
        ):
            with self.subTest(pause_boundary=required):
                self.assertIn(required, combined)

        for internal_recovery in (
            "普通公开下载",
            "备选源",
            "模型可安装",
            "TTS/ASR/sidecar",
            "render/mux",
            "manifest/evidence",
            "门禁 FAIL/REVIEW",
        ):
            with self.subTest(internal_recovery=internal_recovery):
                self.assertIn(internal_recovery, combined)

    def test_sandbox_delivery_has_no_unsolicited_release_or_rights_boilerplate(self) -> None:
        documents = {
            "AGENTS.md": (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8"),
            "CONVENTIONS.md": (REPO_ROOT / "CONVENTIONS.md").read_text(encoding="utf-8"),
            "README.md": (REPO_ROOT / "README.md").read_text(encoding="utf-8"),
            "tools/video/README.md": (VIDEO_ROOT / "README.md").read_text(encoding="utf-8"),
        }

        for label, document in documents.items():
            with self.subTest(document=label):
                self.assertIn("本地机械", document)
                self.assertIn("Sandbox 成片", document)
                self.assertIn("不得自动附加", document)
                self.assertIn("默认交付", document)
                self.assertIn("blocked", document)
                self.assertRegex(
                    document,
                    r"只有用户.{0,40}(?:主动询问|明确请求|明确要求)",
                )

        combined = "\n".join(documents.values())
        for forbidden in (
            "Copyright " + "stance",
            "素材" + "授权",
            "授权" + "评估",
            "版权" + "评估",
            "本地测试优先",
            "当前仅**本地测试**",
            "HUMAN REVIEW: PENDING",
            "profile=local_test",
            "human_review=pending",
        ):
            with self.subTest(forbidden_boilerplate=forbidden):
                self.assertNotIn(forbidden, combined)

        # Strict review remains an explicit opt-in capability, not a default
        # sandbox-delivery footer.
        self.assertIn("--require-human-review", combined)
        self.assertIn("REVIEW_REQUIRED", combined)
        self.assertIn(">1.5s", combined)
        self.assertRegex(combined, r"(?:不得|不能).{0,30}(?:伪造|冒充).{0,30}(?:人审|human)")

    def test_showcase_review_has_local_observation_and_human_release_modes(self) -> None:
        documents = {
            "AGENTS.md": (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8"),
            "CONVENTIONS.md": (REPO_ROOT / "CONVENTIONS.md").read_text(encoding="utf-8"),
            "README.md": (REPO_ROOT / "README.md").read_text(encoding="utf-8"),
            "tools/video/README.md": (VIDEO_ROOT / "README.md").read_text(encoding="utf-8"),
        }
        for label, document in documents.items():
            with self.subTest(document=label):
                self.assertIn("multi → 换窗 → 换源", document)
                self.assertIn("FAIL=0", document)
                self.assertIn("reviewer_kind=agent", document)
                self.assertIn("OBSERVED", document)
                self.assertIn("--require-human-review", document)
                self.assertIn("reviewer_kind=human", document)
                self.assertIn("APPROVED", document)

        combined = "\n".join(documents.values())
        self.assertIn("status=observed, reviewer_kind=agent", combined)
        self.assertIn("status=approved, reviewer_kind=human", combined)
        self.assertRegex(
            combined,
            r"OBSERVED.{0,80}(?:仅本地|local-only|local only)",
        )
        self.assertRegex(
            combined,
            r"--require-human-review.{0,100}(?:只接受|只认).{0,60}(?:human|reviewer_kind=human)",
        )
        self.assertRegex(
            combined,
            r"硬.{0,20}FAIL.{0,80}(?:不能|不可).{0,40}(?:覆盖|跳过)",
        )

    def test_final_qa_preparer_is_required_before_the_central_gate(self) -> None:
        documents = {
            "AGENTS.md": (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8"),
            "CONVENTIONS.md": (REPO_ROOT / "CONVENTIONS.md").read_text(encoding="utf-8"),
            "README.md": (REPO_ROOT / "README.md").read_text(encoding="utf-8"),
            "tools/video/README.md": (VIDEO_ROOT / "README.md").read_text(encoding="utf-8"),
        }

        self.assertIn(VIDEO_ROOT / "prepare_final_qa.py", REQUIRED_CLIS)
        for label, document in documents.items():
            with self.subTest(document=label):
                self.assertIn("tools/video/prepare_final_qa.py", document)
                self.assertIn("tools/video/verify_final_video.py", document)
                self.assertLess(
                    document.index("tools/video/prepare_final_qa.py"),
                    document.index("tools/video/verify_final_video.py"),
                )
                self.assertIn("qa/final-video-qa.json", document)
                self.assertIn("--human-review-input", document)
                self.assertIn("--require-human-review", document)
                self.assertIn("标准结构化盘点/叙事", document)
                self.assertIn("project_kind: free_exploration", document)
                self.assertIn("AI 音色 MV", document)
                self.assertRegex(document, r"(?:不强套|不得(?:强套|声称|冒充))")

        combined = "\n".join(documents.values())
        self.assertRegex(
            combined,
            r"(?:必须|运行|调用).{0,80}prepare_final_qa\.py",
        )
        self.assertRegex(
            combined,
            r"prepare_final_qa\.py.{0,240}同一进程.{0,240}(?:FINAL|gate)",
        )
        self.assertRegex(
            combined,
            r"--human-review-input.{0,120}--require-human-review",
        )

    def test_multi_goal_resource_budget_never_serializes_goals(self) -> None:
        documents = {
            "AGENTS.md": (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8"),
            "CONVENTIONS.md": (REPO_ROOT / "CONVENTIONS.md").read_text(encoding="utf-8"),
            "README.md": (REPO_ROOT / "README.md").read_text(encoding="utf-8"),
            "tools/video/README.md": (VIDEO_ROOT / "README.md").read_text(
                encoding="utf-8"
            ),
        }

        for label, document in documents.items():
            with self.subTest(document=label):
                lowered = document.lower()
                self.assertIn("多个 goal", lowered)
                self.assertRegex(lowered, r"(?:同时|持续).{0,30}(?:推进|继续|并发)")
                self.assertIn("4 → 3 → 2", document)
                self.assertIn("resource_budget.py", document)
                self.assertIn("1–4", document)
                self.assertRegex(
                    lowered,
                    r"(?:禁止|不得|不建立).{0,80}(?:全局|跨 goal).{0,80}"
                    r"(?:锁|semaphore|队列|等待)",
                )
                self.assertIn("同一进程", document)
                self.assertRegex(lowered, r"(?:standalone|独立复核|独立机械复核)")
                self.assertRegex(lowered, r"(?:不要|不得|不再).{0,80}(?:重复|立刻再跑)")

        combined = "\n".join(documents.values())
        for required in (
            "resource_budget.py",
            "Metal preflight",
            "CC_MEDIA_ASR_THREADS=1..4",
            "CC_MEDIA_FFMPEG_THREADS=1..4",
            "CC_MEDIA_HYPERFRAMES_WORKERS=1..4",
            "不 import MLX",
            "不信任项目内自报 diagnostics",
        ):
            with self.subTest(required=required):
                self.assertIn(required, combined)
        self.assertRegex(
            combined,
            r"(?:不得|禁止).{0,60}(?:直接调用裸|直接运行裸).{0,30}whisper",
        )
        self.assertRegex(combined, r"PID.{0,40}(?:启动|start)")
        self.assertRegex(combined, r"注册表.{0,40}(?:回退|fallback).{0,20}2")
        self.assertNotRegex(combined, r"--workers\s+auto")

    def test_canonical_cookie_is_user_owned_and_yt_dlp_is_readonly(self) -> None:
        documents = {
            "AGENTS.md": (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8"),
            "CONVENTIONS.md": (REPO_ROOT / "CONVENTIONS.md").read_text(
                encoding="utf-8"
            ),
            "README.md": (REPO_ROOT / "README.md").read_text(encoding="utf-8"),
            "tools/video/README.md": (VIDEO_ROOT / "README.md").read_text(
                encoding="utf-8"
            ),
        }

        for label, document in documents.items():
            with self.subTest(document=label):
                self.assertIn("all_cookies.txt", document)
                self.assertIn("canonical", document)
                self.assertRegex(
                    document,
                    r"(?:仅用户|只有用户|只由用户|用户本人).{0,40}(?:覆盖|维护)",
                )
                self.assertIn("yt_dlp_readonly.py", document)
                self.assertIn(
                    "python3 tools/video/yt_dlp_readonly.py -- <yt-dlp 参数>",
                    document,
                )
                self.assertIn("不要求不可变锁", document)
                for prohibited in (
                    "chmod",
                    "touch",
                    "mv",
                    "cp",
                ):
                    self.assertIn(prohibited, document)
                self.assertNotIn("chflags", document)
                self.assertNotIn("解锁", document)
                self.assertRegex(
                    document,
                    r"(?:代理|普通 goal).{0,100}(?:禁止|不得).{0,100}"
                    r"(?:filter_cookie_jar|过滤|安装)",
                )
                self.assertIn("仓库外", document)
                self.assertIn("candidate", document)
                self.assertRegex(
                    document,
                    r"Cookie.{0,80}(?:不可用|缺失|异常|失效).{0,100}"
                    r"(?:继续|不得因此).{0,60}goal",
                )

        combined = "\n".join(documents.values())
        self.assertIn(
            "python3 tools/video/filter_cookie_jar.py SOURCE --output "
            "/absolute/outside/candidate.txt",
            combined,
        )
        self.assertRegex(
            combined,
            r"yt-dlp --cookies FILE.{0,120}(?:回写|重新序列化)",
        )
        self.assertNotRegex(
            combined,
            r"(?m)^\s*yt-dlp[^\n]*--cookies[^\n]*all_cookies\.txt",
        )


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
        self.assertIn("当前标准：模型先按作品情绪与叙事表达选择", formal_page)
        self.assertIn("标准池共 10 个声音（8 女 2 男）", formal_page)
        self.assertIn("Legacy Kokoro", formal_page)


if __name__ == "__main__":
    unittest.main()
