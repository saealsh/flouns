"""خط معالجة اللغة الطبيعية الموحَّد للمرحلة 5.

ينفّذ خمس خطوات على أي نص:
1. **NER**: استخلاص الكيانات.
2. **Keywords**: الكلمات المفتاحية المهمة.
3. **Watchlist** (اختياري): مصطلحات يتعقّبها المحلّل.
4. **Events**: استخلاص الأحداث (يستخدم نتائج NER).
5. **Coreference**: تجميع الكيانات المتشابهة.

الناتج:
    {
      "text_length": ...,
      "entities": [...],
      "entity_clusters": [...],
      "keywords": [...],
      "watchlist_matches": [...],
      "events": [...],
      "kg_triples": [...]
    }

يصمَّم للعمل مباشرة على مخرجات ASR (transcripts).

استخدام:
    from src.nlp.pipeline import analyze_text, analyze_transcript

    # تحليل نص بسيط
    result = analyze_text("اجتمع أحمد بسعيد في الرياض يوم الخميس...")

    # تحليل ملف transcript من المرحلة 4
    result = analyze_transcript(transcript_path)
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from src.nlp.coreference import EntityCluster, EntityResolver
from src.nlp.events import Event, EventExtractor, events_to_kg_triples
from src.nlp.keywords import Keyword, KeywordExtractor, Watchlist, WatchlistMatch
from src.nlp.ner import Entity, EntityExtractor
from src.utils.logging import get_logger

log = get_logger(__name__)


@dataclass
class NLPResult:
    """نتيجة تحليل نص واحد."""

    text_length: int
    entities: list[Entity] = field(default_factory=list)
    entity_clusters: list[EntityCluster] = field(default_factory=list)
    keywords: list[Keyword] = field(default_factory=list)
    watchlist_matches: list[WatchlistMatch] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)
    kg_triples: list[dict] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "text_length": self.text_length,
            "entities": [e.to_dict() for e in self.entities],
            "entity_clusters": [c.to_dict() for c in self.entity_clusters],
            "keywords": [k.to_dict() for k in self.keywords],
            "watchlist_matches": [m.to_dict() for m in self.watchlist_matches],
            "events": [e.to_dict() for e in self.events],
            "kg_triples": self.kg_triples,
            "metadata": self.metadata,
        }


class NLPPipeline:
    """خط معالجة قابل لإعادة الاستخدام (يحمّل النماذج مرة واحدة)."""

    def __init__(
        self,
        *,
        watchlist: Watchlist | None = None,
        use_spacy: bool = False,
        top_keywords: int = 20,
    ):
        """
        Args:
            watchlist: قائمة متابعة لمصطلحات اصطلاحية (اختياري).
            use_spacy: تفعيل spaCy إن مثبَّت.
            top_keywords: عدد الكلمات المفتاحية المرجَعة.
        """
        self.ner = EntityExtractor(use_spacy=use_spacy)
        self.keyword_extractor = KeywordExtractor()
        self.event_extractor = EventExtractor()
        self.resolver = EntityResolver()
        self.watchlist = watchlist
        self.top_keywords = top_keywords

    def analyze(self, text: str) -> NLPResult:
        """تحليل نص واحد كاملاً.

        Args:
            text: النص.

        Returns:
            NLPResult.
        """
        if not text:
            return NLPResult(text_length=0)

        # 1. NER
        entities = self.ner.extract(text)
        log.debug(f"استُخرج {len(entities)} كياناً")

        # 2. Coreference
        clusters = self.resolver.resolve(entities)

        # 3. Keywords
        keywords = self.keyword_extractor.extract(text, top_k=self.top_keywords)

        # 4. Watchlist
        watchlist_matches = []
        if self.watchlist:
            watchlist_matches = self.watchlist.scan(text)

        # 5. Events
        events = self.event_extractor.extract(text, entities=entities)
        triples = events_to_kg_triples(events)

        return NLPResult(
            text_length=len(text),
            entities=entities,
            entity_clusters=clusters,
            keywords=keywords,
            watchlist_matches=watchlist_matches,
            events=events,
            kg_triples=triples,
            metadata={
                "n_entities": len(entities),
                "n_unique_entities": len(clusters),
                "n_keywords": len(keywords),
                "n_watchlist_matches": len(watchlist_matches),
                "n_events": len(events),
                "n_kg_triples": len(triples),
            },
        )


def analyze_text(
    text: str,
    *,
    watchlist: Watchlist | None = None,
) -> NLPResult:
    """واجهة بسيطة لتحليل نص واحد.

    Args:
        text: النص.
        watchlist: قائمة مصطلحات اختيارية.

    Returns:
        NLPResult.
    """
    pipeline = NLPPipeline(watchlist=watchlist)
    return pipeline.analyze(text)


def analyze_transcript(
    transcript_path: Path | str,
    *,
    watchlist: Watchlist | None = None,
) -> dict:
    """تحليل ملف transcript من المرحلة 4 (ASR + diarization).

    ملف transcript المتوقّع يتبع صيغة export المرحلة 4:
        {
          "call_id": "...",
          "segments": [
            {"speaker_name": "...", "text": "...", "start": ..., "end": ...},
            ...
          ]
        }

    Args:
        transcript_path: مسار ملف JSON.
        watchlist: قائمة مصطلحات اختيارية.

    Returns:
        قاموس بنفس البنية + قسم "nlp" يحوي نتائج التحليل.
    """
    transcript_path = Path(transcript_path)
    if not transcript_path.exists():
        raise FileNotFoundError(transcript_path)

    with open(transcript_path, encoding="utf-8") as f:
        transcript = json.load(f)

    segments = transcript.get("segments", [])
    if not segments:
        log.warning(f"لا segments في {transcript_path}")
        return {**transcript, "nlp": NLPResult(text_length=0).to_dict()}

    # 1. تحليل النص الكامل (لاستخراج الأحداث والـ keywords على المستوى الكلي)
    full_text = " ".join(s.get("text", "") for s in segments)
    pipeline = NLPPipeline(watchlist=watchlist)
    full_result = pipeline.analyze(full_text)

    # 2. تحليل كل سطر على حدة (للحصول على كيانات/أحداث مرتبطة بالمتحدثين)
    per_segment_results = []
    for seg in segments:
        text = seg.get("text", "")
        seg_result = pipeline.analyze(text) if text else NLPResult(text_length=0)
        per_segment_results.append({
            "speaker_name": seg.get("speaker_name"),
            "speaker_id": seg.get("speaker_id"),
            "start": seg.get("start"),
            "end": seg.get("end"),
            "text": text,
            "entities": [e.to_dict() for e in seg_result.entities],
            "events": [e.to_dict() for e in seg_result.events],
            "watchlist_matches": [m.to_dict() for m in seg_result.watchlist_matches],
        })

    # 3. ربط الأحداث بالمتحدثين (من segments)
    enriched_events = _attribute_events_to_speakers(
        full_result.events, segments
    )

    return {
        **transcript,
        "nlp": {
            "full_text_analysis": full_result.to_dict(),
            "per_segment": per_segment_results,
            "enriched_events": [e.to_dict() if hasattr(e, "to_dict") else e
                                for e in enriched_events],
        },
    }


def _attribute_events_to_speakers(
    events: list[Event],
    segments: list[dict],
) -> list[dict]:
    """إضافة المتحدث المؤكَّد إلى الأحداث.

    لكل حدث (يحوي موقع جملة في النص الكامل)، نُحدّد أي segment يحويه
    ونُضيف اسم المتحدث.
    """
    # نبني خريطة موقع → segment
    cursor = 0
    seg_ranges = []
    for seg in segments:
        text = seg.get("text", "")
        seg_ranges.append((cursor, cursor + len(text) + 1, seg))  # +1 لمسافة الفصل
        cursor += len(text) + 1

    enriched = []
    for event in events:
        ev_dict = event.to_dict()
        # ابحث عن الـ segment الذي يحوي بداية الجملة
        for start, end, seg in seg_ranges:
            if start <= event.sentence_start < end:
                ev_dict["speaker_name"] = seg.get("speaker_name")
                ev_dict["speaker_id"] = seg.get("speaker_id")
                ev_dict["segment_start"] = seg.get("start")
                ev_dict["segment_end"] = seg.get("end")
                break
        enriched.append(ev_dict)

    return enriched
