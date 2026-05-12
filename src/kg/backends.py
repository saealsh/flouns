"""Backends لرسم المعرفة.

نوفّر طبقتين بنفس الواجهة:

1. **NetworkXBackend** (افتراضي، مدمج):
   - رسم بياني في الذاكرة، لا يحتاج خادم.
   - مثالي للاختبار والتطوير.
   - يدعم save/load بصيغة JSON.

2. **Neo4jBackend** (اختياري):
   - يحتاج خادم Neo4j (Docker أو محلي).
   - يدعم Cypher queries، استعلامات معقدة، تخزين دائم.

الواجهة:
    - add_node(node)
    - add_edge(edge)
    - get_node(id) -> Node | None
    - get_edges(source=None, target=None, type=None) -> list[Edge]
    - neighbors(node_id) -> list[Node]
    - shortest_path(source_id, target_id) -> list[str]
    - clear()
    - to_dict() -> dict (للتصدير)
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator, Protocol

from src.kg.schema import Edge, EdgeType, Node, NodeType
from src.utils.logging import get_logger

log = get_logger(__name__)


class KGBackend(Protocol):
    """واجهة موحّدة لكل backend."""

    def add_node(self, node: Node) -> None: ...
    def add_edge(self, edge: Edge) -> None: ...
    def get_node(self, node_id: str) -> Node | None: ...
    def has_node(self, node_id: str) -> bool: ...
    def get_edges(
        self,
        *,
        source: str | None = None,
        target: str | None = None,
        edge_type: EdgeType | None = None,
    ) -> list[Edge]: ...
    def neighbors(self, node_id: str) -> list[Node]: ...
    def nodes_by_type(self, node_type: NodeType) -> list[Node]: ...
    def all_nodes(self) -> Iterator[Node]: ...
    def all_edges(self) -> Iterator[Edge]: ...
    def node_count(self) -> int: ...
    def edge_count(self) -> int: ...
    def clear(self) -> None: ...


class NetworkXBackend:
    """رسم بياني موجّه في الذاكرة باستخدام NetworkX."""

    def __init__(self):
        try:
            import networkx as nx
        except ImportError as e:
            raise ImportError("NetworkXBackend يحتاج: pip install networkx") from e

        self._nx = nx
        self.graph = nx.MultiDiGraph()  # multi-edge موجَّه (نسمح بعلاقات متعددة بين نفس العقدتين)
        self._nodes: dict[str, Node] = {}

    def add_node(self, node: Node) -> None:
        """إضافة عقدة (أو تحديثها إن وُجدت).

        عند التحديث: نُدمج الـ properties (الجديدة تفوز).
        """
        if node.id in self._nodes:
            # دمج: نحدّث الـ properties
            existing = self._nodes[node.id]
            # نزيد عداد الذكر إن كان موجوداً (قبل دمج dict)
            old_count = existing.properties.get("mention_count", 0)
            new_count = node.properties.get("mention_count", 0)
            merged_props = {**existing.properties, **node.properties}
            if "mention_count" in existing.properties or "mention_count" in node.properties:
                merged_props["mention_count"] = old_count + new_count
            existing.properties = merged_props
            self.graph.nodes[node.id].update({"properties": merged_props, "label": node.label})
        else:
            self._nodes[node.id] = node
            self.graph.add_node(
                node.id,
                type=node.type.value,
                label=node.label,
                properties=node.properties,
            )

    def add_edge(self, edge: Edge) -> None:
        """إضافة علاقة. نسمح بعلاقات متعددة بين نفس العقدتين (multigraph)."""
        # نتحقق أن العقدتين موجودتان
        if edge.source not in self._nodes:
            log.warning(f"عقدة مصدر غير موجودة: {edge.source}")
            return
        if edge.target not in self._nodes:
            log.warning(f"عقدة هدف غير موجودة: {edge.target}")
            return

        # نبحث عن علاقة مماثلة (نفس النوع، نفس المصدر والهدف)
        # إن وُجدت، نزيد weight بدل إضافة edge جديد
        for _, _, key, data in self.graph.edges(edge.source, keys=True, data=True):
            if (
                data.get("type") == edge.type.value
                and self.graph.has_edge(edge.source, edge.target, key=key)
            ):
                # نزيد العداد
                data["properties"]["count"] = data["properties"].get("count", 1) + 1
                # إضافة call_id إلى قائمة المصادر إن وُجد
                new_call = edge.properties.get("call_id")
                if new_call:
                    sources = data["properties"].setdefault("call_ids", [])
                    if new_call not in sources:
                        sources.append(new_call)
                return

        # إضافة edge جديد
        props = {**edge.properties, "count": 1}
        if "call_id" in edge.properties:
            props["call_ids"] = [edge.properties["call_id"]]
        self.graph.add_edge(
            edge.source,
            edge.target,
            type=edge.type.value,
            properties=props,
        )

    def get_node(self, node_id: str) -> Node | None:
        return self._nodes.get(node_id)

    def has_node(self, node_id: str) -> bool:
        return node_id in self._nodes

    def get_edges(
        self,
        *,
        source: str | None = None,
        target: str | None = None,
        edge_type: EdgeType | None = None,
    ) -> list[Edge]:
        """قراءة العلاقات بمرشّحات اختيارية."""
        results = []
        for u, v, data in self.graph.edges(data=True):
            if source and u != source:
                continue
            if target and v != target:
                continue
            if edge_type and data.get("type") != edge_type.value:
                continue
            results.append(
                Edge(
                    source=u,
                    target=v,
                    type=EdgeType(data["type"]),
                    properties=data.get("properties", {}),
                )
            )
        return results

    def neighbors(self, node_id: str) -> list[Node]:
        """جيران عقدة (المُشار إليهم + المشيرون إليها)."""
        if not self.has_node(node_id):
            return []
        neighbor_ids = set(self.graph.successors(node_id)) | set(self.graph.predecessors(node_id))
        return [self._nodes[nid] for nid in neighbor_ids if nid in self._nodes]

    def nodes_by_type(self, node_type: NodeType) -> list[Node]:
        return [n for n in self._nodes.values() if n.type == node_type]

    def all_nodes(self) -> Iterator[Node]:
        return iter(self._nodes.values())

    def all_edges(self) -> Iterator[Edge]:
        for u, v, data in self.graph.edges(data=True):
            yield Edge(
                source=u,
                target=v,
                type=EdgeType(data["type"]),
                properties=data.get("properties", {}),
            )

    def node_count(self) -> int:
        return len(self._nodes)

    def edge_count(self) -> int:
        return self.graph.number_of_edges()

    def clear(self) -> None:
        self.graph.clear()
        self._nodes.clear()

    def shortest_path(self, source_id: str, target_id: str) -> list[str] | None:
        """أقصر مسار بين عقدتين (يتجاهل الاتجاه)."""
        if not self.has_node(source_id) or not self.has_node(target_id):
            return None

        # نحوّل لـ undirected للبحث
        undirected = self.graph.to_undirected()
        try:
            return self._nx.shortest_path(undirected, source_id, target_id)
        except self._nx.NetworkXNoPath:
            return None

    def degree_centrality(self) -> dict[str, float]:
        """مركزية الدرجة لكل عقدة (مدى أهميتها في الرسم)."""
        return self._nx.degree_centrality(self.graph)

    def betweenness_centrality(self) -> dict[str, float]:
        """مركزية التوسط (عقد تربط بين مجموعات)."""
        return self._nx.betweenness_centrality(self.graph)

    def connected_components(self) -> list[set[str]]:
        """مكونات متصلة (مجموعات منفصلة من العقد)."""
        undirected = self.graph.to_undirected()
        return [set(c) for c in self._nx.connected_components(undirected)]

    def save(self, path: Path | str) -> None:
        """حفظ الرسم لـ JSON."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "nodes": [n.to_dict() for n in self.all_nodes()],
            "edges": [e.to_dict() for e in self.all_edges()],
            "metadata": {
                "node_count": self.node_count(),
                "edge_count": self.edge_count(),
            },
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        log.info(f"حُفظ الرسم: {self.node_count()} عقدة، {self.edge_count()} علاقة → {path}")

    @classmethod
    def load(cls, path: Path | str) -> "NetworkXBackend":
        """تحميل رسم من JSON."""
        path = Path(path)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        backend = cls()
        for node_data in data.get("nodes", []):
            backend.add_node(
                Node(
                    id=node_data["id"],
                    type=NodeType(node_data["type"]),
                    label=node_data["label"],
                    properties=node_data.get("properties", {}),
                )
            )
        for edge_data in data.get("edges", []):
            backend.add_edge(
                Edge(
                    source=edge_data["source"],
                    target=edge_data["target"],
                    type=EdgeType(edge_data["type"]),
                    properties=edge_data.get("properties", {}),
                )
            )
        log.info(f"حُمِّل الرسم: {backend.node_count()} عقدة، {backend.edge_count()} علاقة")
        return backend


