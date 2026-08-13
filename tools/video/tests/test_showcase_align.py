import json
import math
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.video import showcase_align as align


def analysis(segments, *, evidence="candidate", safe=()):
    return {
        "schema_version": 2,
        "detector": "test",
        "evidence_level": evidence,
        "lead_segments": segments,
        "boundary_evidence": "whisper_word_timestamps",
        "safe_cut_intervals": list(safe),
    }


class VerifySongTests(unittest.TestCase):
    def setUp(self):
        self.window = dict(
            key="song",
            clip="clip",
            narr_end_src=8.0,
            show_start_src=10.0,
            show_end_src=40.0,
        )

    def verify(self, value):
        return align.verify_song(value, **self.window)

    def test_legacy_energy_can_never_auto_pass(self):
        result = self.verify([[7.5, 39.7]])
        self.assertEqual("REVIEW", result["status"])
        self.assertEqual("legacy_energy", result["metrics"]["evidence_level"])

    def test_trusted_identity_without_safe_boundary_needs_review(self):
        result = self.verify(analysis([[7.5, 39.7]], evidence="multi_evidence"))
        self.assertEqual("REVIEW", result["status"])
        self.assertFalse(result["metrics"]["trusted_boundary"])

    def test_trusted_identity_and_safe_boundary_pass(self):
        value = analysis(
            [[7.5, 39.7]],
            evidence="multi_evidence",
            safe=[[39.95, 40.20]],
        )
        self.assertEqual("OK", self.verify(value)["status"])

    def test_active_vocal_tail_is_hard_failure(self):
        value = analysis(
            [[7.5, 41.0]],
            evidence="multi_evidence",
            safe=[[39.95, 40.20]],
        )
        result = self.verify(value)
        self.assertEqual("FAIL", result["status"])
        self.assertEqual("active_vocal", result["metrics"]["end_reason"])

    def test_short_gap_before_next_syllable_fails(self):
        value = analysis(
            [[7.5, 39.7], [41.5, 55.0]],
            evidence="multi_evidence",
            safe=[],
        )
        result = self.verify(value)
        self.assertEqual("FAIL", result["status"])
        self.assertEqual("imminent_next_onset", result["metrics"]["end_reason"])

    def test_verified_safe_interval_overrides_generic_lookahead(self):
        value = analysis(
            [[7.5, 39.7], [42.1, 55.0]],
            evidence="manual",
            safe=[[39.95, 40.20]],
        )
        result = self.verify(value)
        self.assertEqual("OK", result["status"])
        self.assertEqual(2.1, result["metrics"]["gap_to_next_onset"])

    def test_automatic_safe_interval_cannot_override_short_lookahead(self):
        value = analysis(
            [[7.5, 39.7], [40.85, 55.0]],
            evidence="multi_evidence",
            safe=[[40.0, 40.70]],
        )
        result = align.verify_song(
            value,
            narr_end_src=8.0,
            show_start_src=10.0,
            show_end_src=40.70,
        )
        self.assertEqual("FAIL", result["status"])
        self.assertEqual("imminent_next_onset", result["metrics"]["end_reason"])

    def test_intro_hard_restart_allows_long_instrumental_opening(self):
        value = analysis(
            [[30.0, 39.7]],
            evidence="multi_evidence",
            safe=[[39.95, 40.20]],
        )
        result = align.verify_song(
            value,
            narr_end_src=8.0,
            show_start_src=0.0,
            show_end_src=40.0,
            mode="intro_hard_restart",
        )
        self.assertEqual("OK", result["status"])
        self.assertEqual("intro_hard_restart", result["metrics"]["mode"])

    def test_intro_hard_restart_rejects_nonzero_show_start(self):
        value = analysis(
            [[30.0, 39.7]],
            evidence="multi_evidence",
            safe=[[39.95, 40.20]],
        )
        result = align.verify_song(
            value,
            narr_end_src=8.0,
            show_start_src=1.0,
            show_end_src=40.0,
            mode="intro_hard_restart",
        )
        self.assertEqual("FAIL", result["status"])

    def test_weak_word_boundary_still_prevents_cut(self):
        value = analysis(
            [[7.5, 39.7]],
            evidence="multi_evidence",
            safe=[[39.95, 40.20]],
        )
        value["boundary_segments"] = [[7.5, 39.7], [39.9, 40.8]]
        result = self.verify(value)
        self.assertEqual("FAIL", result["status"])
        self.assertEqual("active_vocal", result["metrics"]["end_reason"])

    def test_boundary_failure_stays_fail_when_lead_identity_is_unreliable(self):
        value = analysis([], evidence="candidate", safe=[])
        value["boundary_segments"] = [[39.9, 40.8]]
        result = self.verify(value)
        self.assertEqual("FAIL", result["status"])
        self.assertEqual("active_vocal", result["metrics"]["end_reason"])


