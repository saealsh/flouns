"""تصدير رسم المعرفة بصيغ متعددة.

الصيغ المدعومة:
- **demo**: صيغة `graph.html` من الديمو (nodes + links مع type/label)
- **cytoscape**: cytoscape.js (شائع للويب)
- **graphml**: GraphML XML (لـ Gephi)
- **dot**: Graphviz DOT (للرسم الثابت)

استخدام:
    from src.kg.export import export_to_demo_format, export_to_graphml

    export_to_demo_format(backend, "data/kg/graph_demo.json")
"""
from __future__ import annotations

import json
from pathlib import Path

from src.kg.backends import KGBackend, NetworkXBackend
from src.kg.schema import EdgeType, NodeType
from src.utils.logging import get_logger

log = get_logger(__name__)


# ربط أنواع العقد بألوان (تطابق ألوان الديمو)
NODE_COLORS = {
    NodeType.CALL: "#3b82f6",          # أزرق
    NodeType.SPEAKER: "#8b5cf6",       # بنفسجي
    NodeType.PERSON: "#10b981",        # أخضر
    NodeType.LOCATION: "#f59e0b",      # برتقالي
    NodeType.ORGANIZATION: "#ec4899",  # وردي
    NodeType.DATE: "#06b6d4",          # تركواز
    NodeType.TIME: "#06b6d4",
    NodeType.MONEY: "#84cc16",         # ليموني
    NodeType.KEYWORD: "#ef4444",       # أحمر
    NodeType.EVENT: "#6366f1",         # نيلي
    NodeType.PHONE: "#94a3b8",
    NodeType.EMAIL: "#94a3b8",
}


def export_to_demo_format(backend: KGBackend, path: Path | str) -> dict:
    """تصدير لصيغة `graph.html` في الديمو.

    البنية المتوقعة من الديمو:
        {
          "nodes": [
            {"id": ..., "label": ..., "type": ..., "color": ...},
            ...
          ],
          "links": [
            {"source": ..., "target": ..., "type": ..., "weight": ...},
            ...
          ]
        }

    Returns:
        البيانات المُصدَّرة كقاموس.
    """
    nodes = []
    for node in backend.all_nodes():
        nodes.append({
            "id": node.id,
            "label": node.label,
            "type": node.type.value,
            "color": NODE_COLORS.get(node.type, "#6b7280"),
            "size": _node_size(node),
            "properties": node.properties,
        })

    links = []
    for edge in backend.all_edges():
        links.append({
            "source": edge.source,
            "target": edge.target,
            "type": edge.type.value,
            "label": _edge_label(edge.type),
            "weight": edge.properties.get("count", 1),
            "properties": edge.properties,
        })

    data = {
        "nodes": nodes,
        "links": links,
        "metadata": {
            "format": "demo",
            "version": "1.0",
            "node_count": len(nodes),
            "link_count": len(links),
        },
    }

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    log.info(f"تم التصدير بصيغة demo: {len(nodes)} عقدة، {len(links)} رابط → {path}")
    return data


def _node_size(node) -> int:
    """حجم العقدة في الرسم (متناسب مع mention_count)."""
    count = node.properties.get("mention_count", 1)
    return min(10 + count * 2, 40)


def _edge_label(edge_type: EdgeType) -> str:
    """تسمية بشرية للعلاقة."""
    labels = {
        EdgeType.PARTICIPATED_IN: "شارك في",
        EdgeType.MENTIONED_IN: "ذُكر في",
        EdgeType.MENTIONED: "ذكر",
        EdgeType.IDENTIFIED_AS: "هو",
        EdgeType.HAS_ACTOR: "يشارك فيه",
        EdgeType.OCCURRED_AT: "في",
        EdgeType.OCCURRED_ON: "بتاريخ",
        EdgeType.MET_WITH: "اجتمع بـ",
        EdgeType.MET_AT: "اجتمع في",
        EdgeType.AGREED_WITH: "اتفق مع",
        EdgeType.CALLED: "اتصل بـ",
        EdgeType.SENT_TO: "أرسل إلى",
        EdgeType.RECEIVED_FROM: "استلم من",
        EdgeType.WENT_TO: "ذهب إلى",
        EdgeType.ARRIVED_AT: "وصل إلى",
        EdgeType.MATCHES_WATCHLIST: "يحوي مصطلح",
        EdgeType.SAME_AS: "هو نفسه",
        EdgeType.INVOLVED_KEYWORD: "يتضمن",
    }
    return labels.get(edge_type, edge_type.value)


def export_to_cytoscape(backend: KGBackend, path: Path | str) -> dict:
    """تصدير لصيغة Cytoscape.js."""
    elements = {"nodes": [], "edges": []}

    for node in backend.all_nodes():
        elements["nodes"].append({
            "data": {
                "id": node.id,
                "label": node.label,
                "type": node.type.value,
                **node.properties,
            },
        })

    for i, edge in enumerate(backend.all_edges()):
        elements["edges"].append({
            "data": {
                "id": f"e{i}",
                "source": edge.source,
                "target": edge.target,
                "type": edge.type.value,
                **edge.properties,
            },
        })

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(elements, f, ensure_ascii=False, indent=2)
    log.info(f"تم التصدير بصيغة Cytoscape → {path}")
    return elements


def export_to_graphml(backend: KGBackend, path: Path | str) -> None:
    """تصدير لـ GraphML (لـ Gephi)."""
    if not isinstance(backend, NetworkXBackend):
        raise NotImplementedError("GraphML يحتاج NetworkXBackend حالياً")

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    import networkx as nx
    nx.write_graphml(backend.graph, str(path))
    log.info(f"تم التصدير بصيغة GraphML → {path}")


def export_to_dot(backend: KGBackend, path: Path | str) -> str:
    """تصدير لصيغة Graphviz DOT."""
    lines = ["digraph KG {", "  rankdir=LR;", "  node [shape=box, style=filled];"]

    for node in backend.all_nodes():
        color = NODE_COLORS.get(node.type, "#6b7280")
        # escape quotes في الـ label
        safe_label = node.label.replace('"', '\\"')
        lines.append(
            f'  "{node.id}" [label="{safe_label}", fillcolor="{color}", fontcolor=white];'
        )

    for edge in backend.all_edges():
        label = _edge_label(edge.type)
        weight = edge.properties.get("count", 1)
        lines.append(
            f'  "{edge.source}" -> "{edge.target}" [label="{label}", weight={weight}];'
        )

    lines.append("}")
    content = "\n".join(lines)

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    log.info(f"تم التصدير بصيغة DOT → {path}")
    return content
