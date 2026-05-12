"""مسارات الـ API الرئيسية.

نُنظّمها حسب صفحات الديمو:
- /calls — calls.html
- /speakers — speakers.html
- /graph — graph.html
- /uploads — uploads.html
- /reports — reports.html
- /reviews — التدقيق البشري (جديد)

كل routes تستخدم DataStore و Orchestrator.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from src.api.models import (
    CallDetails,
    CallSegment,
    CallSummary,
    EntityResponse,
    ErrorResponse,
    EventResponse,
    GraphData,
    ProcessingJob,
    ProcessingStatus,
    ReportSummary,
    ReviewRequest,
    ReviewResponse,
    ReviewStatus,
    SpeakerDetails,
    SpeakerSummary,
    TopEntity,
    UploadResponse,
    WatchlistMatchResponse,
)
from src.api.orchestrator import Orchestrator
from src.api.store import DataStore, make_entity_id, make_event_id
from src.utils.logging import get_logger

log = get_logger(__name__)

router = APIRouter()


# مرجع عام للـ store والـ orchestrator (تُعيَّن في main.py)
_store: Optional[DataStore] = None
_orchestrator: Optional[Orchestrator] = None


def set_dependencies(store: DataStore, orchestrator: Orchestrator) -> None:
    """تعيين الـ dependencies من main.py."""
    global _store, _orchestrator
    _store = store
    _orchestrator = orchestrator


def get_store() -> DataStore:
    if _store is None:
        raise HTTPException(status_code=500, detail="DataStore not initialized")
    return _store


def get_orchestrator() -> Orchestrator:
    if _orchestrator is None:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    return _orchestrator


# ──────────────────────────────────────────────────────────────
# Health & info
# ──────────────────────────────────────────────────────────────

@router.get("/health", tags=["health"])
def health_check() -> dict:
    """فحص صحة الخدمة."""
    return {
        "status": "ok",
        "service": "call-intelligence-engine",
        "version": "0.7.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/info", tags=["health"])
def service_info() -> dict:
    """معلومات تشخيصية عن الخدمة."""
    store = get_store()
    return {
        "calls": len(store.list_call_ids()),
        "speakers": len(store.get_registry_summary()),
        "has_kg": (store.kg_dir / "graph.json").exists(),
        "data_root": str(store.root),
    }


# ──────────────────────────────────────────────────────────────
# Calls (تطابق calls.html)
# ──────────────────────────────────────────────────────────────

@router.get("/calls", response_model=list[CallSummary], tags=["calls"])
def list_calls() -> list[CallSummary]:
    """قائمة بكل المكالمات."""
    store = get_store()
    summaries = []
    for call_id in store.list_call_ids():
        s = store.get_call_summary(call_id)
        summaries.append(CallSummary(**s))
    return summaries


@router.get("/calls/{call_id}", response_model=CallDetails, tags=["calls"])
def get_call(call_id: str) -> CallDetails:
    """تفاصيل مكالمة محددة."""
    store = get_store()
    transcript = store.get_call_transcript(call_id)
    if not transcript:
        raise HTTPException(status_code=404, detail=f"المكالمة غير موجودة: {call_id}")

    segments = [
        CallSegment(
            speaker_name=s.get("speaker_name", "Unknown"),
            speaker_id=s.get("speaker_id", "UNKNOWN"),
            speaker_slot=s.get("speaker_slot", 0),
            start=s.get("start", 0),
            end=s.get("end", 0),
            text=s.get("text", ""),
            confidence=s.get("confidence", 0.8),
        )
        for s in transcript.get("segments", [])
    ]

    return CallDetails(
        call_id=call_id,
        duration_sec=transcript.get("duration_sec", 0.0),
        language=transcript.get("language", "ar"),
        segments=segments,
        metadata=transcript.get("metadata", {}),
        status=ProcessingStatus.COMPLETED,
    )


@router.get("/calls/{call_id}/entities", response_model=list[EntityResponse], tags=["calls"])
def get_call_entities(call_id: str) -> list[EntityResponse]:
    """كل الكيانات المستخرجة من مكالمة، مع حالة التدقيق."""
    store = get_store()
    nlp = store.get_call_nlp(call_id)
    if not nlp:
        raise HTTPException(status_code=404, detail=f"لا نتائج NLP لـ {call_id}")

    entities = nlp.get("nlp", {}).get("full_text_analysis", {}).get("entities", [])
    reviews = store.get_reviews(call_id)

    result = []
    for ent in entities:
        ent_id = make_entity_id(call_id, ent)
        review = reviews.get(ent_id, {})
        result.append(EntityResponse(
            id=ent_id,
            type=ent["type"],
            text=ent["text"],
            start=ent["start"],
            end=ent["end"],
            confidence=ent.get("confidence", 0.8),
            normalized=ent.get("normalized", ""),
            context=ent.get("context", ""),
            source=ent.get("source", "rule"),
            review_status=ReviewStatus(review.get("review_status", "pending")),
            reviewed_by=review.get("reviewed_by"),
            reviewed_at=review.get("reviewed_at"),
            review_note=review.get("note"),
        ))
    return result


@router.get("/calls/{call_id}/events", response_model=list[EventResponse], tags=["calls"])
def get_call_events(call_id: str) -> list[EventResponse]:
    """الأحداث المستخرجة من مكالمة."""
    store = get_store()
    nlp = store.get_call_nlp(call_id)
    if not nlp:
        raise HTTPException(status_code=404, detail=f"لا نتائج NLP لـ {call_id}")

    events = nlp.get("nlp", {}).get("enriched_events", [])
    if not events:
        events = nlp.get("nlp", {}).get("full_text_analysis", {}).get("events", [])

    reviews = store.get_reviews(call_id)
    result = []
    for ev in events:
        ev_id = make_event_id(call_id, ev)
        review = reviews.get(ev_id, {})
        result.append(EventResponse(
            id=ev_id,
            action=ev.get("action", "unknown"),
            verb_text=ev.get("verb_text", ""),
            sentence=ev.get("sentence", ""),
            sentence_start=ev.get("sentence_start", 0),
            actors=ev.get("actors", []),
            locations=ev.get("locations", []),
            times=ev.get("times", []),
            confidence=ev.get("confidence", 0.5),
            speaker_name=ev.get("speaker_name"),
            speaker_id=ev.get("speaker_id"),
            call_id=call_id,
            review_status=ReviewStatus(review.get("review_status", "pending")),
        ))
    return result


@router.get(
    "/calls/{call_id}/watchlist",
    response_model=list[WatchlistMatchResponse],
    tags=["calls"],
)
def get_call_watchlist(call_id: str) -> list[WatchlistMatchResponse]:
    """تطابقات watchlist في مكالمة."""
    store = get_store()
    nlp = store.get_call_nlp(call_id)
    if not nlp:
        raise HTTPException(status_code=404, detail=f"لا نتائج NLP لـ {call_id}")

    matches = nlp.get("nlp", {}).get("full_text_analysis", {}).get("watchlist_matches", [])
    return [
        WatchlistMatchResponse(
            id=f"{call_id}:wl:{m['start']}:{m.get('term', '')}",
            term=m["term"],
            matched_text=m.get("matched_text", m["term"]),
            start=m["start"],
            end=m["end"],
            note=m.get("note", ""),
            call_id=call_id,
        )
        for m in matches
    ]


# ──────────────────────────────────────────────────────────────
# Speakers (تطابق speakers.html)
# ──────────────────────────────────────────────────────────────

@router.get("/speakers", response_model=list[SpeakerSummary], tags=["speakers"])
def list_speakers() -> list[SpeakerSummary]:
    """قائمة بكل المتحدثين المعروفين."""
    store = get_store()
    summaries = []
    for vp in store.get_registry_summary():
        summaries.append(SpeakerSummary(
            speaker_id=vp["speaker_id"],
            name=vp["name"],
            status=vp.get("status", "unknown"),
            n_samples=vp.get("n_samples", 0),
            n_clips=vp.get("n_clips", 0),
            source_clips=vp.get("source_clips", []),
        ))
    return summaries


@router.get("/speakers/{speaker_id}", response_model=SpeakerDetails, tags=["speakers"])
def get_speaker(speaker_id: str) -> SpeakerDetails:
    """تفاصيل متحدث محدد."""
    store = get_store()
    for vp in store.get_registry_summary():
        if vp["speaker_id"] == speaker_id:
            return SpeakerDetails(
                speaker_id=vp["speaker_id"],
                name=vp["name"],
                status=vp.get("status", "unknown"),
                n_samples=vp.get("n_samples", 0),
                n_clips=vp.get("n_clips", 0),
                source_clips=vp.get("source_clips", []),
                participated_in=vp.get("participated_in", []),
            )
    raise HTTPException(status_code=404, detail=f"المتحدث غير موجود: {speaker_id}")


# ──────────────────────────────────────────────────────────────
# Knowledge Graph (تطابق graph.html)
# ──────────────────────────────────────────────────────────────

@router.get("/graph", response_model=GraphData, tags=["graph"])
def get_graph() -> GraphData:
    """رسم المعرفة كاملاً بصيغة الديمو."""
    store = get_store()
    data = store.get_kg_data()
    if not data:
        # نُرجع رسماً فارغاً بدل خطأ
        return GraphData(nodes=[], links=[], metadata={"empty": True})
    return GraphData(**data)


@router.get("/graph/summary", tags=["graph"])
def get_graph_summary() -> dict:
    """ملخص رسم المعرفة بدون البيانات الكاملة."""
    store = get_store()
    data = store.get_kg_data()
    if not data:
        return {"empty": True, "nodes": 0, "links": 0}

    # عدّ بالنوع
    from collections import Counter
    types_count = Counter(n["type"] for n in data.get("nodes", []))
    edge_types_count = Counter(l["type"] for l in data.get("links", []))

    return {
        "total_nodes": len(data.get("nodes", [])),
        "total_links": len(data.get("links", [])),
        "nodes_by_type": dict(types_count),
        "edges_by_type": dict(edge_types_count),
    }


# ──────────────────────────────────────────────────────────────
# Uploads (تطابق uploads.html)
# ──────────────────────────────────────────────────────────────

@router.post("/uploads", response_model=UploadResponse, tags=["uploads"])
async def upload_audio(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
) -> UploadResponse:
    """رفع ملف صوتي وبدء معالجته في الخلفية."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="اسم الملف مطلوب")

    # تحقق من النوع
    allowed = {".wav", ".mp3", ".m4a", ".flac", ".ogg"}
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed:
        raise HTTPException(
            status_code=415,
            detail=f"نوع غير مدعوم: {ext}. المدعوم: {', '.join(allowed)}",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="الملف فارغ")

    store = get_store()
    orch = get_orchestrator()

    call_id, file_path = store.save_upload(file.filename, content)

    # بدء المعالجة في الخلفية
    job_id = orch.process_call(file_path, call_id, in_background=True)

    return UploadResponse(
        call_id=call_id,
        filename=file.filename,
        size_bytes=len(content),
        status=ProcessingStatus.PROCESSING,
        message=f"بدأت المعالجة، job_id={job_id}",
    )


