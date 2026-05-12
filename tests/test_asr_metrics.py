"""اختبارات وحدة لـ src.asr.metrics."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from src.asr.metrics import (
    compute_cer,
    compute_wer,
    evaluate_transcript,
    speaker_attribution_accuracy,
)


class TestWER:
    def test_perfect_match_zero_wer(self):
        r = compute_wer("السلام عليكم", "السلام عليكم")
        assert r.error_rate == 0.0
        assert r.substitutions == r.deletions == r.insertions == 0

    def test_complete_mismatch_high_wer(self):
        r = compute_wer("السلام عليكم", "أهلا وسهلا")
        # 2 كلمات استبدال على 2 كلمات مرجع = 100%
        assert r.error_rate == 1.0

    def test_insertion(self):
        r = compute_wer("السلام عليكم", "السلام عليكم ورحمة الله")
        # 2 إضافات على 2 كلمات مرجع = 100%
        assert r.insertions == 2
        assert r.error_rate == 1.0

    def test_deletion(self):
        r = compute_wer("السلام عليكم ورحمة الله", "السلام عليكم")
        # 2 حذف على 4 كلمات = 50%
        assert r.deletions == 2
        assert r.error_rate == 0.5

    def test_substitution(self):
        r = compute_wer("السلام عليكم", "السلام جميعاً")
        assert r.substitutions == 1
        assert r.error_rate == 0.5

    def test_empty_reference(self):
        r = compute_wer("", "بعض الكلمات هنا")
        assert r.error_rate == 1.0
        assert r.insertions == 3

    def test_both_empty(self):
        r = compute_wer("", "")
        assert r.error_rate == 0.0

    def test_normalization_removes_diacritics(self):
        # المرجع بحركات، التفريغ بدون
        r1 = compute_wer("الْعَرَبِيَّة", "العربية")
        # بعد التطبيع، يجب أن يكون متطابقاً
        assert r1.error_rate == 0.0

    def test_normalization_unifies_alef(self):
        r = compute_wer("أحمد ذهب", "احمد ذهب")
        # بعد التطبيع، أ → ا
        assert r.error_rate == 0.0


class TestCER:
    def test_perfect_match(self):
        r = compute_cer("مرحبا", "مرحبا")
        assert r.error_rate == 0.0

    def test_one_char_substitution(self):
        # 5 حروف، خطأ واحد → 20%
        r = compute_cer("مرحبا", "مرحبه")
        assert abs(r.error_rate - 0.2) < 0.01

    def test_cer_lower_than_wer_for_partial_matches(self):
        # كلمة شبه صحيحة: WER عالٍ، CER منخفض
        ref = "السلام عليكم"
        hyp = "السلامو عليكم"  # كلمة واحدة بحرف زائد
        wer = compute_wer(ref, hyp).error_rate
        cer = compute_cer(ref, hyp).error_rate
        assert cer < wer

    def test_empty_inputs(self):
        r = compute_cer("", "")
        assert r.error_rate == 0.0


class TestSpeakerAttribution:
    def test_perfect_attribution(self):
        ref = [
            {"start": 0.0, "end": 2.0, "speaker_id": "alice"},
            {"start": 2.0, "end": 4.0, "speaker_id": "bob"},
        ]
        hyp = [
            {"start": 0.0, "end": 2.0, "speaker_id": "SPK_01"},
            {"start": 2.0, "end": 4.0, "speaker_id": "SPK_02"},
        ]
        result = speaker_attribution_accuracy(hyp, ref)
        # رغم اختلاف الأسماء، التطابق الأمثل يجد التوافق
        assert result["accuracy"] > 0.95

    def test_complete_confusion(self):
        ref = [
            {"start": 0.0, "end": 2.0, "speaker_id": "alice"},
            {"start": 2.0, "end": 4.0, "speaker_id": "bob"},
        ]
        hyp = [
            {"start": 0.0, "end": 4.0, "speaker_id": "everyone"},
        ]
        result = speaker_attribution_accuracy(hyp, ref)
        # نصف الوقت صحيح، نصفه خطأ → ~50%
        assert result["accuracy"] < 0.6

    def test_empty_returns_zero(self):
        result = speaker_attribution_accuracy([], [])
        assert result["accuracy"] == 0.0


class TestEvaluateTranscript:
    def test_returns_all_metrics(self):
        result = evaluate_transcript(
            reference_text="السلام عليكم",
            hypothesis_text="السلام عليكم",
        )
        assert "wer" in result
        assert "cer" in result
        assert "summary" in result
        assert result["summary"]["wer_percent"] == 0.0

    def test_with_segments(self):
        result = evaluate_transcript(
            reference_text="السلام عليكم",
            hypothesis_text="السلام عليكم",
            reference_segments=[{"start": 0, "end": 1, "speaker_id": "a"}],
            hypothesis_segments=[{"start": 0, "end": 1, "speaker_id": "x"}],
        )
        assert result["speaker_attribution"] is not None
        assert result["summary"]["saa_percent"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
