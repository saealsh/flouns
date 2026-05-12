"""دمج مخرجات ASR مع نتائج Diarization → سطور لكل متحدث.

المشكلة: Whisper يقسّم الصوت لقطع لغوية (جمل)، Diarization يقسّمه
لقطع متحدث. الحدود لا تتطابق بالضرورة.

الحل: لكل كلمة من Whisper، نحدد المتحدث الذي يتداخل أكثر مع طابعها الزمني.
ثم نُعيد تجميع الكلمات لسطور متجاورة من نفس المتحدث.

المخرج النهائي يطابق بنية الديمو:
    {
      "call_id": "C-001",
      "segments": [
        {
          "start": 0.0,
          "end": 4.5,
          "speaker_id": "SPK_01",
          "speaker_name": "أحمد",
          "text": "السلام عليكم...",
          "confidence": 0.91,
          "words": [...]
        }
      ]
    }

استخدام:
    from src.asr.alignment import align_transcript_with_speakers

    aligned = align_transcript_with_speakers(transcription, diarization)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from src.asr.backends import TranscriptionResult, WordTiming
from src.diarization.pipeline import DiarizationResult
from src.utils.logging import get_logger

log = get_logger(__name__)


@dataclass
class AlignedSegment:
    """سطر نهائي: متحدث + نص + ميتاداتا."""

    start: float
    end: float
    speaker_id: str | None
    speaker_name: str
    speaker_status: str
    text: str
    words: list[dict] = field(default_factory=list)
    confidence: float = 0.0

    @property
    def duration(self) -> float:
        return self.end - self.start

    def to_dict(self) -> dict:
        return {
            "start": round(self.start, 3),
            "end": round(self.end, 3),
            "duration": round(self.duration, 3),
            "speaker_id": self.speaker_id,
            "speaker_name": self.speaker_name,
            "speaker_status": self.speaker_status,
            "text": self.text,
            "confidence": round(self.confidence, 4),
            "words": self.words,
        }


@dataclass
class AlignedTranscript:
    """تفريغ كامل بعد المحاذاة مع diarization."""

    call_id: str
    duration_sec: float
    language: str
    segments: list[AlignedSegment] = field(default_factory=list)
    speakers: list[dict] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def full_text(self) -> str:
        return "\n".join(f"{s.speaker_name}: {s.text}" for s in self.segments)

    @property
    def avg_confidence(self) -> float:
        if not self.segments:
            return 0.0
        total_dur = sum(s.duration for s in self.segments) or 1.0
        return sum(s.confidence * s.duration for s in self.segments) / total_dur

    def to_dict(self) -> dict:
        return {
            "call_id": self.call_id,
            "duration_sec": round(self.duration_sec, 3),
            "language": self.language,
            "n_segments": len(self.segments),
            "n_speakers": len(self.speakers),
            "avg_confidence": round(self.avg_confidence, 4),
            "segments": [s.to_dict() for s in self.segments],
            "speakers": self.speakers,
            "metadata": self.metadata,
        }


def _word_speaker_overlap(
    word: WordTiming,
    diarization: DiarizationResult,
) -> tuple[str | None, str, str, float]:
    """تحديد المتحدث الذي يتداخل أكثر مع زمن الكلمة.

    Returns:
        (speaker_id, speaker_name, status, overlap_ratio).
    """
    if not diarization.segments:
        return None, "غير معروف", "unknown", 0.0

    word_dur = word.end - word.start
    if word_dur <= 0:
        return None, "غير معروف", "unknown", 0.0

    best: tuple[str | None, str, str, float] = (None, "غير معروف", "unknown", 0.0)

    for seg in diarization.segments:
        # حساب التداخل
        overlap_start = max(word.start, seg.start)
        overlap_end = min(word.end, seg.end)
        overlap = max(0.0, overlap_end - overlap_start)

        if overlap > best[3]:
            best = (seg.speaker_id, seg.speaker_name, seg.status, overlap)

    overlap_ratio = best[3] / word_dur if word_dur > 0 else 0.0
    return best[0], best[1], best[2], overlap_ratio


def _assign_speaker_to_segment(
    segment_start: float,
    segment_end: float,
    diarization: DiarizationResult,
) -> tuple[str | None, str, str]:
    """احتياطي: تحديد المتحدث لقطعة كاملة بدون طوابع كلمات.

    نستخدم أكبر تداخل زمني.
    """
    if not diarization.segments:
        return None, "غير معروف", "unknown"

    best: tuple[str | None, str, str, float] = (None, "غير معروف", "unknown", 0.0)
    for seg in diarization.segments:
        overlap_start = max(segment_start, seg.start)
        overlap_end = min(segment_end, seg.end)
        overlap = max(0.0, overlap_end - overlap_start)
        if overlap > best[3]:
            best = (seg.speaker_id, seg.speaker_name, seg.status, overlap)
    return best[0], best[1], best[2]


def _merge_adjacent_words(
    word_assignments: list[tuple[WordTiming, str | None, str, str]],
    *,
    max_gap: float = 0.6,
) -> list[AlignedSegment]:
    """دمج الكلمات المتجاورة من نفس المتحدث في سطور.

    Args:
        word_assignments: قائمة (word, speaker_id, speaker_name, status).
        max_gap: أقصى فجوة زمنية بين كلمتين لاعتبارهما في نفس السطر.

    Returns:
        قائمة AlignedSegment.
    """
    if not word_assignments:
        return []

    segments = []
    current_words: list[WordTiming] = []
    current_spk_id: str | None = None
    current_spk_name: str = ""
    current_status: str = ""
    current_start = 0.0
    current_end = 0.0

    def flush():
        if not current_words:
            return
        text = " ".join(w.word for w in current_words).strip()
        avg_conf = float(np.mean([w.confidence for w in current_words]))
        segments.append(
            AlignedSegment(
                start=current_start,
                end=current_end,
                speaker_id=current_spk_id,
                speaker_name=current_spk_name,
                speaker_status=current_status,
                text=text,
                words=[w.to_dict() for w in current_words],
                confidence=avg_conf,
            )
        )

    for word, spk_id, spk_name, status in word_assignments:
        # شرط البدء بسطر جديد:
        # (أ) لا سطر حالي.
        # (ب) متحدث مختلف عن الحالي.
        # (ج) فجوة زمنية كبيرة مع آخر كلمة.
        if not current_words:
            current_words = [word]
            current_spk_id = spk_id
            current_spk_name = spk_name
            current_status = status
            current_start = word.start
            current_end = word.end
            continue

        same_speaker = spk_id == current_spk_id
        gap = word.start - current_end

        if same_speaker and gap <= max_gap:
            current_words.append(word)
            current_end = word.end
        else:
            flush()
            current_words = [word]
            current_spk_id = spk_id
            current_spk_name = spk_name
            current_status = status
            current_start = word.start
            current_end = word.end

    flush()
    return segments


def align_transcript_with_speakers(
    transcription: TranscriptionResult,
    diarization: DiarizationResult,
    *,
    call_id: str = "unknown",
    min_overlap_ratio: float = 0.3,
    max_gap: float = 0.6,
) -> AlignedTranscript:
    """دمج تفريغ Whisper مع نتائج diarization.

    Args:
        transcription: مخرج TranscriptionResult.
        diarization: مخرج DiarizationResult.
        call_id: معرّف المكالمة.
        min_overlap_ratio: نسبة تداخل كلمة مع متحدث لاعتبارها له.
                          إن أقل، الكلمة تُسنَد بناءً على القطعة كاملة.
        max_gap: أقصى فجوة بين كلمتين لاعتبارهما في نفس السطر.

    Returns:
        AlignedTranscript.
    """
    # هل لدينا طوابع كلمات؟
    has_word_timestamps = any(
        seg.words for seg in transcription.segments
    )

    if has_word_timestamps:
        # المسار الدقيق: لكل كلمة، نحدد المتحدث الأكثر تداخلاً
        word_assignments = []
        for seg in transcription.segments:
            for word in seg.words:
                spk_id, spk_name, status, overlap_ratio = _word_speaker_overlap(
                    word, diarization
                )
                if overlap_ratio < min_overlap_ratio:
                    # احتياطي: نستخدم القطعة كاملة
                    spk_id, spk_name, status = _assign_speaker_to_segment(
                        seg.start, seg.end, diarization
                    )
                word_assignments.append((word, spk_id, spk_name, status))

        aligned_segments = _merge_adjacent_words(word_assignments, max_gap=max_gap)
    else:
        # المسار التقريبي: نُسند المتحدث لكل قطعة Whisper كاملة
        log.info("لا توجد طوابع كلمات، استخدام التطابق على مستوى القطعة")
        aligned_segments = []
        for seg in transcription.segments:
            spk_id, spk_name, status = _assign_speaker_to_segment(
                seg.start, seg.end, diarization
            )
            aligned_segments.append(
                AlignedSegment(
                    start=seg.start,
                    end=seg.end,
                    speaker_id=spk_id,
                    speaker_name=spk_name,
                    speaker_status=status,
                    text=seg.text,
                    words=[],
                    confidence=seg.avg_confidence,
                )
            )

    # ملخص المتحدثين
    speakers_map: dict[str, dict] = {}
    for s in aligned_segments:
        key = s.speaker_id or "__unknown__"
        if key not in speakers_map:
            speakers_map[key] = {
                "speaker_id": s.speaker_id,
                "speaker_name": s.speaker_name,
                "status": s.speaker_status,
                "total_speech_sec": 0.0,
                "n_segments": 0,
                "n_words": 0,
            }
        speakers_map[key]["total_speech_sec"] += s.duration
        speakers_map[key]["n_segments"] += 1
        speakers_map[key]["n_words"] += len(s.words) if s.words else len(s.text.split())

    for spk in speakers_map.values():
        spk["total_speech_sec"] = round(spk["total_speech_sec"], 2)

    return AlignedTranscript(
        call_id=call_id,
        duration_sec=transcription.duration_sec,
        language=transcription.language,
        segments=aligned_segments,
        speakers=list(speakers_map.values()),
        metadata={
            "n_whisper_segments": len(transcription.segments),
            "n_diarization_segments": len(diarization.segments),
            "n_aligned_segments": len(aligned_segments),
            "has_word_timestamps": has_word_timestamps,
            "asr_backend": transcription.model_info.get("backend"),
            "asr_model": transcription.model_info.get("model"),
            "diarization_method": diarization.metadata.get("embedding_method"),
        },
    )