class SafeEndTests(unittest.TestCase):
    def test_empty_boundary_data_never_crashes_or_auto_passes(self):
        cut, auto_safe, note = align._find_safe_end([], 10.0, 25.0)
        self.assertEqual(35.0, cut)
        self.assertFalse(auto_safe)
        self.assertIn("没有", note)

    def test_historical_short_gap_is_absorbed(self):
        # 《我在哭》旧切点 144.67 落在 2.03s 句内气口；应吞并下一小句。
        segments = [[114.47, 143.92], [146.70, 162.68]]
        cut, auto_safe, _ = align._find_safe_end(segments, 118.17, 25.0)
        self.assertTrue(auto_safe)
        self.assertAlmostEqual(162.98, cut, places=2)

        result = align.verify_song(
            segments,
            narr_end_src=116.47,
            show_start_src=118.17,
            show_end_src=round(cut, 2),
        )
        self.assertNotEqual("FAIL", result["status"])

    def test_old_historical_cut_is_rejected(self):
        result = align.verify_song(
            [[114.47, 143.92], [146.70, 162.68]],
            narr_end_src=116.47,
            show_start_src=118.17,
            show_end_src=144.67,
        )
        self.assertEqual("REVIEW", result["status"])
        self.assertNotEqual("OK", result["status"])
        self.assertEqual("imminent_next_onset", result["metrics"]["end_reason"])