@router.get("/jobs", tags=["uploads"])
def list_jobs(limit: int = 20) -> list[dict]:
    """آخر وظائف المعالجة."""
    store = get_store()
    return store.list_recent_jobs(limit=limit)


@router.get("/jobs/{job_id}", response_model=ProcessingJob, tags=["uploads"])
def get_job(job_id: str) -> ProcessingJob:
    """حالة وظيفة معينة."""
    store = get_store()
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"job غير موجود: {job_id}")
    return ProcessingJob(**job)


# ──────────────────────────────────────────────────────────────
# Reports (تطابق reports.html)
# ──────────────────────────────────────────────────────────────

@router.get("/reports/summary", response_model=ReportSummary, tags=["reports"])
def report_summary() -> ReportSummary:
    """تقرير شامل للنظام."""
    store = get_store()

    call_ids = store.list_call_ids()

    # عدّ الكيانات والأحداث عبر كل المكالمات
    total_entities = 0
    total_events = 0
    watchlist_alerts = 0
    for cid in call_ids:
        nlp = store.get_call_nlp(cid)
        if not nlp:
            continue
        full = nlp.get("nlp", {}).get("full_text_analysis", {})
        total_entities += len(full.get("entities", []))
        total_events += len(full.get("events", []))
        watchlist_alerts += len(full.get("watchlist_matches", []))

    # KG stats
    kg_data = store.get_kg_data() or {}
    nodes = kg_data.get("nodes", [])
    links = kg_data.get("links", [])
    from collections import Counter
    nodes_by_type = dict(Counter(n["type"] for n in nodes))
    edges_by_type = dict(Counter(l["type"] for l in links))

    # ترتيب الكيانات
    persons = sorted(
        [n for n in nodes if n["type"] == "Person"],
        key=lambda n: -n.get("properties", {}).get("mention_count", 0),
    )[:10]
    locations = sorted(
        [n for n in nodes if n["type"] == "Location"],
        key=lambda n: -n.get("properties", {}).get("mention_count", 0),
    )[:10]
    keywords = sorted(
        [n for n in nodes if n["type"] == "Keyword"],
        key=lambda n: -n.get("properties", {}).get("mention_count", 0),
    )[:10]

    def to_top_entity(rank: int, n: dict) -> TopEntity:
        return TopEntity(
            rank=rank,
            label=n["label"],
            type=n["type"],
            score=float(n.get("properties", {}).get("mention_count", 0)),
            mention_count=n.get("properties", {}).get("mention_count", 0),
        )

    return ReportSummary(
        total_calls=len(call_ids),
        total_speakers=len(store.get_registry_summary()),
        total_entities=total_entities,
        total_events=total_events,
        total_kg_nodes=len(nodes),
        total_kg_edges=len(links),
        nodes_by_type=nodes_by_type,
        edges_by_type=edges_by_type,
        top_persons=[to_top_entity(i + 1, p) for i, p in enumerate(persons)],
        top_locations=[to_top_entity(i + 1, l) for i, l in enumerate(locations)],
        top_keywords=[to_top_entity(i + 1, k) for i, k in enumerate(keywords)],
        watchlist_alerts=watchlist_alerts,
    )


