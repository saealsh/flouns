"""خط أنابيب فصل المتحدثين الكامل.

المراحل بالترتيب:

1. **VAD** (من المرحلة 2): كشف قطع الكلام.
2. **Sub-segmentation**: تقسيم كل قطعة طويلة لقطع 1.5ث (لأن المتحدث قد يتغير داخلها).
3. **Embeddings**: استخلاص بصمة لكل قطعة فرعية.
4. **Clustering**: تجميع البصمات → مجموعات (متحدثون مفترضون).
5. **Identification**: مطابقة كل مجموعة بقاعدة البصمات → إسناد اسم.
6. **Merge**: دمج القطع المتجاورة من نفس المتحدث.

النتيجة: قائمة [(start, end, speaker_name, speaker_id, confidence), ...]

استخدام:
    from src.diarization.pipeline import diarize_file

    result = diarize_file("call.wav", registry=registry)
    for seg in result["segments"]:
        print(f"{seg['start']:.2f}-{seg['end']:.2f}: {seg['name']}")
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from src.audio.io import load_and_normalize
from src.audio.vad import SpeechSegment, detect_speech_segments
from src.diarization.clustering import ClusteringMethod, cluster_embeddings
from src.diarization.embeddings import EmbeddingExtractor, EmbeddingMethod
from src.diarization.registry import IdentificationResult, VoiceprintRegistry
from src.utils.logging import get_logger

log = get_logger(__name__)


@dataclass
class DiarizedSegment:
    """قطعة بعد diarization كاملة."""

    start: float
    end: float
    speaker_id: str | None
    speaker_name: str
    cluster_id: int
    similarity: float
    status: str  # stable | new | unstable | unknown

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
            "cluster_id": self.cluster_id,
            "similarity": round(self.similarity, 4),
            "status": self.status,
        }


@dataclass
class DiarizationResult:
    """نتيجة diarization كاملة لملف واحد."""

    file_path: str
    duration_sec: float
    n_speakers_detected: int
    segments: list[DiarizedSegment] = field(default_factory=list)
    speakers_summary: list[dict] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "file_path": self.file_path,
            "duration_sec": round(self.duration_sec, 3),
            "n_speakers_detected": self.n_speakers_detected,
            "segments": [s.to_dict() for s in self.segments],
            "speakers_summary": self.speakers_summary,
            "metadata": self.metadata,
        }


def _subsegment(
    segments: list[SpeechSegment],
    *,
    max_duration: float = 1.5,
    min_duration: float = 0.5,
) -> list[tuple[float, float]]:
    """تقسيم القطع الطويلة لقطع فرعية ثابتة الطول.

    الفكرة: داخل قطعة كلام 10ث قد يتغيّر المتحدث، فلا نستطيع تمثيلها ببصمة واحدة.
    نقسّمها لقطع 1.5ث بتداخل بسيط.

    Args:
        segments: قطع VAD.
        max_duration: أقصى طول مقبول لقطعة فرعية.
        min_duration: أصغر طول مقبول (الأصغر يُسقَط أو يُدمج).

    Returns:
        قائمة (start_sec, end_sec).
    """
    result = []
    for seg in segments:
        if seg.duration_sec <= max_duration:
            if seg.duration_sec >= min_duration:
                result.append((seg.start_sec, seg.end_sec))
            continue

        # تقسيم لقطع فرعية متتالية
        cur = seg.start_sec
        while cur < seg.end_sec:
            end = min(cur + max_duration, seg.end_sec)
            if end - cur >= min_duration:
                result.append((cur, end))
            cur = end
    return result


def _merge_consecutive_same_speaker(
    segments: list[DiarizedSegment],
    *,
    max_gap: float = 0.5,
) -> list[DiarizedSegment]:
    """دمج القطع المتجاورة من نفس المتحدث (إن كانت الفجوة قصيرة)."""
    if not segments:
        return []

    sorted_segs = sorted(segments, key=lambda s: s.start)
    merged = [sorted_segs[0]]

    for seg in sorted_segs[1:]:
        last = merged[-1]
        gap = seg.start - last.end
        if (
            seg.cluster_id == last.cluster_id
            and seg.speaker_id == last.speaker_id
            and gap <= max_gap
        ):
            # دمج: متوسط مرجَّح للتشابه
            new_duration = (last.duration + seg.duration) or 1.0
            new_sim = (
                last.similarity * last.duration + seg.similarity * seg.duration
            ) / new_duration
            merged[-1] = DiarizedSegment(
                start=last.start,
                end=seg.end,
                speaker_id=last.speaker_id,
                speaker_name=last.speaker_name,
                cluster_id=last.cluster_id,
                similarity=new_sim,
                status=last.status,
            )
        else:
            merged.append(seg)
    return merged


def diarize_audio(
    audio: np.ndarray,
    sr: int,
    *,
    registry: VoiceprintRegistry | None = None,
    source_clip: str | None = None,
    embedding_method: EmbeddingMethod = "mfcc",
    clustering_method: ClusteringMethod = "agglomerative",
    n_speakers: int | None = None,
    cluster_threshold: float = 0.45,
    subsegment_max_sec: float = 1.5,
    auto_register_unknown: bool = True,
) -> DiarizationResult:
    """تشغيل diarization كاملاً على مصفوفة صوت في الذاكرة.

    Args:
        audio: مصفوفة الصوت mono float.
        sr: تردد العينة.
        registry: قاعدة بصمات للمطابقة. إن None، تُنشأ قاعدة جديدة فارغة.
        source_clip: معرّف المكالمة للتسجيل في القاعدة.
        embedding_method: "mfcc" | "speechbrain".
        clustering_method: "agglomerative" | "spectral".
        n_speakers: عدد المتحدثين إن كان معلوماً. إن None يُكتشف.
        cluster_threshold: عتبة مسافة cosine للتجميع التدرّجي.
        subsegment_max_sec: أقصى طول قطعة فرعية.
        auto_register_unknown: تسجيل المتحدثين المجهولين تلقائياً.

    Returns:
        DiarizationResult كاملاً.
    """
    duration = audio.size / sr if sr > 0 else 0.0

    if duration == 0:
        return DiarizationResult(
            file_path="<in-memory>",
            duration_sec=0.0,
            n_speakers_detected=0,
            metadata={"reason": "audio فارغ"},
        )

    if registry is None:
        registry = VoiceprintRegistry()

    # 1. VAD
    vad_segments = detect_speech_segments(audio, sr, method="energy")
    if not vad_segments:
        return DiarizationResult(
            file_path="<in-memory>",
            duration_sec=duration,
            n_speakers_detected=0,
            metadata={"reason": "لا كلام مكتشف"},
        )

    # 2. Sub-segmentation
    sub_segments = _subsegment(vad_segments, max_duration=subsegment_max_sec)
    if not sub_segments:
        return DiarizationResult(
            file_path="<in-memory>",
            duration_sec=duration,
            n_speakers_detected=0,
            metadata={"reason": "لا قطع صالحة بعد التقسيم"},
        )

    # 3. Embeddings
    extractor = EmbeddingExtractor(method=embedding_method)
    embeddings = extractor.extract_batch(audio, sr, sub_segments)

    # تصفية البصمات الصفرية (قطع قصيرة جداً أو فاسدة)
    valid_mask = np.linalg.norm(embeddings, axis=1) > 0.5
    if not valid_mask.any():
        return DiarizationResult(
            file_path="<in-memory>",
            duration_sec=duration,
            n_speakers_detected=0,
            metadata={"reason": "كل البصمات فاسدة"},
        )

    valid_embs = embeddings[valid_mask]
    valid_segs = [sub_segments[i] for i, m in enumerate(valid_mask) if m]

    # 4. Clustering
    if clustering_method == "agglomerative":
        labels = cluster_embeddings(
            valid_embs,
            method="agglomerative",
            n_clusters=n_speakers,
            threshold=cluster_threshold,
        )
    else:
        labels = cluster_embeddings(
            valid_embs,
            method="spectral",
            n_clusters=n_speakers,
        )

    n_clusters = len(set(labels.tolist()))
    log.debug(f"اكتُشف {n_clusters} متحدثاً من {len(valid_segs)} قطعة")

    # 5. Identification: لكل cluster، طابق مع registry
    cluster_results = registry.assign_clusters(
        valid_embs,
        labels,
        source_clip=source_clip,
        auto_register_unknown=auto_register_unknown,
    )
    # cluster_results[i] يطابق unique_clusters[i] بترتيب 0..K-1
    cluster_id_to_result: dict[int, IdentificationResult] = {
        i: r for i, r in enumerate(cluster_results)
    }

    # 6. تركيب النتيجة
    diar_segments = []
    for (start, end), cluster_id in zip(valid_segs, labels.tolist(), strict=True):
        result = cluster_id_to_result[cluster_id]
        diar_segments.append(
            DiarizedSegment(
                start=start,
                end=end,
                speaker_id=result.speaker_id,
                speaker_name=result.name,
                cluster_id=cluster_id,
                similarity=result.similarity,
                status=result.status,
            )
        )

    # 7. دمج القطع المتجاورة من نفس المتحدث
    merged_segments = _merge_consecutive_same_speaker(diar_segments)

    # 8. ملخص لكل متحدث
    speakers_summary = []
    for cluster_id in sorted({s.cluster_id for s in merged_segments}):
        speaker_segs = [s for s in merged_segments if s.cluster_id == cluster_id]
        total_speech = sum(s.duration for s in speaker_segs)
        first = speaker_segs[0]
        speakers_summary.append(
            {
                "cluster_id": cluster_id,
                "speaker_id": first.speaker_id,
                "speaker_name": first.speaker_name,
                "status": first.status,
                "n_segments": len(speaker_segs),
                "total_speech_sec": round(total_speech, 2),
                "speech_ratio": round(total_speech / duration, 4) if duration > 0 else 0,
                "avg_similarity": round(
                    sum(s.similarity for s in speaker_segs) / len(speaker_segs), 4
                ),
            }
        )

    return DiarizationResult(
        file_path="<in-memory>",
        duration_sec=duration,
        n_speakers_detected=len({s.cluster_id for s in merged_segments}),
        segments=merged_segments,
        speakers_summary=speakers_summary,
        metadata={
            "embedding_method": embedding_method,
            "clustering_method": clustering_method,
            "n_vad_segments": len(vad_segments),
            "n_sub_segments": len(sub_segments),
            "n_valid_embeddings": int(valid_mask.sum()),
            "cluster_threshold": cluster_threshold if clustering_method == "agglomerative" else None,
        },
    )


def diarize_file(
    file_path: Path | str,
    *,
    registry: VoiceprintRegistry | None = None,
    source_clip: str | None = None,
    **kwargs,
) -> DiarizationResult:
    """تشغيل diarization على ملف. ينظّف الواجهة لـ diarize_audio.

    Args:
        file_path: مسار الملف الصوتي.
        registry: قاعدة بصمات (إن None تنشأ فارغة).
        source_clip: معرّف للتسجيل في القاعدة.
        **kwargs: تُمرَّر لـ diarize_audio.

    Returns:
        DiarizationResult مع file_path المحدّث.
    """
    file_path = Path(file_path)
    audio, sr = load_and_normalize(file_path)
    result = diarize_audio(audio, sr, registry=registry, source_clip=source_clip, **kwargs)
    result.file_path = str(file_path)
    return result