class ApprovalGateTests(unittest.TestCase):
    def setUp(self):
        self.blocks = [{
            "key": "song",
            "clip": "clip",
            "start": 0.0,
            "narr_end": 8.0,
            "full_start": 10.0,
            "end": 40.0,
        }]
        self.vocals = {"clip": [[7.5, 39.7]]}
        self.window = {
            "narr_end_src": 8.0,
            "show_start_src": 10.0,
            "show_end_src": 40.0,
        }

    def approval(self, *, reviewer_kind="human", **window_changes):
        window = {**self.window, **window_changes}
        reason = (
            "multi、换窗和换源均已穷尽；代理工具辅助观察到目标歌手且句尾完整"
            if reviewer_kind == "agent"
            else "用户已试听确认是目标歌手且句尾完整"
        )
        evidence = (
            ["qa/song-window.mp3", "qa/tool-assisted-observation.txt"]
            if reviewer_kind == "agent"
            else ["qa/song-window.mp3", "用户复核记录 2026-07-15"]
        )
        return {"song": {
            "status": "observed" if reviewer_kind == "agent" else "approved",
            "reviewer_kind": reviewer_kind,
            "reviewer": f"fixture-{reviewer_kind}-reviewer",
            "reviewed_at": "2026-08-11T12:00:00+08:00",
            "clip": "clip",
            "analysis_sha256": align._analysis_fingerprint(self.vocals["clip"]),
            "window": window,
            "reason": reason,
            "evidence": evidence,
        }}

    def test_review_blocks_even_with_legacy_global_override(self):
        with mock.patch.dict(os.environ, {"SHOWCASE_OVERRIDE": "1"}):
            with self.assertRaises(SystemExit):
                align.gate(self.blocks, self.vocals, verbose=False)

    def test_all_blocking_states_direct_ordinary_goals_to_automatic_recovery(self):
        cases = {
            "MISS": {},
            "REVIEW": self.vocals,
            "FAIL": {"clip": analysis(
                [[7.5, 41.0]],
                evidence="multi_evidence",
                safe=[[41.3, 42.0]],
            )},
        }
        for expected_status, vocals in cases.items():
            with self.subTest(expected_status=expected_status):
                with self.assertRaises(SystemExit) as raised:
                    align.gate(self.blocks, vocals, verbose=False)
                message = str(raised.exception)
                self.assertIn("--mode multi", message)
                self.assertIn("换完整乐句窗", message)
                self.assertIn("换同版本", message)
                self.assertIn("硬 FAIL=0", message)
                self.assertIn("reviewer_kind=agent", message)
                self.assertIn("OBSERVED", message)
                self.assertIn("代理不得代签 human", message)
                self.assertNotIn("请人工复核", message)
                self.assertNotIn("经逐曲试听后", message)

    def test_exact_window_per_song_approval_passes(self):
        rows = align.gate(
            self.blocks,
            self.vocals,
            approvals=self.approval(),
            verbose=False,
        )
        self.assertEqual("APPROVED", rows[0][1])

        strict_rows = align.gate(
            self.blocks,
            self.vocals,
            approvals=self.approval(),
            verbose=False,
            require_human_review=True,
        )
        self.assertEqual("APPROVED", strict_rows[0][1])

    def test_agent_observation_passes_local_but_not_release(self):
        rows = align.gate(
            self.blocks,
            self.vocals,
            approvals=self.approval(reviewer_kind="agent"),
            verbose=False,
        )
        self.assertEqual("OBSERVED", rows[0][1])
        with self.assertRaises(SystemExit):
            align.gate(
                self.blocks,
                self.vocals,
                approvals=self.approval(reviewer_kind="agent"),
                verbose=False,
                require_human_review=True,
            )

    def test_check_cli_keeps_agent_observation_local_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan_path = root / "showcase_plan.json"
            vocals_path = root / "vocal_analysis.json"
            approvals_path = root / "showcase_approvals.json"
            plan_path.write_text(
                json.dumps({"songs": [{"key": "song", "clip": "clip", **self.window}]}),
                encoding="utf-8",
            )
            vocals_path.write_text(json.dumps(self.vocals), encoding="utf-8")
            approvals_path.write_text(
                json.dumps({
                    "schema_version": 1,
                    "approvals": self.approval(reviewer_kind="agent"),
                }),
                encoding="utf-8",
            )
            command = [
                sys.executable,
                str(Path(align.__file__)),
                "check",
                "--plan",
                str(plan_path),
                "--vocals",
                str(vocals_path),
                "--approvals",
                str(approvals_path),
            ]
            local = subprocess.run(command, text=True, capture_output=True, check=False)
            release = subprocess.run(
                [*command, "--require-human-review"],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(0, local.returncode, local.stderr)
        self.assertIn("OBSERVED", local.stdout)
        self.assertNotIn("真人逐曲复核批准", local.stdout)
        self.assertNotEqual(0, release.returncode)
        self.assertIn("REVIEW", release.stdout)
        self.assertIn("agent observation", release.stdout)

    def test_approval_requires_explicit_reviewer_metadata(self):
        for field, value in (
            ("reviewer_kind", None),
            ("reviewer_kind", "automation"),
            ("reviewer", ""),
            ("reviewed_at", "2026-08-11T12:00:00"),
        ):
            with self.subTest(field=field, value=value):
                approval = self.approval()
                approval["song"][field] = value
                accepted, error = align._validate_approval(
                    approval, "song", "clip",
                    expected_window=self.window,
                    expected_analysis=self.vocals["clip"],
                )
                self.assertIsNone(accepted)
                self.assertIn(field, error)

    def test_observation_and_approval_statuses_cannot_impersonate_each_other(self):
        for reviewer_kind, wrong_status, expected_status in (
            ("agent", "approved", "observed"),
            ("human", "observed", "approved"),
        ):
            with self.subTest(reviewer_kind=reviewer_kind):
                review = self.approval(reviewer_kind=reviewer_kind)
                review["song"]["status"] = wrong_status
                accepted, error = align._validate_approval(
                    review,
                    "song",
                    "clip",
                    expected_window=self.window,
                    expected_analysis=self.vocals["clip"],
                )
                self.assertIsNone(accepted)
                self.assertIn(f"status 必须为 {expected_status}", error)

    def test_non_finite_approval_window_never_matches(self):
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value):
                approval = self.approval(show_end_src=value)
                accepted, error = align._validate_approval(
                    approval, "song", "clip",
                    expected_window=self.window,
                    expected_analysis=self.vocals["clip"],
                )
                self.assertIsNone(accepted)
                self.assertIn("有限数值", error)

    def test_stale_approval_cannot_pass_changed_cut(self):
        with self.assertRaises(SystemExit):
            align.gate(
                self.blocks,
                self.vocals,
                approvals=self.approval(show_end_src=39.0),
                verbose=False,
            )

    def test_approval_cannot_mask_hard_boundary_failure(self):
        vocals = {"clip": analysis(
            [[7.5, 41.0]],
            evidence="multi_evidence",
            safe=[[41.3, 42.0]],
        )}
        approval = self.approval()
        approval["song"]["analysis_sha256"] = align._analysis_fingerprint(vocals["clip"])
        with self.assertRaises(SystemExit):
            align.gate(
                self.blocks,
                vocals,
                approvals=approval,
                verbose=False,
            )

    def test_changed_analysis_invalidates_old_approval(self):
        changed = {"clip": [[7.5, 39.6]]}
        with self.assertRaises(SystemExit):
            align.gate(
                self.blocks,
                changed,
                approvals=self.approval(),
                verbose=False,
            )