# ──────────────────────────────────────────────────────────────
# Reviews (HITL — جديد في المرحلة 7)
# ──────────────────────────────────────────────────────────────

@router.post(
    "/calls/{call_id}/reviews/{entity_id}",
    response_model=ReviewResponse,
    tags=["reviews"],
)
def submit_review(call_id: str, entity_id: str, review: ReviewRequest) -> ReviewResponse:
    """تسجيل مراجعة بشرية لكيان أو حدث.

    Args:
        call_id: معرّف المكالمة.
        entity_id: ID الكيان (من /calls/{call_id}/entities).
        review: قرار التدقيق (confirmed/rejected/edited).
    """
    store = get_store()

    # تأكيد وجود المكالمة
    if not store.get_call_nlp(call_id):
        raise HTTPException(status_code=404, detail=f"المكالمة غير موجودة: {call_id}")

    review_data = {
        "review_status": review.review_status.value,
        "reviewed_by": review.reviewed_by,
        "note": review.note,
        "edits": review.edits,
    }
    store.save_review(call_id, entity_id, review_data)

    saved = store.get_review_for(call_id, entity_id) or {}

    return ReviewResponse(
        id=entity_id,
        review_status=review.review_status,
        reviewed_by=review.reviewed_by,
        reviewed_at=saved.get("reviewed_at", datetime.now(timezone.utc).isoformat()),
        note=review.note,
        applied=True,
    )


