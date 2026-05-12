"""استعلامات معرفية شائعة على رسم المعرفة.

أمثلة استخدام شائعة في تحليل المكالمات:
- من شارك في أي مكالمات؟
- من اجتمع بمن؟
- الجدول الزمني لشخص محدد.
- الأماكن المرتبطة بشخص.
- أكثر الأشخاص ذِكراً.
- المسار بين شخصين (هل يعرفان بعضهما عبر طرف ثالث؟).
- المتحدثون الأكثر مركزية في الشبكة.

استخدام:
    from src.kg.queries import KGQueries

    q = KGQueries(backend)
    print(q.top_persons(limit=5))
    print(q.who_met_whom())
    print(q.path_between("Person:احمد", "Person:خالد"))
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from src.kg.backends import KGBackend, NetworkXBackend
from src.kg.schema import Edge, EdgeType, Node, NodeType
from src.utils.logging import get_logger

log = get_logger(__name__)


@dataclass
class EntityRanking:
    """ترتيب كيان بمقياس معين."""
    node: Node
    score: float
    rank: int


class KGQueries:
    """واجهة استعلامات عالية المستوى."""

    def __init__(self, backend: KGBackend):
        self.backend = backend

    # ──────────────────────────────────────────────
    # إحصاءات عامة
    # ──────────────────────────────────────────────

    def summary(self) -> dict:
        """ملخص الرسم: عدد العقد/العلاقات بكل نوع."""
        node_types = Counter()
        for node in self.backend.all_nodes():
            node_types[node.type.value] += 1

        edge_types = Counter()
        for edge in self.backend.all_edges():
            edge_types[edge.type.value] += 1

        return {
            "total_nodes": self.backend.node_count(),
            "total_edges": self.backend.edge_count(),
            "nodes_by_type": dict(node_types),
            "edges_by_type": dict(edge_types),
        }

    # ──────────────────────────────────────────────
    # تصنيف الكيانات
    # ──────────────────────────────────────────────

    def top_entities_by_type(
        self,
        node_type: NodeType,
        *,
        limit: int = 10,
        metric: str = "mention_count",
    ) -> list[EntityRanking]:
        """أعلى الكيانات من نوع معين حسب مقياس.

        Args:
            node_type: نوع العقدة المطلوب.
            limit: عدد النتائج.
            metric: "mention_count" أو "degree" (عدد العلاقات).

        Returns:
            قائمة EntityRanking مرتبة تنازلياً.
        """
        nodes = self.backend.nodes_by_type(node_type)
        scored = []
        for node in nodes:
            if metric == "degree":
                score = len(self.backend.neighbors(node.id))
            else:
                score = node.properties.get(metric, 0)
            scored.append((node, score))

        scored.sort(key=lambda x: -x[1])
        return [
            EntityRanking(node=n, score=float(s), rank=i + 1)
            for i, (n, s) in enumerate(scored[:limit])
        ]

    def top_persons(self, limit: int = 10) -> list[EntityRanking]:
        """أكثر الأشخاص ذِكراً."""
        return self.top_entities_by_type(NodeType.PERSON, limit=limit)

    def top_locations(self, limit: int = 10) -> list[EntityRanking]:
        return self.top_entities_by_type(NodeType.LOCATION, limit=limit)

    def top_keywords(self, limit: int = 10) -> list[EntityRanking]:
        return self.top_entities_by_type(NodeType.KEYWORD, limit=limit)

    # ──────────────────────────────────────────────
    # علاقات شخصية
    # ──────────────────────────────────────────────

    def who_met_whom(self) -> list[dict]:
        """قائمة كل أزواج الأشخاص الذين اجتمعوا.

        Returns:
            قائمة {"person_a": ..., "person_b": ..., "count": ...}
        """
        results = []
        for edge in self.backend.get_edges(edge_type=EdgeType.MET_WITH):
            a = self.backend.get_node(edge.source)
            b = self.backend.get_node(edge.target)
            if a and b:
                results.append({
                    "person_a": a.label,
                    "person_b": b.label,
                    "count": edge.properties.get("count", 1),
                    "call_ids": edge.properties.get("call_ids", []),
                })
        return sorted(results, key=lambda r: -r["count"])

    def persons_at_location(self, location_label: str) -> list[Node]:
        """من كان في مكان محدد؟

        نبحث عن: Person --(MET_AT|WENT_TO|ARRIVED_AT)--> Location
        أو Event --OCCURRED_AT--> Location و Event --HAS_ACTOR--> Person
        """
        # نوجد عقدة المكان
        loc_id = None
        for n in self.backend.nodes_by_type(NodeType.LOCATION):
            if n.label == location_label or location_label in n.label:
                loc_id = n.id
                break
        if not loc_id:
            return []

        persons = set()

        # المسار المباشر: Person → Location
        for et in (EdgeType.MET_AT, EdgeType.WENT_TO, EdgeType.ARRIVED_AT):
            for edge in self.backend.get_edges(target=loc_id, edge_type=et):
                src = self.backend.get_node(edge.source)
                if src and src.type == NodeType.PERSON:
                    persons.add(src.id)

        # المسار غير المباشر: Event → Location, Event → Person
        for edge in self.backend.get_edges(target=loc_id, edge_type=EdgeType.OCCURRED_AT):
            event_id = edge.source
            for ev_edge in self.backend.get_edges(source=event_id, edge_type=EdgeType.HAS_ACTOR):
                target = self.backend.get_node(ev_edge.target)
                if target and target.type == NodeType.PERSON:
                    persons.add(target.id)

        return [self.backend.get_node(pid) for pid in persons if self.backend.get_node(pid)]

    def person_timeline(self, person_label: str) -> list[dict]:
        """الجدول الزمني لشخص: الأحداث التي شارك فيها مرتبة زمنياً.

        Returns:
            قائمة {event_label, action, time, location, call_id}
        """
        # إيجاد عقدة الشخص
        person_id = None
        for n in self.backend.nodes_by_type(NodeType.PERSON):
            if n.label == person_label or person_label in n.label:
                person_id = n.id
                break
        if not person_id:
            return []

        timeline = []
        # الأحداث التي يشارك فيها هذا الشخص: Event --HAS_ACTOR--> Person
        for edge in self.backend.get_edges(target=person_id, edge_type=EdgeType.HAS_ACTOR):
            event_node = self.backend.get_node(edge.source)
            if not event_node or event_node.type != NodeType.EVENT:
                continue

            # نبحث عن زمن ومكان هذا الحدث
            times = []
            locations = []
            for ev_edge in self.backend.get_edges(source=event_node.id):
                target = self.backend.get_node(ev_edge.target)
                if not target:
                    continue
                if ev_edge.type == EdgeType.OCCURRED_ON:
                    times.append(target.label)
                elif ev_edge.type == EdgeType.OCCURRED_AT:
                    locations.append(target.label)

            timeline.append({
                "event_id": event_node.id,
                "label": event_node.label,
                "action": event_node.properties.get("action"),
                "sentence": event_node.properties.get("sentence", ""),
                "times": times,
                "locations": locations,
                "call_id": event_node.properties.get("call_id"),
                "segment_start": event_node.properties.get("segment_start"),
                "speaker_name": event_node.properties.get("speaker_name"),
            })

        # ترتيب بـ call_id ثم segment_start
        timeline.sort(key=lambda x: (
            x.get("call_id") or "",
            x.get("segment_start") or 0,
        ))
        return timeline

    def path_between(
        self,
        source_label: str,
        target_label: str,
        node_type: NodeType = NodeType.PERSON,
    ) -> list[dict] | None:
        """أقصر مسار بين كيانين (يتجاهل اتجاه العلاقات).

        Returns:
            قائمة العقد على المسار (مع معلوماتها)، أو None إن لم يوجد مسار.
        """
        # إيجاد العقد
        source_id = self._find_node_by_label(source_label, node_type)
        target_id = self._find_node_by_label(target_label, node_type)
        if not source_id or not target_id:
            return None

        # نستخدم shortest_path من NetworkX (إن الـ backend يدعمه)
        if not isinstance(self.backend, NetworkXBackend):
            log.warning("path_between يتطلب NetworkXBackend حالياً")
            return None

        path_ids = self.backend.shortest_path(source_id, target_id)
        if not path_ids:
            return None

        return [
            self.backend.get_node(nid).to_dict()  # type: ignore
            for nid in path_ids
        ]

    def _find_node_by_label(self, label: str, node_type: NodeType) -> str | None:
        """البحث عن عقدة بنوعها واسمها."""
        for n in self.backend.nodes_by_type(node_type):
            if n.label == label or label in n.label:
                return n.id
        return None

    # ──────────────────────────────────────────────
    # تحليل الشبكة
    # ──────────────────────────────────────────────

    def central_persons(self, limit: int = 5) -> list[EntityRanking]:
        """الأشخاص الأكثر مركزية (يربطون مجموعات مختلفة).

        نستخدم betweenness centrality من NetworkX.
        """
        if not isinstance(self.backend, NetworkXBackend):
            log.warning("central_persons يحتاج NetworkXBackend")
            return []

        bc = self.backend.betweenness_centrality()
        person_scores = []
        for n in self.backend.nodes_by_type(NodeType.PERSON):
            person_scores.append((n, bc.get(n.id, 0.0)))

        person_scores.sort(key=lambda x: -x[1])
        return [
            EntityRanking(node=n, score=s, rank=i + 1)
            for i, (n, s) in enumerate(person_scores[:limit])
            if s > 0
        ]

    def communities(self) -> list[list[str]]:
        """اكتشاف المكونات المتصلة (مجموعات منفصلة)."""
        if not isinstance(self.backend, NetworkXBackend):
            return []
        components = self.backend.connected_components()
        # نُرجع labels بدل IDs للقراءة
        result = []
        for comp in components:
            labels = []
            for nid in comp:
                n = self.backend.get_node(nid)
                if n:
                    labels.append(n.label)
            result.append(sorted(labels))
        return sorted(result, key=lambda r: -len(r))

    # ──────────────────────────────────────────────
    # watchlist analysis
    # ──────────────────────────────────────────────

    def calls_matching_watchlist(self) -> list[dict]:
        """المكالمات التي ذُكر فيها مصطلح من watchlist.

        Returns:
            قائمة {call_id, keyword, matched_text}
        """
        results = []
        for edge in self.backend.get_edges(edge_type=EdgeType.MATCHES_WATCHLIST):
            call_node = self.backend.get_node(edge.source)
            kw_node = self.backend.get_node(edge.target)
            if call_node and kw_node:
                results.append({
                    "call_id": call_node.label,
                    "keyword": kw_node.label,
                    "matched_text": edge.properties.get("matched_text"),
                    "note": kw_node.properties.get("note", ""),
                })
        return results

    def speakers_using_watchlist_term(self, term: str) -> list[Node]:
        """المتحدثون الذين ذكروا مصطلحاً من watchlist.

        نبحث عن: Speaker --MENTIONED--> Keyword
        """
        kw_id = None
        for n in self.backend.nodes_by_type(NodeType.KEYWORD):
            if n.label == term or term in n.label:
                kw_id = n.id
                break
        if not kw_id:
            return []

        speakers = set()
        for edge in self.backend.get_edges(target=kw_id, edge_type=EdgeType.MENTIONED):
            src = self.backend.get_node(edge.source)
            if src and src.type == NodeType.SPEAKER:
                speakers.add(src.id)
        return [self.backend.get_node(sid) for sid in speakers if self.backend.get_node(sid)]
