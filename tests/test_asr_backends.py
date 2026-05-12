"""اختبارات وحدة لـ src.asr.backends."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pytest

from src.asr.backends import (
    MockASRBackend,
    TranscriptionResult,
    TranscriptionSegment,
    WordTiming,
    get_backend,
)

SR = 16000


def make_audio(duration: float) -> np.ndarray:
    t = np.linspace(0, duration, int(SR * duration), endpoint=False)
    return (0.3 * np.sin(2 * np.pi * 200 * t)).astype(np.float32)


class TestDataClasses:
    def test_word_timing_to_dict(self):
        w = WordTiming(word="مرحباً", start=1.234, end=2.345, confidence=0.95)
        d = w.to_dict()
        assert d["word"] == "مرحباً"
        assert d["start"] == 1.234
        assert d["confidence"] == 0.95

    def test_segment_duration(self):
        s = TranscriptionSegment(start=1.0, end=4.5, text="x")
        assert s.duration == 3.5

    def test_segment_to_dict_includes_words(self):
        words = [WordTiming("a", 0, 1), WordTiming("b", 1, 2)]
        s = TranscriptionSegment(start=0, end=2, text="a b", words=words)
        d = s.to_dict()
        assert len(d["words"]) == 2

    def test_result_full_text(self):
        result = TranscriptionResult(
            segments=[
                TranscriptionSegment(0, 1, "السلام"),
                TranscriptionSegment(1, 2, "عليكم"),
            ]
        )
        assert result.full_text == "السلام عليكم"

    def test_result_avg_confidence_weighted_by_duration(self):
        result = TranscriptionResult(
            segments=[
                TranscriptionSegment(0, 1, "a", avg_confidence=0.5),
                TranscriptionSegment(1, 4, "b", avg_confidence=1.0),  # 3 أضعاف الوزن
            ]
        )
        # 0.5*1 + 1.0*3 = 3.5، /4 = 0.875
        assert abs(result.avg_confidence - 0.875) < 0.01

    def test_empty_result_zero_confidence(self):
        result = TranscriptionResult()
        assert result.avg_confidence == 0.0


class TestMockBackend:
    def test_returns_valid_result(self):
        backend = MockASRBackend(mock_text="test")
        result = backend.transcribe(make_audio(2.0), SR)
        assert isinstance(result, TranscriptionResult)
        assert result.language == "ar"
        assert len(result.segments) >= 1

    def test_segments_cover_duration(self):
        backend = MockASRBackend()
        result = backend.transcribe(make_audio(7.5), SR, segment_duration=3.0)
        # 7.5 / 3.0 = 2.5 → 3 قطع
        assert len(result.segments) == 3
        # آخر قطعة تنتهي عند 7.5
        assert abs(result.segments[-1].end - 7.5) < 0.1

    def test_empty_audio_empty_result(self):
        backend = MockASRBackend()
        result = backend.transcribe(np.array([], dtype=np.float32), SR)
        assert len(result.segments) == 0

    def test_words_have_timestamps(self):
        backend = MockASRBackend(mock_text="كلمة أخرى ثالثة")
        result = backend.transcribe(make_audio(3.0), SR)
        seg = result.segments[0]
        assert len(seg.words) == 3
        # كل كلمة لها start و end
        for w in seg.words:
            assert w.end > w.start


class TestGetBackend:
    def test_mock_default(self):
        backend = get_backend("mock")
        assert isinstance(backend, MockASRBackend)

    def test_unknown_raises(self):
        with pytest.raises(ValueError):
            get_backend("unknown")  # type: ignore

    def test_openai_not_implemented(self):
        with pytest.raises(NotImplementedError):
            get_backend("openai-whisper")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
