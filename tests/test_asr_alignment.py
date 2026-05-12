"""اختبارات وحدة لـ src.asr.alignment."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from src.asr.alignment import align_transcript_with_speakers
from src.asr.backends import (
    TranscriptionResult,
    TranscriptionSegment,
    WordTiming,
)
from src.diarization.pipeline import DiarizationResult, DiarizedSegment


def make_transcription(words_spec: list[tuple[str, float, float, float]]) -> TranscriptionResult:
    """بناء TranscriptionResult من قائمة (word, start, end, conf).

    كل قطعة Whisper تحوي كل الكلمات لتبسيط الاختبار.
    """
    words = [WordTiming(w, s, e, c) for w, s, e, c in words_spec]
    text = " ".join(w[0] for w in words_spec)
    return TranscriptionResult(
        segments=[
            TranscriptionSegment(
                start=words_spec[0][1] if words_spec else 0,
                end=words_spec[-1][2] if words_spec else 0,
                text=text,
                words=words,
                avg_confidence=0.9,
            )
        ],
        duration_sec=words_spec[-1][2] if words_spec else 0,
    )


def make_diarization(segs: list[tuple[float, float, str, str]]) -> DiarizationResult:
    """بناء DiarizationResult من قائمة (start, end, spk_id, name)."""
    segments = [
        DiarizedSegment(
            start=s,
            end=e,
            speaker_id=sid,
            speaker_name=name,
            cluster_id=i,
            similarity=0.9,
            status="new",
        )
        for i, (s, e, sid, name) in enumerate(segs)
    ]
    return DiarizationResult(
        file_path="x.wav",
        duration_sec=segs[-1][1] if segs else 0,
        n_speakers_detected=len({s[2] for s in segs}),
        segments=segments,
    )


class TestAlignment:
    def test_simple_two_speakers(self):
        """متحدثان متناوبان: alice (0-2) ثم bob (2-4)."""
        transcription = make_transcription([
            ("السلام", 0.0, 0.5, 0.95),
            ("عليكم", 0.5, 1.0, 0.95),
            ("وعليكم", 2.2, 2.7, 0.92),
            ("السلام", 2.7, 3.2, 0.92),
        ])
        diarization = make_diarization([
            (0.0, 2.0, "SPK_01", "أحمد"),
            (2.0, 4.0, "SPK_02", "خالد"),
        ])

        aligned = align_transcript_with_speakers(transcription, diarization, call_id="C-001")
        assert len(aligned.segments) == 2  # سطران، كل متحدث له سطر
        assert aligned.segments[0].speaker_name == "أحمد"
        assert aligned.segments[1].speaker_name == "خالد"
        assert "السلام" in aligned.segments[0].text
        assert "وعليكم" in aligned.segments[1].text

    def test_segments_have_correct_speakers(self):
        transcription = make_transcription([
            ("a", 0.0, 0.5, 0.9),
            ("b", 1.5, 2.0, 0.9),
        ])
        diarization = make_diarization([
            (0.0, 1.0, "SPK_01", "أحمد"),
            (1.0, 3.0, "SPK_02", "خالد"),
        ])
        aligned = align_transcript_with_speakers(transcription, diarization)
        spk_names = [s.speaker_name for s in aligned.segments]
        assert "أحمد" in spk_names and "خالد" in spk_names

    def test_call_id_propagated(self):
        transcription = make_transcription([("a", 0, 1, 0.9)])
        diarization = make_diarization([(0, 1, "SPK_01", "x")])
        aligned = align_transcript_with_speakers(transcription, diarization, call_id="MY-CALL")
        assert aligned.call_id == "MY-CALL"

    def test_speakers_summary_includes_all_present(self):
        transcription = make_transcription([
            ("a", 0, 0.5, 0.9),
            ("b", 1.5, 2.0, 0.9),
            ("c", 3.5, 4.0, 0.9),
        ])
        diarization = make_diarization([
            (0.0, 1.0, "SPK_01", "أحمد"),
            (1.0, 3.0, "SPK_02", "خالد"),
            (3.0, 5.0, "SPK_01", "أحمد"),
        ])
        aligned = align_transcript_with_speakers(transcription, diarization)
        names = {spk["speaker_name"] for spk in aligned.speakers}
        assert "أحمد" in names
        assert "خالد" in names

    def test_empty_transcription(self):
        transcription = TranscriptionResult()
        diarization = make_diarization([(0, 1, "SPK_01", "x")])
        aligned = align_transcript_with_speakers(transcription, diarization, call_id="C")
        assert len(aligned.segments) == 0

    def test_empty_diarization_uses_unknown(self):
        transcription = make_transcription([("a", 0, 1, 0.9)])
        diarization = DiarizationResult(file_path="x", duration_sec=1.0, n_speakers_detected=0)
        aligned = align_transcript_with_speakers(transcription, diarization)
        assert all(s.speaker_name == "غير معروف" for s in aligned.segments)

    def test_consecutive_same_speaker_merged(self):
        """3 كلمات متتالية من نفس المتحدث → سطر واحد."""
        transcription = make_transcription([
            ("a", 0.0, 0.5, 0.9),
            ("b", 0.5, 1.0, 0.9),
            ("c", 1.0, 1.5, 0.9),
        ])
        diarization = make_diarization([(0.0, 2.0, "SPK_01", "أحمد")])
        aligned = align_transcript_with_speakers(transcription, diarization)
        assert len(aligned.segments) == 1
        assert aligned.segments[0].text == "a b c"

    def test_long_gap_splits_segments(self):
        """فجوة كبيرة بين كلمتين من نفس المتحدث → سطران."""
        transcription = make_transcription([
            ("a", 0.0, 0.5, 0.9),
            ("b", 5.0, 5.5, 0.9),  # فجوة 4.5s
        ])
        diarization = make_diarization([(0.0, 6.0, "SPK_01", "أحمد")])
        aligned = align_transcript_with_speakers(transcription, diarization, max_gap=1.0)
        assert len(aligned.segments) == 2

    def test_no_word_timestamps_fallback(self):
        """إذا غابت طوابع الكلمات، يُستخدم تطابق القطعة."""
        transcription = TranscriptionResult(
            segments=[
                TranscriptionSegment(0.0, 1.0, "نص أول", words=[], avg_confidence=0.9),
                TranscriptionSegment(2.0, 3.0, "نص ثاني", words=[], avg_confidence=0.9),
            ]
        )
        diarization = make_diarization([
            (0.0, 1.5, "SPK_01", "أحمد"),
            (1.5, 3.5, "SPK_02", "خالد"),
        ])
        aligned = align_transcript_with_speakers(transcription, diarization)
        assert len(aligned.segments) == 2
        assert aligned.segments[0].speaker_name == "أحمد"
        assert aligned.segments[1].speaker_name == "خالد"

    def test_confidence_averaged_per_segment(self):
        transcription = make_transcription([
            ("a", 0.0, 0.5, 0.9),
            ("b", 0.5, 1.0, 0.7),
        ])
        diarization = make_diarization([(0.0, 2.0, "SPK_01", "أحمد")])
        aligned = align_transcript_with_speakers(transcription, diarization)
        # متوسط 0.9 و 0.7 = 0.8
        assert abs(aligned.segments[0].confidence - 0.8) < 0.05


class TestSerialization:
    def test_to_dict_is_json_serializable(self):
        import json

        transcription = make_transcription([("a", 0, 1, 0.9)])
        diarization = make_diarization([(0, 1, "SPK_01", "x")])
        aligned = align_transcript_with_speakers(transcription, diarization, call_id="C")
        json_str = json.dumps(aligned.to_dict(), ensure_ascii=False)
        assert "segments" in json_str
        assert "speakers" in json_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
