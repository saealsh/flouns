"""بناء رسم المعرفة من مخرجات المرحلة 5.

أمثلة:
    # بناء من ملف NLP واحد
    python scripts/build_kg.py --input data/nlp/call_001.nlp.json

    # بناء من مجلد كامل
    python scripts/build_kg.py --input-dir data/nlp/

    # تصدير بصيغة الديمو لرفعها على graph.html
    python scripts/build_kg.py \\
        --input-dir data/nlp/ \\
        --output data/kg/ \\
        --export-demo

    # تشغيل استعلامات على الرسم الناتج
    python scripts/build_kg.py --input-dir data/nlp/ --query
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.kg.backends import NetworkXBackend
from src.kg.builder import KGBuilder
from src.kg.export import (
    export_to_cytoscape,
    export_to_demo_format,
    export_to_dot,
)
from src.kg.queries import KGQueries
from src.kg.schema import NodeType
from src.utils.config import PROJECT_ROOT
from src.utils.logging import get_logger

log = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="بناء رسم المعرفة — المرحلة 6")

    src_group = parser.add_mutually_exclusive_group(required=True)
    src_group.add_argument("--input", type=Path, help="ملف NLP واحد")
    src_group.add_argument("--input-dir", type=Path, help="مجلد ملفات NLP")

    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="مجلد المخرجات (افتراضياً data/kg)",
    )
    parser.add_argument(
        "--export-demo",
        action="store_true",
        help="تصدير بصيغة graph.html من الديمو",
    )
    parser.add_argument(
        "--export-cytoscape",
        action="store_true",
        help="تصدير بصيغة Cytoscape.js",
    )
    parser.add_argument(
        "--export-dot",
        action="store_true",
        help="تصدير بصيغة Graphviz DOT",
    )
    parser.add_argument(
        "--query",
        action="store_true",
        help="تشغيل استعلامات شائعة وطباعتها",
    )
    return parser.parse_args()


def print_queries(queries: KGQueries) -> None:
    """تشغيل استعلامات وطباعتها."""
    log.info("─" * 60)
    log.info("📊 ملخص الرسم")
    log.info("─" * 60)
    summary = queries.summary()
    log.info(f"  العقد: {summary['total_nodes']}")
    log.info(f"  العلاقات: {summary['total_edges']}")
    log.info(f"\n  العقد بالنوع:")
    for nt, c in summary["nodes_by_type"].items():
        log.info(f"    {nt}: {c}")
    log.info(f"\n  العلاقات بالنوع:")
    for et, c in summary["edges_by_type"].items():
        log.info(f"    {et}: {c}")

    log.info("\n" + "─" * 60)
    log.info("👥 أكثر الأشخاص ذِكراً")
    log.info("─" * 60)
    for r in queries.top_persons(limit=5):
        log.info(f"  {r.rank}. {r.node.label} (score={r.score:.0f})")

    log.info("\n" + "─" * 60)
    log.info("📍 أكثر الأماكن ذِكراً")
    log.info("─" * 60)
    for r in queries.top_locations(limit=5):
        log.info(f"  {r.rank}. {r.node.label} (score={r.score:.0f})")

    log.info("\n" + "─" * 60)
    log.info("🔑 مصطلحات watchlist المُكتشفة")
    log.info("─" * 60)
    matches = queries.calls_matching_watchlist()
    for m in matches:
        log.info(f"  • {m['keyword']} (في {m['call_id']})")
    if not matches:
        log.info("  لا تطابقات")

    log.info("\n" + "─" * 60)
    log.info("🤝 من اجتمع بمن")
    log.info("─" * 60)
    pairs = queries.who_met_whom()
    for p in pairs[:5]:
        log.info(f"  • {p['person_a']} ↔ {p['person_b']} ({p['count']} مرة)")
    if not pairs:
        log.info("  لا اجتماعات مكتشفة")

    log.info("\n" + "─" * 60)
    log.info("🌟 الأشخاص الأكثر مركزية")
    log.info("─" * 60)
    central = queries.central_persons(limit=5)
    for r in central:
        log.info(f"  {r.rank}. {r.node.label} (مركزية={r.score:.4f})")
    if not central:
        log.info("  لا توجد عقد ذات مركزية > 0")


def main() -> int:
    args = parse_args()

    output_dir = args.output or (PROJECT_ROOT / "data" / "kg")
    output_dir.mkdir(parents=True, exist_ok=True)

    # بناء
    backend = NetworkXBackend()
    builder = KGBuilder(backend)

    if args.input:
        if not args.input.exists():
            log.error(f"الملف غير موجود: {args.input}")
            return 1
        log.info(f"ابتلاع {args.input.name}...")
        result = builder.ingest_call_from_file(args.input)
        log.info(f"✅ {result}")
    else:
        if not args.input_dir.exists():
            log.error(f"المجلد غير موجود: {args.input_dir}")
            return 1
        log.info(f"ابتلاع كل ملفات NLP من {args.input_dir}")
        result = builder.ingest_directory(args.input_dir)
        log.info(f"✅ {result['n_files']} ملف، الإحصاءات: {result['total_stats']}")

    # حفظ الرسم الكامل
    graph_path = output_dir / "graph.json"
    backend.save(graph_path)

    # تصديرات
    if args.export_demo:
        export_to_demo_format(backend, output_dir / "graph_demo.json")
    if args.export_cytoscape:
        export_to_cytoscape(backend, output_dir / "graph_cytoscape.json")
    if args.export_dot:
        export_to_dot(backend, output_dir / "graph.dot")

    # استعلامات
    if args.query:
        queries = KGQueries(backend)
        print_queries(queries)

    log.info(f"\n📄 الرسم: {graph_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