class LoaderAndTemplateTests(unittest.TestCase):
    def test_single_result_json_is_wrapped_by_name(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "clip.vocal.json"
            path.write_text(json.dumps({
                "name": "clip",
                "duration": 50.0,
                "vocal_segments": [[1.0, 5.0]],
            }), encoding="utf-8")
            loaded = align._load_analysis(path)
        self.assertEqual(["clip"], list(loaded))
        self.assertEqual([[1.0, 5.0]], loaded["clip"]["vocal_segments"])

    def test_strict_json_rejects_nan_and_duplicate_fields(self):
        with tempfile.TemporaryDirectory() as td:
            nan_path = Path(td) / "nan.json"
            nan_path.write_text('{"approvals":{"song":{"window":{"show_end_src":NaN}}}}',
                                encoding="utf-8")
            with self.assertRaises(ValueError):
                align._load_approvals(nan_path)

            duplicate_path = Path(td) / "duplicate.json"
            duplicate_path.write_text('{"approvals":{},"approvals":{}}', encoding="utf-8")
            with self.assertRaises(ValueError):
                align._load_approvals(duplicate_path)

    def test_empty_gate_and_check_fail_closed(self):
        with self.assertRaises(SystemExit):
            align.gate([], {}, verbose=False)
        with tempfile.TemporaryDirectory() as td:
            plan = Path(td) / "showcase_plan.json"
            plan.write_text(json.dumps({"songs": []}), encoding="utf-8")
            vocals = Path(td) / "vocal_analysis.json"
            vocals.write_text("{}", encoding="utf-8")
            args = type("Args", (), {
                "plan": str(plan), "vocals": str(vocals),
                "approvals": None, "clips": "clips",
                "require_human_review": False,
            })()
            self.assertNotEqual(0, align.cmd_check(args))

    def test_sibling_approval_is_ignored_without_explicit_argument(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            plan = root / "showcase_plan.json"
            plan.write_text(json.dumps({"songs": [{
                "key": "song",
                "clip": "clip",
                "narr_end_src": 8.0,
                "show_start_src": 10.0,
                "show_end_src": 40.0,
            }]}), encoding="utf-8")
            vocals = root / "vocal_analysis.json"
            analysis_payload = {"clip": [[7.5, 39.7]]}
            vocals.write_text(json.dumps(analysis_payload), encoding="utf-8")
            approval = {
                "schema_version": 1,
                "approvals": {
                    "song": {
                        "status": "approved",
                        "reviewer_kind": "human",
                        "reviewer": "fixture-human-reviewer",
                        "reviewed_at": "2026-08-11T12:00:00+08:00",
                        "clip": "clip",
                        "analysis_sha256": align._analysis_fingerprint(
                            analysis_payload["clip"]),
                        "window": {
                            "narr_end_src": 8.0,
                            "show_start_src": 10.0,
                            "show_end_src": 40.0,
                        },
                        "reason": "用户已完整试听",
                        "evidence": ["用户复核记录"],
                    }
                },
            }
            sibling = root / "showcase_approvals.json"
            sibling.write_text(json.dumps(approval), encoding="utf-8")
            base = {
                "plan": str(plan), "vocals": str(vocals), "clips": "clips",
                "require_human_review": False,
            }
            implicit_args = type("Args", (), {**base, "approvals": None})()
            explicit_args = type("Args", (), {**base, "approvals": str(sibling)})()
            with mock.patch("builtins.print"):
                self.assertNotEqual(0, align.cmd_check(implicit_args))
                self.assertEqual(0, align.cmd_check(explicit_args))

    def test_cmd_plan_review_does_not_claim_values_are_ready_for_build(self):
        with tempfile.TemporaryDirectory() as td:
            vocals = Path(td) / "vocal_analysis.json"
            vocals.write_text(json.dumps({"clip": analysis(
                [[10.0, 50.0]], evidence="candidate", safe=[[50.2, 50.5]],
            )}), encoding="utf-8")
            args = type("Args", (), {
                "vocals": str(vocals), "clip": "clip", "voice_dur": 10.0,
                "post": 0.25, "dig": 1.45, "near": None, "min_show": 25.0,
            })()
            with mock.patch("builtins.print") as output:
                self.assertNotEqual(0, align.cmd_plan(args))
            rendered = "\n".join(" ".join(map(str, call.args)) for call in output.call_args_list)
            self.assertIn("[REVIEW]", rendered)
            self.assertNotIn("填进 build", rendered)
            self.assertNotIn("可写入 build", rendered)

    def test_approval_template_is_pending_and_window_bound(self):
        with tempfile.TemporaryDirectory() as td:
            plan = Path(td) / "showcase_plan.json"
            plan.write_text(json.dumps({"songs": [{
                "key": "song",
                "clip": "clip",
                "narr_end_src": 8.0,
                "show_start_src": 10.0,
                "show_end_src": 40.0,
            }]}), encoding="utf-8")
            vocals = Path(td) / "vocal_analysis.json"
            vocals.write_text(json.dumps({"clip": {
                "name": "clip",
                "vocal_segments": [[7.5, 39.7]],
            }}), encoding="utf-8")
            args = type("Args", (), {
                "plan": str(plan), "vocals": str(vocals),
                "out": None, "force": False,
            })()
            self.assertEqual(0, align.cmd_approval_template(args))
            payload = json.loads(
                plan.with_name("showcase_approvals.json").read_text(encoding="utf-8"))
        item = payload["approvals"]["song"]
        self.assertEqual("pending", item["status"])
        self.assertIsNone(item["reviewer_kind"])
        self.assertEqual("", item["reviewer"])
        self.assertIsNone(item["reviewed_at"])
        self.assertEqual("clip", item["clip"])
        self.assertRegex(item["analysis_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(40.0, item["window"]["show_end_src"])
        self.assertIn("仅接受用户已完成逐曲复核", payload["instructions"])
        self.assertIn("代理或脚本不得填写", payload["instructions"])
        self.assertIn("不得代签", payload["instructions"])

    def test_cli_help_distinguishes_local_observation_from_human_release(self):
        script = Path(align.__file__)
        for command in ("check", "approval-template"):
            with self.subTest(command=command):
                completed = subprocess.run(
                    [sys.executable, str(script), command, "--help"],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(0, completed.returncode, completed.stderr)
                self.assertIn("代理不得代签", completed.stdout)
                if command == "check":
                    self.assertIn("reviewer_kind=agent", completed.stdout)
                    self.assertIn("--require-human-review", completed.stdout)
                else:
                    self.assertIn("用户", completed.stdout)


if __name__ == "__main__":
    unittest.main()