@router.get("/calls/{call_id}/reviews", tags=["reviews"])
def list_reviews(call_id: str) -> dict:
    """كل المراجعات لمكالمة."""
    store = get_store()
    reviews = store.get_reviews(call_id)
    return {
        "call_id": call_id,
        "n_reviews": len(reviews),
        "reviews": reviews,
    }


@router.get("/reviews/pending", tags=["reviews"])
def list_pending_reviews(limit: int = 50) -> dict:
    """الكيانات التي تحتاج مراجعة في كل المكالمات (لقائمة المهام)."""
    store = get_store()
    pending = []
    for call_id in store.list_call_ids():
        nlp = store.get_call_nlp(call_id)
        if not nlp:
            continue
        entities = nlp.get("nlp", {}).get("full_text_analysis", {}).get("entities", [])
        reviews = store.get_reviews(call_id)

        for ent in entities:
            ent_id = make_entity_id(call_id, ent)
            if ent_id not in reviews:
                # نُعطي الأولوية للكيانات منخفضة الثقة
                pending.append({
                    "call_id": call_id,
                    "entity_id": ent_id,
                    "type": ent["type"],
                    "text": ent["text"],
                    "confidence": ent.get("confidence", 0.8),
                    "context": ent.get("context", ""),
                })

    # ترتيب: الأقل ثقة أولاً (أكثر حاجة للمراجعة)
    pending.sort(key=lambda x: x["confidence"])
    return {
        "total_pending": len(pending),
        "items": pending[:limit],
    }
