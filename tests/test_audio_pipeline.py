"""اختبار التكامل لخط أنابيب المرحلة 2."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pytest
import soundfile as sf

from src.audio.pipeline import process_audio_file, process_directory


@pytest.fixture
def good_audio_file(tmp_path) -> Path:
    """ملف صوتي ذو جودة جيدة: كلام واضح + صمت واضح."""
    sr = 16000
    t = np.linspace(0, 0.8, int(sr * 0.8), endpoint=False)
    speech = (0.5 * np.sin(2 * np.pi * 200 * t) +
              0.3 * np.sin(2 * np.pi * 400 * t)).astype(np.float32)
    silence = np.zeros(int(sr * 0.4), dtype=np.float32)
    signal = np.concatenate([silence, speech, silence, speech, silence])
    path = tmp_path / "good.wav"
    sf.write(str(path), signal, sr)
    return path


@pytest.fixture
def silent_audio_file(tmp_path) -> Path:
    """ملف صامت بالكامل."""
    sr = 16000
    silence = np.zeros(sr * 2, dtype=np.float32)
    path = tmp_path / "silent.wav"
    sf.write(str(path), silence, sr)
    return path


@pytest.fixture
def noisy_audio_file(tmp_path) -> Path:
    """ملف ذو ضوضاء عالية."""
    sr = 16000
    rng = np.random.default_rng(42)
    noise = (0.3 * rng.standard_normal(sr * 2)).astype(np.float32)
    path = tmp_path / "noisy.wav"
    sf.write(str(path), noise, sr)
    return path


class TestProcessAudioFile:
    def test_good_file_passes(self, good_audio_file, tmp_path):
        out_dir = tmp_path / "out"
        report = process_audio_file(good_audio_file, output_dir=out_dir)

        assert report.status in ("ok", "warning")
        assert report.error is None
        assert report.duration_sec > 0
        assert report.output_path is not None
        assert Path(report.output_path).exists()
        assert report.vad["n_segments"] >= 2  # قطعتي كلام
        assert report.quality["passes"] or len(report.quality["issues"]) <= 1

    def test_silent_file_warning(self, silent_audio_file, tmp_path):
        report = process_audio_file(silent_audio_file, output_dir=tmp_path / "out")

        assert report.status == "warning"
        assert report.vad["n_segments"] == 0
        assert any("صامت" in iss or "RMS" in iss for iss in report.quality["issues"])

    def test_missing_file_failed(self, tmp_path):
        report = process_audio_file(
            tmp_path / "nonexistent.wav",
            output_dir=tmp_path / "out",
        )
        assert report.status == "failed"
        assert report.error is not None

    def test_no_save_when_output_dir_none(self, good_audio_file):
        report = process_audio_file(good_audio_file, output_dir=None)
        assert report.output_path is None
        assert report.status in ("ok", "warning")

    def test_report_to_dict_serializable(self, good_audio_file, tmp_path):
        import json

        report = process_audio_file(good_audio_file, output_dir=tmp_path / "out")
        # يجب أن يكون قابلاً للتسلسل
        json_str = json.dumps(report.to_dict(), ensure_ascii=False)
        assert "duration_sec" in json_str
        assert "quality" in json_str
        assert "vad" in json_str


class TestProcessDirectory:
    def test_processes_multiple_files(self, good_audio_file, silent_audio_file, tmp_path):
        # نضع الملفات في مجلد واحد
        in_dir = tmp_path / "in"
        in_dir.mkdir()
        for f in [good_audio_file, silent_audio_file]:
            target = in_dir / f.name
            target.write_bytes(f.read_bytes())

        out_dir = tmp_path / "out"
        reports = process_directory(in_dir, out_dir)

        assert len(reports) == 2

    def test_empty_directory(self, tmp_path):
        empty = tmp_path / "empty"
        empty.mkdir()
        reports = process_directory(empty, tmp_path / "out")
        assert reports == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
