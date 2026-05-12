"""Call Intelligence Engine — diarization module."""

from src.diarization.embeddings import EmbeddingExtractor, cosine_similarity
from src.diarization.clustering import cluster_embeddings
from src.diarization.registry import VoiceprintRegistry, IdentificationResult
from src.diarization.metrics import diarization_error_rate, speaker_purity_coverage
from src.diarization.pipeline import diarize_audio, diarize_file, DiarizationResult

__all__ = [
    "EmbeddingExtractor",
    "cosine_similarity",
    "cluster_embeddings",
    "VoiceprintRegistry",
    "IdentificationResult",
    "diarization_error_rate",
    "speaker_purity_coverage",
    "diarize_audio",
    "diarize_file",
    "DiarizationResult",
]
