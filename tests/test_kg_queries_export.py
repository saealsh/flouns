"""اختبارات لـ src.kg.queries و src.kg.export."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from src.kg.backends import NetworkXBackend
from src.kg.export import (
    export_to_cytoscape,
    export_to_demo_format,
    export_to_dot,
)
from src.kg.queries import KGQueries
from src.kg.schema import Edge, EdgeType, Node, NodeType


@pytest.fixture
def populated_backend():
    """رسم جاهز للاختبار."""
    b = NetworkXBackend()

    # 2 مكالمات
    b.add_node(Node(id="Call:C1", type=NodeType.CALL, label="C1"))
    b.add_node(Node(id="Call:C2", type=NodeType.CALL, label="C2"))

    # 3 أشخاص بمستويات ذِكر مختلفة
    b.add_node(Node(id="Person:ahmad", type=NodeType.PERSON, label="أحمد",
                    properties={"mention_count": 5}))
    b.add_node(Node(id="Person:khaled", type=NodeType.PERSON, label="خالد",
                    properties={"mention_count": 3}))
    b.add_node(Node(id="Person:saeed", type=NodeType.PERSON, label="سعيد",
                    properties={"mention_count": 1}))

    # موقع واحد
    b.add_node(Node(id="Location:riyadh", type=NodeType.LOCATION, label="الرياض",
                    properties={"mention_count": 4}))

    # مصطلح watchlist
    b.add_node(Node(id="Keyword:shipment", type=NodeType.KEYWORD, label="الشحنة",
                    properties={"mention_count": 2, "note": "متعقَّب"}))

    # علاقات
    b.add_edge(Edge(source="Person:ahmad", target="Person:khaled",
                    type=EdgeType.MET_WITH, properties={"call_id": "C1"}))
    b.add_edge(Edge(source="Person:khaled", target="Person:saeed",
                    type=EdgeType.AGREED_WITH, properties={"call_id": "C2"}))
    b.add_edge(Edge(source="Person:ahmad", target="Location:riyadh",
                    type=EdgeType.WENT_TO, properties={"call_id": "C1"}))
    b.add_edge(Edge(source="Call:C1", target="Keyword:shipment",
                    type=EdgeType.MATCHES_WATCHLIST,
                    properties={"matched_text": "الشحنة الجاهزة"}))

    return b


class TestSummary:
    def test_summary_structure(self, populated_backend):
        q = KGQueries(populated_backend)
        s = q.summary()
        assert "total_nodes" in s
        assert "total_edges" in s
        assert "nodes_by_type" in s
        assert s["total_nodes"] == 7
        assert s["nodes_by_type"]["Person"] == 3


class TestTopEntities:
    def test_top_persons_sorted(self, populated_backend):
        q = KGQueries(populated_backend)
        results = q.top_persons(limit=3)
        assert len(results) == 3
        # أحمد بـ mention_count=5 أعلى
        assert results[0].node.label == "أحمد"
        assert results[0].rank == 1

    def test_top_locations(self, populated_backend):
        q = KGQueries(populated_backend)
        results = q.top_locations(limit=5)
        assert len(results) == 1
        assert results[0].node.label == "الرياض"


class TestWhoMetWhom:
    def test_finds_meetings(self, populated_backend):
        q = KGQueries(populated_backend)
        pairs = q.who_met_whom()
        assert len(pairs) >= 1
        # أحمد ↔ خالد
        labels = {(p["person_a"], p["person_b"]) for p in pairs}
        assert any(
            ("أحمد", "خالد") == lp or ("خالد", "أحمد") == lp
            for lp in labels
        )

    def test_empty_when_no_meetings(self):
        b = NetworkXBackend()
        q = KGQueries(b)
        assert q.who_met_whom() == []


class TestPersonsAtLocation:
    def test_finds_person_at_location(self, populated_backend):
        q = KGQueries(populated_backend)
        persons = q.persons_at_location("الرياض")
        # أحمد ذهب إلى الرياض
        labels = {p.label for p in persons}
        assert "أحمد" in labels

    def test_returns_empty_for_unknown_location(self, populated_backend):
        q = KGQueries(populated_backend)
        assert q.persons_at_location("جدة") == []


class TestPathBetween:
    def test_direct_path(self, populated_backend):
        q = KGQueries(populated_backend)
        # أحمد → خالد مباشر
        path = q.path_between("أحمد", "خالد")
        assert path is not None
        assert len(path) == 2

    def test_indirect_path(self, populated_backend):
        q = KGQueries(populated_backend)
        # أحمد → خالد → سعيد (طريق غير مباشر)
        path = q.path_between("أحمد", "سعيد")
        assert path is not None
        assert len(path) == 3  # 3 عقد على المسار

    def test_no_path(self, populated_backend):
        # نضيف شخصاً معزولاً
        populated_backend.add_node(
            Node(id="Person:isolated", type=NodeType.PERSON, label="معزول")
        )
        q = KGQueries(populated_backend)
        path = q.path_between("أحمد", "معزول")
        assert path is None


class TestWatchlist:
    def test_calls_matching_watchlist(self, populated_backend):
        q = KGQueries(populated_backend)
        matches = q.calls_matching_watchlist()
        assert len(matches) == 1
        assert matches[0]["keyword"] == "الشحنة"
        assert matches[0]["call_id"] == "C1"


class TestCommunities:
    def test_detects_components(self, populated_backend):
        q = KGQueries(populated_backend)
        comps = q.communities()
        # على الأقل مكوّن واحد كبير (يحوي أحمد، خالد، سعيد، الرياض، الشحنة)
        assert len(comps) >= 1
        biggest = comps[0]
        assert len(biggest) >= 4


class TestExportDemoFormat:
    def test_export_creates_file(self, populated_backend, tmp_path):
        path = tmp_path / "demo.json"
        data = export_to_demo_format(populated_backend, path)
        assert path.exists()
        # يحوي nodes و links
        assert "nodes" in data
        assert "links" in data
        assert len(data["nodes"]) == 7
        assert len(data["links"]) >= 4

    def test_nodes_have_color(self, populated_backend, tmp_path):
        path = tmp_path / "demo.json"
        data = export_to_demo_format(populated_backend, path)
        for node in data["nodes"]:
            assert "color" in node
            assert node["color"].startswith("#")

    def test_links_have_label(self, populated_backend, tmp_path):
        path = tmp_path / "demo.json"
        data = export_to_demo_format(populated_backend, path)
        for link in data["links"]:
            assert "label" in link
            # العلاقات يجب أن تكون عربية
            assert len(link["label"]) > 0


class TestExportCytoscape:
    def test_cytoscape_format(self, populated_backend, tmp_path):
        path = tmp_path / "cyto.json"
        data = export_to_cytoscape(populated_backend, path)
        assert "nodes" in data
        assert "edges" in data
        # cytoscape format: {data: {...}}
        for n in data["nodes"]:
            assert "data" in n


class TestExportDot:
    def test_dot_format(self, populated_backend, tmp_path):
        path = tmp_path / "g.dot"
        content = export_to_dot(populated_backend, path)
        assert content.startswith("digraph")
        assert path.exists()
        # المحتوى يحوي العقد
        assert "Person:ahmad" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
