"""باني رسم المعرفة من مخرجات NLP.

يأخذ نتائج المرحلة 5 (entities, events, watchlist_matches, kg_triples) ويبني
رسماً بيانياً موجَّهاً يحوي:
- عقد Call لكل مكالمة
- عقد Speaker للمتحدثين
- عقد Person/Location/... للكيانات
- علاقات MENTIONED, MET_AT, AGREED_WITH... من الأحداث
- علاقات MATCHES_WATCHLIST من قائمة المتابعة

التصميم:
- KGBuilder يحمل backend واحداً (NetworkX أو Neo4j).
- ingest_call() تأخذ ملف NLP واحد → تضيف كل عقده وعلاقاته.
- ingest_directory() تعالج مجلداً كاملاً.

استخدام:
    from src.kg.builder import KGBuilder
    from src.kg.backends import NetworkXBackend

    builder = KGBuilder(NetworkXBackend())
    builder.ingest_call_from_file("data/nlp/call_001.nlp.json")
    builder.backend.save("data/kg/graph.json")
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.kg.backends import KGBackend
from src.kg.schema import (
    ACTION_TO_EDGE,
    NER_TO_NODE_TYPE,
    Edge,
    EdgeType,
    Node,
    NodeType,
    make_node_id,
)
from src.utils.logging import get_logger

log = get_logger(__name__)


class KGBuilder:
    """يبني رسم المعرفة من مخرجات NLP."""

    def __init__(self, backend: KGBackend):
        self.backend = backend
        self.stats = {
            "calls_ingested": 0,
            "nodes_added": 0,
            "edges_added": 0,
            "events_processed": 0,
        }

    def ingest_call(
        self,
        call_data: dict,
        *,
        call_id: str | None = None,
    ) -> dict:
        """ابتلاع مكالمة كاملة من مخرج المرحلة 5.

        Args:
            call_data: قاموس بصيغة مخرج analyze_transcript:
                {
                  "call_id": ...,
                  "segments": [...],
                  "nlp": {
                    "full_text_analysis": {...},
                    "per_segment": [...],
                    "enriched_events": [...]
                  }
                }
            call_id: تجاوز call_id من البيانات.

        Returns:
            إحصاءات الـ ingestion لهذه المكالمة.
        """
        call_id = call_id or call_data.get("call_id") or "UNKNOWN_CALL"
        nlp = call_data.get("nlp", {})

        # 1. إنشاء عقدة المكالمة
        call_node = Node(
            id=make_node_id(NodeType.CALL, call_id),
            type=NodeType.CALL,
            label=call_id,
            properties={
                "duration_sec": call_data.get("duration_sec", 0),
                "language": call_data.get("language", "ar"),
                "n_segments": len(call_data.get("segments", [])),
            },
        )
        self._add_node(call_node)
        call_node_id = call_node.id

        before_nodes = self.backend.node_count()
        before_edges = self.backend.edge_count()

        # 2. إنشاء عقد المتحدثين من segments
        speakers_seen: dict[str, str] = {}  # speaker_id → node_id
        for seg in call_data.get("segments", []):
            spk_id = seg.get("speaker_id") or seg.get("speaker_name", "UNKNOWN")
            spk_name = seg.get("speaker_name") or spk_id

            speaker_node = Node(
                id=make_node_id(NodeType.SPEAKER, spk_id),
                type=NodeType.SPEAKER,
                label=spk_name,
                properties={
                    "mention_count": 1,
                    "n_segments": 1,
                },
            )
            self._add_node(speaker_node)
            speakers_seen[spk_id] = speaker_node.id

            # علاقة Speaker → Call
            self._add_edge(Edge(
                source=speaker_node.id,
                target=call_node_id,
                type=EdgeType.PARTICIPATED_IN,
                properties={"call_id": call_id},
            ))

            # إن كان اسم المتحدث ليس مجرد ID (مثل SPK_01)، نُنشئ Person عقدة أيضاً
            if not spk_id.startswith("SPK_") and spk_name == spk_id:
                person_node = Node(
                    id=make_node_id(NodeType.PERSON, spk_name),
                    type=NodeType.PERSON,
                    label=spk_name,
                    properties={"mention_count": 1, "is_speaker": True},
                )
                self._add_node(person_node)
                # علاقة Speaker → Person (تحديد الهوية)
                self._add_edge(Edge(
                    source=speaker_node.id,
                    target=person_node.id,
                    type=EdgeType.IDENTIFIED_AS,
                    properties={"call_id": call_id, "confidence": 0.9},
                ))

        # 3. معالجة الكيانات على المستوى الكلي
        full_analysis = nlp.get("full_text_analysis", {})
        entities = full_analysis.get("entities", [])
        entity_node_ids: dict[str, str] = {}  # text → node_id

        for ent in entities:
            node_type = NER_TO_NODE_TYPE.get(ent["type"])
            if not node_type:
                continue

            ent_node = Node(
                id=make_node_id(node_type, ent.get("normalized") or ent["text"]),
                type=node_type,
                label=ent["text"],
                properties={
                    "mention_count": 1,
                    "confidence": ent.get("confidence", 0.8),
                    "type": ent["type"],
                    "source": ent.get("source", "ner"),
                },
            )
            self._add_node(ent_node)
            entity_node_ids[ent["text"]] = ent_node.id

            # علاقة Entity → Call
            self._add_edge(Edge(
                source=ent_node.id,
                target=call_node_id,
                type=EdgeType.MENTIONED_IN,
                properties={"call_id": call_id},
            ))

        # 4. معالجة الـ per_segment (من نطق باسم من)
        per_segment = nlp.get("per_segment", [])
        for seg in per_segment:
            spk_id = seg.get("speaker_id") or seg.get("speaker_name", "UNKNOWN")
            speaker_node_id = speakers_seen.get(spk_id)
            if not speaker_node_id:
                continue

            for ent in seg.get("entities", []):
                node_type = NER_TO_NODE_TYPE.get(ent["type"])
                if not node_type:
                    continue
                # نستخدم نفس entity node من الخطوة 3
                ent_id = make_node_id(node_type, ent.get("normalized") or ent["text"])
                if self.backend.has_node(ent_id):
                    self._add_edge(Edge(
                        source=speaker_node_id,
                        target=ent_id,
                        type=EdgeType.MENTIONED,
                        properties={
                            "call_id": call_id,
                            "segment_start": seg.get("start"),
                        },
                    ))

        # 5. معالجة الأحداث (enriched_events أفضل لأنها مربوطة بمتحدث)
        events = nlp.get("enriched_events") or full_analysis.get("events", [])
        for ev in events:
            self._ingest_event(ev, call_id, call_node_id, speakers_seen)

        # 6. معالجة watchlist matches
        watchlist_matches = full_analysis.get("watchlist_matches", [])
        for m in watchlist_matches:
            keyword_node = Node(
                id=make_node_id(NodeType.KEYWORD, m["term"]),
                type=NodeType.KEYWORD,
                label=m["term"],
                properties={
                    "mention_count": 1,
                    "note": m.get("note", ""),
                    "is_watchlist": True,
                },
            )
            self._add_node(keyword_node)
            self._add_edge(Edge(
                source=call_node_id,
                target=keyword_node.id,
                type=EdgeType.MATCHES_WATCHLIST,
                properties={
                    "call_id": call_id,
                    "matched_text": m["matched_text"],
                    "position": m.get("start"),
                },
            ))

        # 7. معالجة kg_triples (من events.py)
        triples = full_analysis.get("kg_triples", [])
        for t in triples:
            self._ingest_triple(t, call_id)

        self.stats["calls_ingested"] += 1
        added_nodes = self.backend.node_count() - before_nodes
        added_edges = self.backend.edge_count() - before_edges

        return {
            "call_id": call_id,
            "nodes_added": added_nodes,
            "edges_added": added_edges,
            "entities_processed": len(entities),
            "events_processed": len(events),
            "watchlist_matches": len(watchlist_matches),
        }

    def _ingest_event(
        self,
        event: dict,
        call_id: str,
        call_node_id: str,
        speakers_seen: dict[str, str],
    ) -> None:
        """إضافة عقدة Event + علاقاتها."""
        action = event.get("action", "unknown")
        verb_text = event.get("verb_text", "")
        sentence = event.get("sentence", "")[:100]  # حد أقصى للعرض

        # عقدة الحدث: ID فريد بنوع الإجراء + المكالمة + الموقع
        event_id_suffix = f"{call_id}_{event.get('sentence_start', 0)}_{action}"
        event_node = Node(
            id=make_node_id(NodeType.EVENT, event_id_suffix),
            type=NodeType.EVENT,
            label=f"{action}: {sentence[:50]}",
            properties={
                "action": action,
                "verb_text": verb_text,
                "sentence": sentence,
                "confidence": event.get("confidence", 0.5),
                "call_id": call_id,
                "speaker_name": event.get("speaker_name"),
                "segment_start": event.get("segment_start"),
            },
        )
        self._add_node(event_node)

        # علاقات Event → Actors
        for actor in event.get("actors", []):
            actor_node_id = make_node_id(
                NodeType.PERSON,
                actor.get("normalized") or actor["text"],
            )
            if self.backend.has_node(actor_node_id):
                self._add_edge(Edge(
                    source=event_node.id,
                    target=actor_node_id,
                    type=EdgeType.HAS_ACTOR,
                    properties={"call_id": call_id},
                ))

        # علاقات Event → Locations
        for loc in event.get("locations", []):
            loc_node_id = make_node_id(
                NodeType.LOCATION,
                loc.get("normalized") or loc["text"],
            )
            if self.backend.has_node(loc_node_id):
                self._add_edge(Edge(
                    source=event_node.id,
                    target=loc_node_id,
                    type=EdgeType.OCCURRED_AT,
                    properties={"call_id": call_id},
                ))

        # علاقات Event → Times
        for time in event.get("times", []):
            t_type = time.get("type", "DATE")
            node_type = NodeType.DATE if t_type == "DATE" else NodeType.TIME
            time_node_id = make_node_id(
                node_type,
                time.get("normalized") or time["text"],
            )
            if self.backend.has_node(time_node_id):
                self._add_edge(Edge(
                    source=event_node.id,
                    target=time_node_id,
                    type=EdgeType.OCCURRED_ON,
                    properties={"call_id": call_id},
                ))

        # ربط الحدث بمتحدثه (إن كان معروفاً)
        speaker_name_or_id = event.get("speaker_id") or event.get("speaker_name")
        if speaker_name_or_id and speaker_name_or_id in speakers_seen:
            self._add_edge(Edge(
                source=speakers_seen[speaker_name_or_id],
                target=event_node.id,
                type=EdgeType.MENTIONED,
                properties={"call_id": call_id},
            ))

        self.stats["events_processed"] += 1

    def _ingest_triple(self, triple: dict, call_id: str) -> None:
        """إضافة triple مباشر من events.py."""
        relation = triple.get("relation", "")
        edge_type = ACTION_TO_EDGE.get(relation)
        if not edge_type:
            return

        subj_text = triple.get("subject", "")
        obj_text = triple.get("object", "")
        if not subj_text or not obj_text:
            return

        # نتوقع أن العقد موجودة سلفاً (من خطوة الكيانات).
        # نبحث عنها بالنوع المحتمل
        subj_id = self._find_node_id_for(subj_text)
        obj_id = self._find_node_id_for(obj_text)
        if not subj_id or not obj_id:
            return

        self._add_edge(Edge(
            source=subj_id,
            target=obj_id,
            type=edge_type,
            properties={
                **triple.get("attributes", {}),
                "call_id": call_id,
            },
        ))

    def _find_node_id_for(self, name: str) -> str | None:
        """البحث عن node_id لكيان بالاسم (نُجرّب الأنواع المحتملة)."""
        # نُجرّب الأنواع الشائعة بالترتيب
        for nt in (NodeType.PERSON, NodeType.LOCATION, NodeType.ORGANIZATION,
                   NodeType.DATE, NodeType.TIME):
            candidate = make_node_id(nt, name)
            if self.backend.has_node(candidate):
                return candidate
        return None

    def _add_node(self, node: Node) -> None:
        """إضافة عقدة وتحديث الإحصاءات."""
        existed = self.backend.has_node(node.id)
        self.backend.add_node(node)
        if not existed:
            self.stats["nodes_added"] += 1

    def _add_edge(self, edge: Edge) -> None:
        before = self.backend.edge_count()
        self.backend.add_edge(edge)
        if self.backend.edge_count() > before:
            self.stats["edges_added"] += 1

    def ingest_call_from_file(self, path: Path | str) -> dict:
        """قراءة ملف NLP من مخرج المرحلة 5 وابتلاعه."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(path)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return self.ingest_call(data)

    def ingest_directory(
        self,
        directory: Path | str,
        *,
        pattern: str = "*.nlp.json",
    ) -> dict:
        """ابتلاع كل ملفات NLP في مجلد.

        Returns:
            ملخص الإحصاءات.
        """
        directory = Path(directory)
        if not directory.exists():
            raise FileNotFoundError(directory)

        files = sorted(directory.glob(pattern))
        per_call = []
        for f in files:
            try:
                log.info(f"⏳ ابتلاع {f.name}")
                result = self.ingest_call_from_file(f)
                per_call.append(result)
            except Exception as e:
                log.error(f"❌ فشل {f.name}: {e}")
                per_call.append({"file": f.name, "error": str(e)})

        return {
            "n_files": len(files),
            "per_call": per_call,
            "total_stats": self.stats,
        }
