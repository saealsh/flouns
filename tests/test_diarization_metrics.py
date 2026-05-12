"""اختبارات وحدة لـ src.diarization.metrics."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from src.diarization.metrics import (
    diarization_error_rate,
    speaker_purity_coverage,
)


class TestDER:
    def test_perfect_match_zero_der(self):
        ref = [(0.0, 2.0, "alice"), (2.0, 4.0, "bob")]
        hyp = [(0.0, 2.0, "spk1"), (2.0, 4.0, "spk2")]  # أسماء مختلفة لكن نفس التقسيم
        result = diarization_error_rate(hyp, ref)
        assert result["der"] < 0.01

    def test_perfect_match_with_correct_mapping(self):
        ref = [(0.0, 2.0, "alice"), (2.0, 4.0, "bob")]
        hyp = [(0.0, 2.0, "alice"), (2.0, 4.0, "bob")]
        result = diarization_error_rate(hyp, ref)
        assert result["der"] == 0.0
        assert result["mapping"]["alice"] == "alice"
        assert result["mapping"]["bob"] == "bob"

    def test_complete_miss_high_der(self):
        ref = [(0.0, 2.0, "alice"), (2.0, 4.0, "bob")]
        hyp = []
        result = diarization_error_rate(hyp, ref)
        assert result["der"] == 1.0
        assert result["miss"] == pytest.approx(4.0, abs=0.05)

    def test_false_alarm(self):
        ref = []
        hyp = [(0.0, 2.0, "spk1")]
        result = diarization_error_rate(hyp, ref)
        assert result["false_alarm"] == pytest.approx(2.0, abs=0.05)
        # المرجع فارغ → التعريف يجعل DER يساوي 1.0

    def test_speaker_confusion(self):
        ref = [(0.0, 2.0, "alice"), (2.0, 4.0, "bob")]
        # كل شيء نُسب لـ alice
        hyp = [(0.0, 4.0, "alice")]
        result = diarization_error_rate(hyp, ref)
        # تقريباً 2 ثانية confusion (bob → alice)
        assert result["confusion"] > 1.5

    def test_returns_required_keys(self):
        ref = [(0.0, 1.0, "a")]
        hyp = [(0.0, 1.0, "x")]
        result = diarization_error_rate(hyp, ref)
        required = {"der", "false_alarm", "miss", "confusion", "total_ref_sec", "mapping"}
        assert required <= set(result.keys())

    def test_empty_inputs(self):
        result = diarization_error_rate([], [])
        assert result["der"] == 0.0

    def test_collar_reduces_errors(self):
        # تشويش بسيط على حدود segments
        ref = [(0.0, 2.0, "a"), (2.0, 4.0, "b")]
        hyp = [(0.0, 2.1, "a"), (2.1, 4.0, "b")]  # حد متأخر 100ms

        no_collar = diarization_error_rate(hyp, ref, collar_sec=0.0)
        with_collar = diarization_error_rate(hyp, ref, collar_sec=0.25)
        assert with_collar["der"] <= no_collar["der"]

    def test_accepts_dict_input(self):
        ref = [{"start": 0.0, "end": 1.0, "label": "a"}]
        hyp = [{"start": 0.0, "end": 1.0, "speaker": "x"}]
        result = diarization_error_rate(hyp, ref)
        assert result["der"] < 0.01


class TestPurityCoverage:
    def test_perfect_returns_one(self):
        ref = [(0.0, 2.0, "a"), (2.0, 4.0, "b")]
        hyp = [(0.0, 2.0, "x"), (2.0, 4.0, "y")]
        m = speaker_purity_coverage(hyp, ref)
        assert m["purity"] > 0.95
        assert m["coverage"] > 0.95

    def test_over_clustering_low_purity(self):
        # متحدثان دُمجا في cluster واحد
        ref = [(0.0, 2.0, "a"), (2.0, 4.0, "b")]
        hyp = [(0.0, 4.0, "everyone")]
        m = speaker_purity_coverage(hyp, ref)
        assert m["purity"] < 0.6  # خلط بين متحدثين
        assert m["coverage"] > 0.9  # كل متحدث في cluster واحد (وإن مختلطاً)

    def test_over_splitting_low_coverage(self):
        # متحدث واحد قُسِّم لعدة clusters
        ref = [(0.0, 4.0, "a")]
        hyp = [(0.0, 1.0, "x"), (1.0, 2.0, "y"), (2.0, 3.0, "z"), (3.0, 4.0, "w")]
        m = speaker_purity_coverage(hyp, ref)
        assert m["purity"] > 0.9  # كل cluster نقي
        assert m["coverage"] < 0.4  # لكن المتحدث مبعثر


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
