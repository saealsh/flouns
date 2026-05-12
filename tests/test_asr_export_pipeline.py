"""اختبارات وحدة لـ src.asr.export و src.asr.pipeline."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pytest

from src.asr.alignment import AlignedSegment, AlignedTranscript
from src.asr.export import export_aligned_transcript
from src.asr.pipeline import transcribe_audio


def make_aligned() -> AlignedTranscript:
    """تفريغ محاذى نموذجي للاختبار."""
    return AlignedTranscript(
        call_id="C-TEST",
        duration_sec=6.5,
        language="ar",
        segments=[
            AlignedSegment(
                start=0.5,
                end=2.5,
                speaker_id="SPK_01",
                speaker_name="أحمد",
                speaker_status="new",
                text="السلام عليكم",
                confidence=0.92,
            ),
            AlignedSegment(
                start=3.0,
                end=5.5,
                speaker_id="SPK_02",
                speaker_name="خالد",
                speaker_status="new",
                text="وعليكم السلام ورحمة الله",
                confidence=0.88,
            ),
        ],
        speakers=[
            {"speaker_id": "SPK_01", "speaker_name": "أحمد", "status": "new", "total_speech_sec": 2.0, "n_segments": 1, "n_words": 2},
            {"speaker_id": "SPK_02", "speaker_name": "خالد", "status": "new", "total_speech_sec": 2.5, "n_segments": 1, "n_words": 4},
        ],
    )


class TestExport:
    def test_exports_all_formats(self, tmp_path):
        aligned = make_aligned()
        result = export_aligned_transcript(aligned, tmp_path / "out")
        # يجب أن نحصل على json, txt, srt, vtt, csv, demo
        for fmt in ["json", "txt", "srt", "vtt", "csv", "demo"]:
            assert fmt in result
            assert result[fmt].exists()

    def test_json_is_valid(self, tmp_path):
        aligned = make_aligned()
        result = export_aligned_transcript(aligned, tmp_path / "out", formats=["json"])
        data = json.loads(result["json"].read_text(encoding="utf-8"))
        assert data["call_id"] == "C-TEST"
        assert len(data["segments"]) == 2

    def test_srt_format(self, tmp_path):
        aligned = make_aligned()
        result = export_aligned_transcript(aligned, tmp_path / "out", formats=["srt"])
        content = result["srt"].read_text(encoding="utf-8")
        assert "1\n" in content
        assert "أحمد" in content
        assert "-->" in content
        assert "00:00:00,500" in content  # start: 0.5s

    def test_vtt_format(self, tmp_path):
        aligned = make_aligned()
        result = export_aligned_transcript(aligned, tmp_path / "out", formats=["vtt"])
        content = result["vtt"].read_text(encoding="utf-8")
        assert content.startswith("WEBVTT")
        assert "<v أحمد>" in content

    def test_demo_format_matches_seed_structure(self, tmp_path):
        aligned = make_aligned()
        result = export_aligned_transcript(aligned, tmp_path / "out", formats=["demo"])
        data = json.loads(result["demo"].read_text(encoding="utf-8"))
        assert isinstance(data, list)
        assert data[0]["call_id"] == "C-TEST"
        assert "speaker_name" in data[0]
        assert "speaker_slot" in data[0]
        assert "time_stamp" in data[0]
        assert "confidence" in data[0]
        # سلوت أول متحدث = 1
        assert data[0]["speaker_slot"] == 1
        assert data[1]["speaker_slot"] == 2

    def test_txt_format_readable(self, tmp_path):
        aligned = make_aligned()
        result = export_aligned_transcript(aligned, tmp_path / "out", formats=["txt"])
        content = result["txt"].read_text(encoding="utf-8")
        assert "C-TEST" in content
        assert "أحمد:" in content
        assert "السلام عليكم" in content

    def test_csv_has_header_and_rows(self, tmp_path):
        aligned = make_aligned()
        result = export_aligned_transcript(aligned, tmp_path / "out", formats=["csv"])
        content = result["csv"].read_text(encoding="utf-8")
        lines = content.strip().split("\n")
        assert len(lines) == 3  # header + 2 rows
        assert "speaker_id" in lines[0]

    def test_unknown_format_skipped(self, tmp_path, caplog):
        aligned = make_aligned()
        result = export_aligned_transcript(aligned, tmp_path / "out", formats=["invented"])
        assert "invented" not in result


class TestPipeline:
    """اختبار خط الـ pipeline الكامل بـ mock backend."""

    SR = 16000

    def _make_audio_two_speakers(self):
        """صوت بمتحدثين متميّزين تردداتياً."""
        def speaker(duration, freq, seed):
            rng = np.random.default_rng(seed)
            t = np.linspace(0, duration, int(self.SR * duration), endpoint=False)
            sig = 0.4 * np.sin(2 * np.pi * freq * t) + 0.005 * rng.standard_normal(len(t))
            return sig.astype(np.float32)

        def silence(d):
            return np.zeros(int(self.SR * d), dtype=np.float32)

        return np.concatenate([
            silence(0.3),
            speaker(2.0, 150, 1),
            silence(0.4),
            speaker(2.0, 400, 2),
        ])

    def test_returns_aligned_transcript(self):
        audio = self._make_audio_two_speakers()
        aligned = transcribe_audio(
            audio,
            self.SR,
            call_id="C-TEST",
            asr_backend="mock",
            n_speakers=2,
        )
        assert aligned.call_id == "C-TEST"
        assert len(aligned.segments) > 0
        assert aligned.language == "ar"

    def test_pipeline_produces_speakers(self):
        audio = self._make_audio_two_speakers()
        aligned = transcribe_audio(
            audio,
            self.SR,
            call_id="C",
            asr_backend="mock",
            n_speakers=2,
        )
        # يجب أن يكون لكل segment متحدث (ليس فارغاً)
        assert all(s.speaker_name for s in aligned.segments)

    def test_full_pipeline_serializable(self):
        audio = self._make_audio_two_speakers()
        aligned = transcribe_audio(audio, self.SR, asr_backend="mock", n_speakers=2)
        # serialization should not fail
        json_str = json.dumps(aligned.to_dict(), ensure_ascii=False)
        assert "C-" in json_str or "unknown" in json_str

    def test_pipeline_with_empty_audio(self):
        audio = np.array([], dtype=np.float32)
        aligned = transcribe_audio(audio, self.SR, asr_backend="mock")
        assert len(aligned.segments) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