class Neo4jBackend:
    """Backend لـ Neo4j (Cypher queries).

    التشغيل (يحتاج Docker):
        docker run -d \\
            --name neo4j \\
            -p 7474:7474 -p 7687:7687 \\
            -e NEO4J_AUTH=neo4j/password \\
            neo4j:5

    تركيب التبعية:
        pip install neo4j
    """

    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        user: str = "neo4j",
        password: str = "password",
    ):
        try:
            from neo4j import GraphDatabase
        except ImportError as e:
            raise ImportError(
                "Neo4jBackend يحتاج: pip install neo4j\n"
                "وتشغيل خادم Neo4j (انظر docker command في docstring)"
            ) from e

        self._GraphDatabase = GraphDatabase
        self.uri = uri
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        log.info(f"اتصال Neo4j: {uri}")

    def close(self) -> None:
        if self.driver:
            self.driver.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def add_node(self, node: Node) -> None:
        with self.driver.session() as session:
            session.run(
                f"""
                MERGE (n:{node.type.value} {{id: $id}})
                SET n.label = $label, n += $properties
                """,
                id=node.id, label=node.label, properties=node.properties,
            )

    def add_edge(self, edge: Edge) -> None:
        with self.driver.session() as session:
            session.run(
                f"""
                MATCH (s {{id: $source}}), (t {{id: $target}})
                MERGE (s)-[r:{edge.type.value}]->(t)
                ON CREATE SET r += $properties, r.count = 1
                ON MATCH SET r.count = coalesce(r.count, 0) + 1
                """,
                source=edge.source, target=edge.target, properties=edge.properties,
            )

    def get_node(self, node_id: str) -> Node | None:
        with self.driver.session() as session:
            result = session.run(
                "MATCH (n {id: $id}) RETURN n LIMIT 1",
                id=node_id,
            )
            record = result.single()
            if not record:
                return None
            n = record["n"]
            return Node(
                id=n["id"],
                type=NodeType(list(n.labels)[0]),
                label=n.get("label", n["id"]),
                properties=dict(n),
            )

    def clear(self) -> None:
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

    def cypher(self, query: str, **params) -> list[dict]:
        """تشغيل Cypher مباشر — مفيد للاستعلامات المعقدة."""
        with self.driver.session() as session:
            result = session.run(query, **params)
            return [dict(record) for record in result]


# Factory
def create_backend(name: str = "networkx", **kwargs) -> KGBackend:
    """إنشاء backend حسب الاسم."""
    if name == "networkx":
        return NetworkXBackend()
    elif name == "neo4j":
        return Neo4jBackend(**kwargs)
    else:
        raise ValueError(f"backend غير معروف: {name}")
