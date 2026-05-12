"""خط أنابيب التفريغ التلقائي الكامل.

المسار: ملف صوتي → ASR (Whisper) → Diarization → Alignment → Export.

استخدام:
    from src.asr.pipeline import transcribe_file

    result = transcribe_file(
        "call.wav",
        asr_backend="faster-whisper",
        n_speakers=2,
    )
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.asr.alignment import AlignedTranscript, align_transcript_with_speakers
from src.asr.backends import ASRBackendName, get_backend
from src.asr.export import export_aligned_transcript
from src.audio.io import load_and_normalize
from src.diarization.pipeline import diarize_audio
from src.diarization.registry import VoiceprintRegistry
from src.utils.logging import get_logger

log = get_logger(__name__)


@dataclass
class FullPipelineResult:
    """نتيجة الخط الكامل."""

    file_path: str
    aligned_transcript: AlignedTranscript
    exported_files: dict[str, Path] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "file_path": self.file_path,
            "aligned_transcript": self.aligned_transcript.to_dict(),
            "exported_files": {k: str(v) for k, v in self.exported_files.items()},
            "metadata": self.metadata,
        }


def transcribe_audio(
    audio,
    sr: int,
    *,
    call_id: str = "unknown",
    asr_backend: ASRBackendName = "faster-whisper",
    asr_kwargs: dict | None = None,
    registry: VoiceprintRegistry | None = None,
    n_speakers: int | None = None,
    language: str = "ar",
    initial_prompt: str | None = None,
) -> AlignedTranscript:
    """تشغيل ASR + Diarization + Alignment على مصفوفة صوت.

    Args:
        audio: مصفوفة الصوت mono float32.
        sr: تردد العينة (يفضّل 16000).
        call_id: معرّف المكالمة.
        asr_backend: "mock" | "faster-whisper".
        asr_kwargs: kwargs للـ backend (model_size, device, ...).
        registry: قاعدة بصمات. إن None، تُنشأ فارغة.
        n_speakers: عدد المتحدثين إن كان معلوماً.
        language: لغة التفريغ (ar للعربية).
        initial_prompt: prompt اختياري لتوجيه Whisper.

    Returns:
        AlignedTranscript.
    """
    # 1. ASR
    asr_kwargs = asr_kwargs or {}
    asr = get_backend(asr_backend, **asr_kwargs)
    log.info(f"بدء التفريغ بـ {asr_backend}...")
    transcription = asr.transcribe(
        audio,
        sr,
        language=language,
        initial_prompt=initial_prompt,
    )
    log.info(f"  • تم: {len(transcription.segments)} قطعة، ثقة {transcription.avg_confidence:.2%}")

    # 2. Diarization
    if registry is None:
        registry = VoiceprintRegistry()
    log.info("بدء فصل المتحدثين...")
    diarization = diarize_audio(
        audio,
        sr,
        registry=registry,
        source_clip=call_id,
        n_speakers=n_speakers,
        auto_register_unknown=True,
    )
    log.info(f"  • تم: {diarization.n_speakers_detected} متحدث، {len(diarization.segments)} قطعة")

    # 3. Alignment
    log.info("دمج التفريغ مع المتحدثين...")
    aligned = align_transcript_with_speakers(
        transcription,
        diarization,
        call_id=call_id,
    )
    log.info(f"  • تم: {len(aligned.segments)} سطر نهائي")

    return aligned


def transcribe_file(
    file_path: Path | str,
    *,
    output_dir: Path | str | None = None,
    export_formats: list[str] | None = None,
    call_id: str | None = None,
    asr_backend: ASRBackendName = "faster-whisper",
    asr_kwargs: dict | None = None,
    registry: VoiceprintRegistry | None = None,
    n_speakers: int | None = None,
    language: str = "ar",
    initial_prompt: str | None = None,
) -> FullPipelineResult:
    """تفريغ ملف صوتي كامل مع التصدير.

    Args:
        file_path: مسار الملف.
        output_dir: مجلد الإخراج. إن None، لا تصدير لملفات.
        export_formats: قائمة الصيغ (افتراضياً json/txt/srt).
        call_id: معرّف المكالمة. إن None يُشتقّ من اسم الملف.
        asr_backend: backend الـ ASR.
        asr_kwargs: kwargs للـ backend.
        registry: قاعدة بصمات.
        n_speakers: عدد المتحدثين إن كان معلوماً.
        language: لغة التفريغ.
        initial_prompt: prompt اختياري.

    Returns:
        FullPipelineResult.
    """
    file_path = Path(file_path)
    if call_id is None:
        call_id = file_path.stem

    log.info(f"معالجة: {file_path.name} (call_id={call_id})")

    # تحميل الصوت
    audio, sr = load_and_normalize(file_path)

    # تشغيل الـ pipeline
    aligned = transcribe_audio(
        audio,
        sr,
        call_id=call_id,
        asr_backend=asr_backend,
        asr_kwargs=asr_kwargs,
        registry=registry,
        n_speakers=n_speakers,
        language=language,
        initial_prompt=initial_prompt,
    )

    # تصدير إن طُلب
    exported_files: dict[str, Path] = {}
    if output_dir:
        output_dir = Path(output_dir)
        export_formats = export_formats or ["json", "txt", "srt", "demo"]
        base_path = output_dir / call_id
        exported = export_aligned_transcript(
            aligned,
            base_path,
            formats=export_formats,
        )
        exported_files = exported
        log.info(f"  • تصدير: {len(exported)} ملف في {output_dir}")

    return FullPipelineResult(
        file_path=str(file_path),
        aligned_transcript=aligned,
        exported_files=exported_files,
        metadata={
            "asr_backend": asr_backend,
            "n_speakers_requested": n_speakers,
            "language": language,
        },
    )
