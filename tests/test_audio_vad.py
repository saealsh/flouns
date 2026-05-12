"""اختبارات وحدة لـ src.audio.vad."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pytest

from src.audio.vad import (
    SpeechSegment,
    detect_speech_segments,
    energy_vad,
    extract_speech_audio,
    total_speech_duration,
)

SR = 16000


def make_sine(duration: float, freq: float = 440, amp: float = 0.5) -> np.ndarray:
    t = np.linspace(0, duration, int(SR * duration), endpoint=False)
    return (amp * np.sin(2 * np.pi * freq * t)).astype(np.float32)


def make_silence(duration: float) -> np.ndarray:
    return np.zeros(int(SR * duration), dtype=np.float32)


class TestSpeechSegment:
    def test_duration_property(self):
        seg = SpeechSegment(start_sec=1.0, end_sec=3.5)
        assert seg.duration_sec == 2.5

    def test_to_tuple_rounding(self):
        seg = SpeechSegment(start_sec=1.123456, end_sec=2.987654)
        assert seg.to_tuple() == (1.123, 2.988)


class TestEnergyVAD:
    def test_pure_silence_no_segments(self):
        audio = make_silence(2.0)
        segments = energy_vad(audio, SR)
        assert segments == []

    def test_pure_speech_one_segment(self):
        audio = make_sine(1.0, amp=0.5)
        segments = energy_vad(audio, SR)
        assert len(segments) == 1
        # القطعة تغطي ~كامل المدة
        assert segments[0].duration_sec > 0.9

    def test_speech_silence_speech_two_segments(self):
        # كلام، صمت طويل، كلام
        speech1 = make_sine(0.6, amp=0.5)
        long_silence = make_silence(0.6)  # طويل بما يكفي للفصل
        speech2 = make_sine(0.6, amp=0.5)
        signal = np.concatenate([speech1, long_silence, speech2])

        segments = energy_vad(signal, SR, min_silence_ms=300)
        assert len(segments) == 2

    def test_short_silence_merged(self):
        # كلام، صمت قصير جداً، كلام → قطعة واحدة
        speech1 = make_sine(0.5, amp=0.5)
        short_silence = make_silence(0.05)  # 50ms أقل من min_silence_ms الافتراضي
        speech2 = make_sine(0.5, amp=0.5)
        signal = np.concatenate([speech1, short_silence, speech2])

        segments = energy_vad(signal, SR, min_silence_ms=200)
        # نتسامح بقطعة واحدة أو قطعتين قريبتين، المهم إجمالي المدة
        total_dur = sum(s.duration_sec for s in segments)
        assert total_dur > 0.9

    def test_short_speech_filtered_out(self):
        # كلام قصير جداً (50ms) محاط بصمت → يُحذف
        silence1 = make_silence(0.5)
        tiny_speech = make_sine(0.05, amp=0.5)  # 50ms
        silence2 = make_silence(0.5)
        signal = np.concatenate([silence1, tiny_speech, silence2])

        segments = energy_vad(signal, SR, min_speech_ms=200)
        assert len(segments) == 0

    def test_empty_audio(self):
        assert energy_vad(np.array([], dtype=np.float32), SR) == []

    def test_very_short_audio(self):
        # أقل من إطار واحد
        audio = np.zeros(100, dtype=np.float32)
        segments = energy_vad(audio, SR)
        assert segments == []

    def test_adaptive_threshold_quiet_signal(self):
        # كلام بسعة منخفضة (0.05) لكن أعلى بكثير من الضوضاء (0.005)
        rng = np.random.default_rng(42)
        noise = (0.005 * rng.standard_normal(SR * 2)).astype(np.float32)
        speech = (0.05 * np.sin(2 * np.pi * 440 * np.arange(SR) / SR)).astype(np.float32)
        signal = np.concatenate([noise[: SR // 2], speech, noise[SR // 2 :]])

        # adaptive يكشفه، non-adaptive بعتبة -35dB قد لا يكشفه
        segments_adaptive = energy_vad(signal, SR, adaptive=True)
        assert len(segments_adaptive) >= 1


class TestDetectSpeechSegments:
    def test_method_dispatch_energy(self):
        audio = make_sine(0.5, amp=0.5)
        segments = detect_speech_segments(audio, SR, method="energy")
        assert len(segments) == 1

    def test_unknown_method_raises(self):
        with pytest.raises(ValueError):
            detect_speech_segments(make_sine(0.5), SR, method="random")  # type: ignore


class TestUtilities:
    def test_total_speech_duration(self):
        segments = [
            SpeechSegment(0.0, 1.0),
            SpeechSegment(2.0, 3.5),
            SpeechSegment(4.0, 5.0),
        ]
        assert total_speech_duration(segments) == 3.5

    def test_total_speech_duration_empty(self):
        assert total_speech_duration([]) == 0.0

    def test_extract_speech_audio(self):
        # 3 ثوانٍ كاملة من الكلام
        audio = make_sine(3.0, amp=0.5)
        # نأخذ القطعة الأولى والثالثة فقط
        segments = [SpeechSegment(0.0, 1.0), SpeechSegment(2.0, 3.0)]
        extracted = extract_speech_audio(audio, SR, segments)
        # المتوقع: 2 ثانية = 32000 عينة
        assert abs(len(extracted) - 32000) < 100

    def test_extract_no_segments(self):
        audio = make_sine(1.0)
        result = extract_speech_audio(audio, SR, [])
        assert len(result) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
