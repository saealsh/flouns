"""اختبارات لـ src.kg.schema و src.kg.backends."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from src.kg.backends import NetworkXBackend
from src.kg.schema import Edge, EdgeType, Node, NodeType, make_node_id


class TestMakeNodeId:
    def test_simple_arabic(self):
        nid = make_node_id(NodeType.PERSON, "أحمد")
        assert nid == "Person:أحمد"

    def test_with_spaces(self):
        nid = make_node_id(NodeType.PERSON, "أحمد محمد")
        assert nid == "Person:أحمد_محمد"

    def test_strips_punctuation(self):
        nid = make_node_id(NodeType.PERSON, "أبو محمد!")
        assert "!" not in nid

    def test_different_types_different_ids(self):
        a = make_node_id(NodeType.PERSON, "أحمد")
        b = make_node_id(NodeType.LOCATION, "أحمد")
        assert a != b


class TestNetworkXBackend:
    def test_empty_backend(self):
        b = NetworkXBackend()
        assert b.node_count() == 0
        assert b.edge_count() == 0

    def test_add_node(self):
        b = NetworkXBackend()
        node = Node(id="p1", type=NodeType.PERSON, label="أحمد")
        b.add_node(node)
        assert b.node_count() == 1
        assert b.has_node("p1")

    def test_add_node_idempotent_merges_props(self):
        b = NetworkXBackend()
        n1 = Node(id="p1", type=NodeType.PERSON, label="أحمد",
                  properties={"mention_count": 1})
        n2 = Node(id="p1", type=NodeType.PERSON, label="أحمد",
                  properties={"mention_count": 2})
        b.add_node(n1)
        b.add_node(n2)
        assert b.node_count() == 1
        # mention_count يجب أن يتجمّع
        node = b.get_node("p1")
        assert node.properties["mention_count"] == 3

    def test_add_edge(self):
        b = NetworkXBackend()
        b.add_node(Node(id="p1", type=NodeType.PERSON, label="أ"))
        b.add_node(Node(id="p2", type=NodeType.PERSON, label="ب"))
        b.add_edge(Edge(source="p1", target="p2", type=EdgeType.MET_WITH))
        assert b.edge_count() == 1

    def test_add_edge_to_missing_node_warns(self):
        b = NetworkXBackend()
        b.add_node(Node(id="p1", type=NodeType.PERSON, label="أ"))
        b.add_edge(Edge(source="p1", target="p_missing", type=EdgeType.MET_WITH))
        # لا يضاف
        assert b.edge_count() == 0

    def test_duplicate_edge_increments_count(self):
        b = NetworkXBackend()
        b.add_node(Node(id="p1", type=NodeType.PERSON, label="أ"))
        b.add_node(Node(id="p2", type=NodeType.PERSON, label="ب"))
        e = Edge(source="p1", target="p2", type=EdgeType.MET_WITH,
                 properties={"call_id": "C1"})
        b.add_edge(e)
        b.add_edge(e)
        edges = b.get_edges(source="p1", target="p2", edge_type=EdgeType.MET_WITH)
        assert len(edges) == 1
        assert edges[0].properties["count"] == 2

    def test_get_edges_filters(self):
        b = NetworkXBackend()
        b.add_node(Node(id="p1", type=NodeType.PERSON, label="أ"))
        b.add_node(Node(id="p2", type=NodeType.PERSON, label="ب"))
        b.add_node(Node(id="p3", type=NodeType.PERSON, label="ج"))
        b.add_edge(Edge(source="p1", target="p2", type=EdgeType.MET_WITH))
        b.add_edge(Edge(source="p1", target="p3", type=EdgeType.AGREED_WITH))

        # كل العلاقات من p1
        all_p1 = b.get_edges(source="p1")
        assert len(all_p1) == 2

        # علاقات MET_WITH فقط
        met = b.get_edges(edge_type=EdgeType.MET_WITH)
        assert len(met) == 1

    def test_neighbors(self):
        b = NetworkXBackend()
        b.add_node(Node(id="p1", type=NodeType.PERSON, label="أ"))
        b.add_node(Node(id="p2", type=NodeType.PERSON, label="ب"))
        b.add_node(Node(id="p3", type=NodeType.PERSON, label="ج"))
        b.add_edge(Edge(source="p1", target="p2", type=EdgeType.MET_WITH))
        b.add_edge(Edge(source="p3", target="p1", type=EdgeType.CALLED))

        ns = b.neighbors("p1")
        ids = {n.id for n in ns}
        assert ids == {"p2", "p3"}

    def test_nodes_by_type(self):
        b = NetworkXBackend()
        b.add_node(Node(id="p1", type=NodeType.PERSON, label="أ"))
        b.add_node(Node(id="p2", type=NodeType.PERSON, label="ب"))
        b.add_node(Node(id="l1", type=NodeType.LOCATION, label="الرياض"))

        persons = b.nodes_by_type(NodeType.PERSON)
        assert len(persons) == 2
        locs = b.nodes_by_type(NodeType.LOCATION)
        assert len(locs) == 1

    def test_shortest_path(self):
        b = NetworkXBackend()
        for i in range(1, 5):
            b.add_node(Node(id=f"p{i}", type=NodeType.PERSON, label=f"P{i}"))
        b.add_edge(Edge(source="p1", target="p2", type=EdgeType.MET_WITH))
        b.add_edge(Edge(source="p2", target="p3", type=EdgeType.MET_WITH))
        b.add_edge(Edge(source="p3", target="p4", type=EdgeType.MET_WITH))

        path = b.shortest_path("p1", "p4")
        assert path == ["p1", "p2", "p3", "p4"]

    def test_no_path(self):
        b = NetworkXBackend()
        b.add_node(Node(id="p1", type=NodeType.PERSON, label="أ"))
        b.add_node(Node(id="p2", type=NodeType.PERSON, label="ب"))
        # لا علاقات
        path = b.shortest_path("p1", "p2")
        assert path is None

    def test_save_and_load(self, tmp_path):
        b = NetworkXBackend()
        b.add_node(Node(id="p1", type=NodeType.PERSON, label="أحمد",
                        properties={"mention_count": 3}))
        b.add_node(Node(id="l1", type=NodeType.LOCATION, label="الرياض"))
        b.add_edge(Edge(source="p1", target="l1", type=EdgeType.MET_AT,
                        properties={"call_id": "C1"}))

        path = tmp_path / "g.json"
        b.save(path)

        b2 = NetworkXBackend.load(path)
        assert b2.node_count() == 2
        assert b2.edge_count() == 1
        n = b2.get_node("p1")
        assert n is not None
        assert n.label == "أحمد"
        assert n.properties["mention_count"] == 3

    def test_clear(self):
        b = NetworkXBackend()
        b.add_node(Node(id="p1", type=NodeType.PERSON, label="أ"))
        b.clear()
        assert b.node_count() == 0


class TestCentrality:
    def test_degree_centrality(self):
        b = NetworkXBackend()
        # عقدة مركزية تربط 3 عقد
        b.add_node(Node(id="hub", type=NodeType.PERSON, label="hub"))
        for i in range(1, 4):
            b.add_node(Node(id=f"p{i}", type=NodeType.PERSON, label=f"p{i}"))
            b.add_edge(Edge(source="hub", target=f"p{i}", type=EdgeType.MET_WITH))

        dc = b.degree_centrality()
        # hub أعلى مركزية
        assert dc["hub"] > dc["p1"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
