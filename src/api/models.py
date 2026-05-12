"""نماذج Pydantic للـ API.

تطابق صيغ الديمو الموجودة (shared.js) لتسهيل التكامل مع الواجهة.

نُحدّد:
- نماذج المدخلات (request bodies)
- نماذج المخرجات (response models)
- نماذج التدقيق البشري (review states)
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ProcessingStatus(str, Enum):
    """حالات معالجة المكالمة."""

    PENDING = "pending"          # لم تبدأ بعد
    PROCESSING = "processing"    # قيد المعالجة
    COMPLETED = "completed"      # اكتملت
    FAILED = "failed"            # فشلت
    NEEDS_REVIEW = "needs_review"  # تحتاج تدقيقاً بشرياً


class ReviewStatus(str, Enum):
    """حالات تدقيق الكيان/الحدث."""

    PENDING = "pending"          # لم يُراجع بعد
    CONFIRMED = "confirmed"      # المراجع وافق
    REJECTED = "rejected"        # المراجع رفض
    EDITED = "edited"            # المراجع عدّل


# ──────────────────────────────────────────────────────────────
# نماذج المكالمات (تطابق calls.html)
# ──────────────────────────────────────────────────────────────

class CallSegment(BaseModel):
    """قطعة كلام (سطر في التفريغ)."""

    speaker_name: str
    speaker_id: str
    speaker_slot: int = 0
    start: float
    end: float
    text: str
    confidence: float = 0.8


class CallSummary(BaseModel):
    """ملخص مكالمة في قائمة المكالمات."""

    call_id: str
    duration_sec: float = 0.0
    n_speakers: int = 0
    n_segments: int = 0
    status: ProcessingStatus = ProcessingStatus.PENDING
    created_at: Optional[str] = None
    processed_at: Optional[str] = None
    has_nlp: bool = False
    has_kg: bool = False
    watchlist_hits: int = 0


class CallDetails(BaseModel):
    """تفاصيل كاملة لمكالمة."""

    call_id: str
    duration_sec: float
    language: str = "ar"
    segments: list[CallSegment]
    metadata: dict[str, Any] = Field(default_factory=dict)
    status: ProcessingStatus = ProcessingStatus.COMPLETED


# ──────────────────────────────────────────────────────────────
# نماذج الكيانات والأحداث (مع حقول التدقيق)
# ──────────────────────────────────────────────────────────────

class EntityResponse(BaseModel):
    """كيان مع معلومات التدقيق."""

    id: str  # entity_id فريد (call_id + start + type)
    type: str
    text: str
    start: int
    end: int
    confidence: float
    normalized: str = ""
    context: str = ""
    source: str = "rule"
    # حقول التدقيق
    review_status: ReviewStatus = ReviewStatus.PENDING
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    review_note: Optional[str] = None


class EventResponse(BaseModel):
    """حدث مع معلومات التدقيق."""

    id: str
    action: str
    verb_text: str
    sentence: str
    sentence_start: int
    actors: list[dict[str, Any]] = Field(default_factory=list)
    locations: list[dict[str, Any]] = Field(default_factory=list)
    times: list[dict[str, Any]] = Field(default_factory=list)
    confidence: float = 0.5
    speaker_name: Optional[str] = None
    speaker_id: Optional[str] = None
    call_id: Optional[str] = None
    review_status: ReviewStatus = ReviewStatus.PENDING


class WatchlistMatchResponse(BaseModel):
    """تطابق watchlist."""

    id: str
    term: str
    matched_text: str
    start: int
    end: int
    note: str = ""
    call_id: Optional[str] = None
    speaker_name: Optional[str] = None


# ──────────────────────────────────────────────────────────────
# نماذج المتحدثين (تطابق speakers.html)
# ──────────────────────────────────────────────────────────────

class SpeakerSummary(BaseModel):
    """ملخص متحدث في قائمة المتحدثين."""

    speaker_id: str
    name: str
    status: str  # stable | new | unstable | unknown
    n_samples: int = 0
    n_clips: int = 0
    source_clips: list[str] = Field(default_factory=list)


class SpeakerDetails(SpeakerSummary):
    """تفاصيل كاملة لمتحدث."""

    embedding_method: Optional[str] = "mfcc"
    match_threshold: float = 0.85
    # المكالمات المشارك فيها
    participated_in: list[str] = Field(default_factory=list)
    # الكيانات التي ذكرها
    mentioned_entities: list[dict[str, Any]] = Field(default_factory=list)


# ──────────────────────────────────────────────────────────────
# نماذج رسم المعرفة (تطابق graph.html)
# ──────────────────────────────────────────────────────────────

class GraphNode(BaseModel):
    id: str
    label: str
    type: str
    color: str = "#6b7280"
    size: int = 10
    properties: dict[str, Any] = Field(default_factory=dict)


class GraphLink(BaseModel):
    source: str
    target: str
    type: str
    label: str = ""
    weight: int = 1
    properties: dict[str, Any] = Field(default_factory=dict)


class GraphData(BaseModel):
    """الرسم كاملاً للديمو."""

    nodes: list[GraphNode]
    links: list[GraphLink]
    metadata: dict[str, Any] = Field(default_factory=dict)


# ──────────────────────────────────────────────────────────────
# نماذج التقارير (تطابق reports.html)
# ──────────────────────────────────────────────────────────────

class TopEntity(BaseModel):
    """كيان في تقرير الترتيب."""

    rank: int
    label: str
    type: str
    score: float
    mention_count: int = 0


class ReportSummary(BaseModel):
    """ملخص شامل للنظام."""

    total_calls: int
    total_speakers: int
    total_entities: int
    total_events: int
    total_kg_nodes: int
    total_kg_edges: int
    nodes_by_type: dict[str, int]
    edges_by_type: dict[str, int]
    top_persons: list[TopEntity]
    top_locations: list[TopEntity]
    top_keywords: list[TopEntity]
    watchlist_alerts: int


# ──────────────────────────────────────────────────────────────
# نماذج الرفع والمعالجة (تطابق uploads.html)
# ──────────────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    """ردّ على رفع ملف."""

    call_id: str
    filename: str
    size_bytes: int
    status: ProcessingStatus
    message: str = ""


class ProcessingJob(BaseModel):
    """وظيفة معالجة جارية."""

    job_id: str
    call_id: str
    status: ProcessingStatus
    stage: str  # "audio" | "diarization" | "asr" | "nlp" | "kg" | "done"
    progress: float = 0.0  # 0-1
    started_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None


# ──────────────────────────────────────────────────────────────
# نماذج التدقيق البشري
# ──────────────────────────────────────────────────────────────

class ReviewRequest(BaseModel):
    """طلب مراجعة من المستخدم."""

    review_status: ReviewStatus
    reviewed_by: str = "user"
    note: Optional[str] = None
    # للحالة EDITED: قيم محدّثة
    edits: Optional[dict[str, Any]] = None


class ReviewResponse(BaseModel):
    """نتيجة المراجعة."""

    id: str
    review_status: ReviewStatus
    reviewed_by: str
    reviewed_at: str
    note: Optional[str] = None
    applied: bool


# ──────────────────────────────────────────────────────────────
# نموذج عام للأخطاء
# ──────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    """رد خطأ موحّد."""

    error: str
    detail: Optional[str] = None
    code: int = 500
