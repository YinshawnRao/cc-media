import contextlib
import io
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

try:
    from tools.video import vocal_segments as vocal
except (ImportError, ModuleNotFoundError):  # 系统 Python 可能没有 librosa；真实环境用 tools/tts/venv。
    vocal = None


def asr_segment(text, chars, start=0.0, step=0.4):
    words = []
    for idx, char in enumerate(chars):
        words.append({
            "word": char,
            "start": start + idx * step,
            "end": start + (idx + 1) * step,
            "probability": 0.8,
        })
    return {
        "text": text,
        "start": start,
        "end": start + len(chars) * step,
        "words": words,
        "avg_logprob": -0.7,
        "no_speech_prob": 0.9,
    }


def set_confidence(segment, probability, avg_logprob):
    segment["avg_logprob"] = avg_logprob
    for word in segment["words"]:
        word["probability"] = probability
    return segment


@unittest.skipIf(vocal is None, "audio-analysis dependencies are unavailable")
class LexicalEvidenceTests(unittest.TestCase):
    @staticmethod
    def successful_result(*, whisper="available"):
        return {
            "duration": 1.0,
            "candidate_segments": [],
            "vocal_segments": [],
            "lead_segments": [],
            "segment_scores": [],
            "evidence_level": "multi_evidence" if whisper == "available" else "candidate",
            "capabilities": {"whisper": whisper},
        }

    def test_known_subtitle_hallucination_is_removed(self):
        result = {"segments": [asr_segment("字幕by索兰娅", list("字幕by索兰娅"))]}
        groups, rejected = vocal._group_asr_segments(result)
        self.assertEqual([], groups)
        self.assertEqual(1, len(rejected))

    def test_four_character_false_phrase_cannot_be_strong_positive(self):
        result = {"segments": [asr_segment("任何时代", list("任何时代"), step=0.7)]}
        groups, _ = vocal._group_asr_segments(result)
        self.assertEqual(1, len(groups))
        self.assertFalse(groups[0]["lexical_positive"])
        self.assertLess(groups[0]["units"], vocal.LEXICAL_MIN_UNITS)

    def test_dense_lyrics_are_strong_positive_even_with_high_no_speech(self):
        result = {"segments": [asr_segment("每晚我要分析岁月", list("每晚我要分析岁月"))]}
        groups, _ = vocal._group_asr_segments(result)
        self.assertTrue(groups[0]["lexical_positive"])
        # no_speech_prob 只记录，不参与正负判定。
        self.assertEqual(0.9, groups[0]["items"][0]["no_speech_prob"])

    def test_zero_confidence_dense_hallucination_stays_review(self):
        raw = asr_segment("天青色等烟雨", list("天青色等烟雨"))
        groups, _ = vocal._group_asr_segments({
            "segments": [set_confidence(raw, probability=0.0, avg_logprob=-8.0)]})
        self.assertTrue(groups[0]["lexical_content_positive"])
        self.assertTrue(groups[0]["confidence_conflict"])
        self.assertFalse(groups[0]["lexical_positive"])

    def test_safe_cut_intervals_require_release_and_real_gap(self):
        intervals = vocal._safe_intervals([[0.0, 5.0], [5.6, 10.0], [13.0, 15.0]], 20.0)
        # 0.6s 词间隙不足，不产生出点；3s gap 和末段会产生。
        self.assertEqual([[10.3, 12.85], [15.3, 17.5]], intervals)

    def test_whisper_model_load_applies_budget_before_loading_checkpoint(self):
        events = []
        fake_torch = types.ModuleType("torch")
        fake_whisper = types.ModuleType("whisper")
        fake_whisper._ALIGNMENT_HEADS = {}

        def fake_load_model(_checkpoint, *, device):
            events.append(("load", device))
            return object()

        fake_whisper.load_model = fake_load_model
        with mock.patch.object(vocal, "_whisper_cache_exists", return_value=True), \
                mock.patch.dict(
                    sys.modules,
                    {"torch": fake_torch, "whisper": fake_whisper},
                ), mock.patch.object(
                    vocal.resource_budget,
                    "configure_torch_runtime",
                    side_effect=lambda *_: events.append(("budget", "cpu")),
                ):
            vocal.load_whisper_model("small", "cpu")
        self.assertEqual([("budget", "cpu"), ("load", "cpu")], events)

    def test_multi_mode_inference_failure_returns_nonzero(self):
        failed = {
            "duration": 1.0,
            "candidate_segments": [],
            "vocal_segments": [],
            "lead_segments": [],
            "segment_scores": [],
            "evidence_level": "candidate",
            "capabilities": {"whisper": "failed"},
        }
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "source.wav"
            output = Path(td) / "analysis.json"
            source.write_bytes(b"placeholder")
            argv = [
                "vocal_segments.py", "--mode", "multi", "-o", str(output), str(source)]
            with mock.patch.object(sys, "argv", argv), \
                    mock.patch.object(vocal, "load_whisper_model", return_value=object()), \
                    mock.patch.object(vocal, "analyze", return_value=failed):
                self.assertEqual(2, vocal.main())
            self.assertFalse(output.exists())

    def test_default_mode_is_fail_closed_when_whisper_is_unavailable(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "source.wav"
            output = Path(td) / "analysis.json"
            source.write_bytes(b"placeholder")
            argv = ["vocal_segments.py", "-o", str(output), str(source)]
            stderr = io.StringIO()
            secret = "synthetic-model-detail-must-not-leak"
            with mock.patch.object(sys, "argv", argv), \
                    mock.patch.object(
                        vocal,
                        "load_whisper_model",
                        side_effect=FileNotFoundError(secret),
                    ), contextlib.redirect_stderr(stderr):
                self.assertEqual(2, vocal.main())
            self.assertFalse(output.exists())
            self.assertNotIn(secret, stderr.getvalue())
            self.assertIn("修复环境", stderr.getvalue())

    def test_all_missing_inputs_fail_before_model_load_and_write_nothing(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "analysis.json"
            missing = Path(td) / "missing.wav"
            argv = ["vocal_segments.py", "-o", str(output), str(missing)]
            with mock.patch.object(sys, "argv", argv), \
                    mock.patch.object(vocal, "load_whisper_model") as load_model:
                self.assertEqual(2, vocal.main())
            load_model.assert_not_called()
            self.assertFalse(output.exists())

    def test_unanalyzable_input_returns_nonzero_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "broken.wav"
            output = Path(td) / "analysis.json"
            source.write_bytes(b"not audio")
            argv = ["vocal_segments.py", "-o", str(output), str(source)]
            stderr = io.StringIO()
            secret = "synthetic-decoder-detail-must-not-leak"
            with mock.patch.object(sys, "argv", argv), \
                    mock.patch.object(vocal, "load_whisper_model", return_value=object()), \
                    mock.patch.object(vocal, "analyze", side_effect=ValueError(secret)), \
                    contextlib.redirect_stderr(stderr):
                self.assertEqual(2, vocal.main())
            self.assertFalse(output.exists())
            self.assertNotIn(secret, stderr.getvalue())

    def test_failure_preserves_but_explicitly_rejects_stale_output(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "broken.wav"
            output = Path(td) / "analysis.json"
            source.write_bytes(b"not audio")
            output.write_text("stale-sentinel", encoding="utf-8")
            stderr = io.StringIO()
            argv = ["vocal_segments.py", "-o", str(output), str(source)]
            with mock.patch.object(sys, "argv", argv), \
                    mock.patch.object(vocal, "load_whisper_model", return_value=object()), \
                    mock.patch.object(vocal, "analyze", side_effect=ValueError("decode failed")), \
                    contextlib.redirect_stderr(stderr):
                self.assertEqual(2, vocal.main())
            self.assertEqual("stale-sentinel", output.read_text(encoding="utf-8"))
            self.assertIn("属于旧结果", stderr.getvalue())
            self.assertIn("不得据本次失败继续 build", stderr.getvalue())

    def test_mixed_valid_and_missing_inputs_do_not_write_partial_output(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "source.wav"
            missing = Path(td) / "missing.wav"
            output = Path(td) / "analysis.json"
            source.write_bytes(b"placeholder")
            argv = [
                "vocal_segments.py",
                "-o",
                str(output),
                str(source),
                str(missing),
            ]
            with mock.patch.object(sys, "argv", argv), \
                    mock.patch.object(vocal, "load_whisper_model", return_value=object()), \
                    mock.patch.object(
                        vocal,
                        "analyze",
                        return_value=self.successful_result(),
                    ):
                self.assertEqual(2, vocal.main())
            self.assertFalse(output.exists())

    def test_combined_output_rejects_same_stem_before_analysis_or_write(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            first = root / "source-a" / "same.wav"
            second = root / "source-b" / "same.mp4"
            output = root / "analysis.json"
            first.parent.mkdir()
            second.parent.mkdir()
            first.write_bytes(b"placeholder-a")
            second.write_bytes(b"placeholder-b")
            output.write_text("stale-sentinel", encoding="utf-8")
            stderr = io.StringIO()
            argv = [
                "vocal_segments.py",
                "-o",
                str(output),
                str(first),
                str(second),
            ]
            with mock.patch.object(sys, "argv", argv), \
                    mock.patch.object(vocal, "load_whisper_model") as load_model, \
                    mock.patch.object(vocal, "analyze") as analyze, \
                    mock.patch.object(Path, "write_text") as write_text, \
                    contextlib.redirect_stderr(stderr):
                self.assertEqual(2, vocal.main())
            load_model.assert_not_called()
            analyze.assert_not_called()
            write_text.assert_not_called()
            self.assertEqual("stale-sentinel", output.read_text(encoding="utf-8"))
            self.assertIn(
                "合并输出 key 冲突：1 组输入使用了相同 stem",
                stderr.getvalue(),
            )
            self.assertIn("属于旧结果", stderr.getvalue())
            self.assertIn("不得据本次失败继续 build", stderr.getvalue())
            self.assertNotIn(first.name, stderr.getvalue())
            self.assertNotIn(second.name, stderr.getvalue())
            self.assertNotIn(str(first.parent), stderr.getvalue())
            self.assertNotIn(str(second.parent), stderr.getvalue())

    def test_explicit_acoustic_mode_remains_supported(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "source.wav"
            output = Path(td) / "analysis.json"
            source.write_bytes(b"placeholder")
            argv = [
                "vocal_segments.py",
                "--mode",
                "acoustic",
                "-o",
                str(output),
                str(source),
            ]
            with mock.patch.object(sys, "argv", argv), \
                    mock.patch.object(vocal, "load_whisper_model") as load_model, \
                    mock.patch.object(
                        vocal,
                        "analyze",
                        return_value=self.successful_result(whisper="not_run"),
                    ):
                self.assertEqual(0, vocal.main())
            load_model.assert_not_called()
            self.assertTrue(output.is_file())
            self.assertIn("source", output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
