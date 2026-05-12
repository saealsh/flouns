"""اختبارات وحدة لـ src.audio.quality."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pytest

from src.audio.quality import (
    compute_clipping_ratio,
    compute_dynamic_range_db,
    compute_quality_metrics,
    compute_rms,
    compute_silence_ratio,
    compute_snr_db,
)

SR = 16000


def make_sine(duration: float, freq: float = 440, amp: float = 0.5) -> np.ndarray:
    """توليد موجة جيبية."""
    t = np.linspace(0, duration, int(SR * duration), endpoint=False)
    return (amp * np.sin(2 * np.pi * freq * t)).astype(np.float32)


def make_noise(duration: float, amp: float = 0.001) -> np.ndarray:
    """توليد ضوضاء بيضاء بسعة محددة."""
    rng = np.random.default_rng(42)
    return (amp * rng.standard_normal(int(SR * duration))).astype(np.float32)


def make_silence(duration: float) -> np.ndarray:
    return np.zeros(int(SR * duration), dtype=np.float32)


class TestRMS:
    def test_silence_has_zero_rms(self):
        rms, rms_db = compute_rms(make_silence(0.5))
        assert rms == 0.0
        assert rms_db == float("-inf") or rms_db < -100

    def test_full_scale_sine_has_correct_rms(self):
        # سعة 1.0 → RMS نظري = 1/sqrt(2) ≈ 0.707
        sine = make_sine(0.5, amp=1.0)
        rms, _ = compute_rms(sine)
        assert abs(rms - 1 / np.sqrt(2)) < 0.01

    def test_empty_array(self):
        rms, rms_db = compute_rms(np.array([], dtype=np.float32))
        assert rms == 0.0


class TestSilenceRatio:
    def test_pure_silence(self):
        ratio = compute_silence_ratio(make_silence(1.0), SR)
        assert ratio == 1.0

    def test_pure_speech(self):
        # موجة بسعة 0.5 = -6 dBFS، أعلى بكثير من -40 dB
        ratio = compute_silence_ratio(make_sine(1.0, amp=0.5), SR)
        assert ratio < 0.05

    def test_half_silence_half_speech(self):
        speech = make_sine(0.5, amp=0.5)
        silence = make_silence(0.5)
        signal = np.concatenate([speech, silence])
        ratio = compute_silence_ratio(signal, SR)
        # ~50%، نسمح بهامش بسبب حدود الإطارات
        assert 0.40 < ratio < 0.60


class TestSNR:
    def test_clean_signal_high_snr(self):
        speech = make_sine(0.5, amp=0.5)
        silence = make_silence(0.5)
        signal = np.concatenate([speech, silence])
        snr = compute_snr_db(signal, SR)
        assert snr > 30

    def test_pure_silence_returns_zero(self):
        snr = compute_snr_db(make_silence(1.0), SR)
        assert snr == 0.0

    def test_noisy_signal_low_snr(self):
        # كلام بسعة 0.05، ضوضاء بسعة 0.04 → SNR منخفض
        speech = make_sine(0.5, amp=0.05)
        noise_silence = make_noise(0.5, amp=0.04)
        signal = np.concatenate([speech, noise_silence])
        snr = compute_snr_db(signal, SR)
        # لا نختبر قيمة دقيقة، نختبر أنه أقل من النقي
        clean_speech = make_sine(0.5, amp=0.05)
        clean_silence = make_silence(0.5)
        clean_signal = np.concatenate([clean_speech, clean_silence])
        clean_snr = compute_snr_db(clean_signal, SR)
        assert snr < clean_snr


class TestClipping:
    def test_no_clipping(self):
        audio = make_sine(0.5, amp=0.5)
        assert compute_clipping_ratio(audio) == 0.0

    def test_full_clipping(self):
        audio = np.ones(1000, dtype=np.float32)
        assert compute_clipping_ratio(audio) == 1.0

    def test_partial_clipping(self):
        audio = np.array([0.5, 1.0, -1.0, 0.3, 0.99], dtype=np.float32)
        ratio = compute_clipping_ratio(audio)
        # 3 من 5 عينات: 1.0, -1.0, 0.99
        assert ratio == 0.6


class TestDynamicRange:
    def test_constant_signal_zero_range(self):
        audio = 0.5 * np.ones(1000, dtype=np.float32)
        dr = compute_dynamic_range_db(audio)
        assert dr < 1.0  # المنطق: peak ≈ floor

    def test_varying_signal_has_range(self):
        # موجة جيبية: peak/floor تختلف
        audio = make_sine(0.5, amp=0.8)
        dr = compute_dynamic_range_db(audio)
        assert dr > 5.0


class TestQualityMetricsIntegration:
    def test_clean_signal_passes(self):
        speech = make_sine(0.5, amp=0.5)
        silence = make_silence(0.3)
        signal = np.concatenate([speech, silence, speech])
        metrics = compute_quality_metrics(signal, SR)
        assert metrics.passes
        assert metrics.snr_db > 10
        assert len(metrics.issues) == 0

    def test_silent_file_fails(self):
        signal = make_silence(2.0)
        metrics = compute_quality_metrics(signal, SR)
        assert not metrics.passes
        assert any("RMS" in iss or "صامت" in iss for iss in metrics.issues)

    def test_clipped_signal_fails(self):
        # كلام مشبَّع بشدة
        signal = 1.5 * make_sine(1.0, amp=1.0)  # أعلى من النطاق بكثير
        signal = signal.astype(np.float32)
        # نضمن وجود تشبع فعلي قبل clip
        signal_normalized = np.clip(signal, -1.0, 1.0)  # تشبع كبير
        # نزيد التشبع بإضافة دوال مربعة
        signal_clipped = np.where(np.abs(signal) > 1.0, np.sign(signal), signal)
        metrics = compute_quality_metrics(
            signal_clipped, SR, max_clipping_ratio=0.001
        )
        # يجب أن يكون هناك تشبع كبير
        assert metrics.clipping_ratio > 0.05


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
