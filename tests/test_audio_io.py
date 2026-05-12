"""اختبارات وحدة لـ src.audio.io."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pytest
import soundfile as sf

from src.audio.io import (
    AudioLoadError,
    get_audio_info,
    load_and_normalize,
    save_audio,
)


@pytest.fixture
def stereo_wav(tmp_path) -> Path:
    """ملف ستيريو 44.1kHz للاختبار."""
    sr = 44100
    duration = 1.0
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    left = 0.3 * np.sin(2 * np.pi * 440 * t)
    right = 0.3 * np.sin(2 * np.pi * 880 * t)
    stereo = np.stack([left, right], axis=1).astype(np.float32)
    path = tmp_path / "stereo_44k.wav"
    sf.write(str(path), stereo, sr)
    return path


@pytest.fixture
def mono_wav(tmp_path) -> Path:
    """ملف mono 16kHz."""
    sr = 16000
    t = np.linspace(0, 0.5, sr // 2, endpoint=False)
    audio = 0.5 * np.sin(2 * np.pi * 440 * t).astype(np.float32)
    path = tmp_path / "mono_16k.wav"
    sf.write(str(path), audio, sr)
    return path


class TestLoadAndNormalize:
    def test_loads_mono_wav_unchanged(self, mono_wav):
        audio, sr = load_and_normalize(mono_wav)
        assert sr == 16000
        assert audio.ndim == 1
        assert audio.dtype == np.float32

    def test_converts_stereo_to_mono(self, stereo_wav):
        audio, sr = load_and_normalize(stereo_wav)
        assert sr == 16000
        assert audio.ndim == 1

    def test_resamples_to_target(self, stereo_wav):
        audio, sr = load_and_normalize(stereo_wav, target_sr=16000)
        assert sr == 16000
        # المدة محفوظة (1 ثانية ≈ 16000 عينة)
        assert abs(len(audio) - 16000) < 100

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_and_normalize(tmp_path / "nonexistent.wav")

    def test_no_extension_raises(self, tmp_path):
        bad = tmp_path / "no_ext"
        bad.write_bytes(b"\x00" * 100)
        with pytest.raises(AudioLoadError):
            load_and_normalize(bad)

    def test_output_in_normal_range(self, mono_wav):
        audio, _ = load_and_normalize(mono_wav)
        assert audio.max() <= 1.0
        assert audio.min() >= -1.0


class TestSaveAudio:
    def test_saves_and_reads_back(self, tmp_path):
        sr = 16000
        # نضمن أن القيم في النطاق [-1, 1] لتجنّب القصّ
        audio = (np.random.RandomState(42).randn(sr) * 0.2).astype(np.float32)
        audio = np.clip(audio, -0.95, 0.95)  # هامش أمان
        out = tmp_path / "out.wav"
        save_audio(audio, sr, out)

        assert out.exists()
        loaded, loaded_sr = sf.read(str(out), dtype="float32")
        assert loaded_sr == sr
        # 16-bit PCM فقدان طفيف، ~3e-5 عادة
        np.testing.assert_allclose(loaded, audio, atol=1e-3)

    def test_clips_out_of_range(self, tmp_path):
        # مصفوفة بقيم خارج [-1, 1]
        audio = np.array([2.0, -2.0, 0.5], dtype=np.float32)
        out = tmp_path / "clipped.wav"
        save_audio(audio, 16000, out)
        loaded, _ = sf.read(str(out), dtype="float32")
        # القيم تُقصّ
        assert loaded.max() <= 1.0
        assert loaded.min() >= -1.0


class TestGetAudioInfo:
    def test_returns_correct_metadata(self, mono_wav):
        info = get_audio_info(mono_wav)
        assert info["sample_rate"] == 16000
        assert info["channels"] == 1
        assert abs(info["duration_sec"] - 0.5) < 0.01

    def test_stereo_metadata(self, stereo_wav):
        info = get_audio_info(stereo_wav)
        assert info["channels"] == 2
        assert info["sample_rate"] == 44100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
