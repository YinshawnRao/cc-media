import sys
import tempfile
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


if __name__ == "__main__":
    unittest.main()
