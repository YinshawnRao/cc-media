import json
import os
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

    def approval(self, **window_changes):
        window = {**self.window, **window_changes}
        return {"song": {
            "status": "approved",
            "clip": "clip",
            "analysis_sha256": align._analysis_fingerprint(self.vocals["clip"]),
            "window": window,
            "reason": "已试听确认是目标歌手且句尾完整",
            "evidence": ["qa/song-window.mp3", "人工复核记录 2026-07-15"],
        }}

    def test_review_blocks_even_with_legacy_global_override(self):
        with mock.patch.dict(os.environ, {"SHOWCASE_OVERRIDE": "1"}):
            with self.assertRaises(SystemExit):
                align.gate(self.blocks, self.vocals, verbose=False)

    def test_exact_window_per_song_approval_passes(self):
        rows = align.gate(
            self.blocks,
            self.vocals,
            approvals=self.approval(),
            verbose=False,
        )
        self.assertEqual("APPROVED", rows[0][1])

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
        self.assertEqual("clip", item["clip"])
        self.assertRegex(item["analysis_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(40.0, item["window"]["show_end_src"])


if __name__ == "__main__":
    unittest.main()
