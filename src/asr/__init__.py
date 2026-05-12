"""Call Intelligence Engine — asr module."""

from src.asr.backends import (
    ASRBackendName,
    MockASRBackend,
    FasterWhisperBackend,
    TranscriptionResult,
    TranscriptionSegment,
    WordTiming,
    get_backend,
)
from src.asr.alignment import (
    AlignedSegment,
    AlignedTranscript,
    align_transcript_with_speakers,
)
from src.asr.export import export_aligned_transcript
from src.asr.metrics import (
    ErrorRateResult,
    compute_wer,
    compute_cer,
    speaker_attribution_accuracy,
    evaluate_transcript,
)
from src.asr.pipeline import (
    FullPipelineResult,
    transcribe_audio,
    transcribe_file,
)

__all__ = [
    "ASRBackendName", "MockASRBackend", "FasterWhisperBackend",
    "TranscriptionResult", "TranscriptionSegment", "WordTiming", "get_backend",
    "AlignedSegment", "AlignedTranscript", "align_transcript_with_speakers",
    "export_aligned_transcript",
    "ErrorRateResult", "compute_wer", "compute_cer",
    "speaker_attribution_accuracy", "evaluate_transcript",
    "FullPipelineResult", "transcribe_audio", "transcribe_file",
]
