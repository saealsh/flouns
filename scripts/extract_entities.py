"""تحليل NLP لـ transcript أو نص خام.

أمثلة:
    # تحليل نص خام مباشرة
    python scripts/extract_entities.py --text "اجتمع أحمد بسعيد في الرياض الخميس"

    # تحليل ملف transcript من المرحلة 4
    python scripts/extract_entities.py --input transcripts/call_001.json

    # مجلد كامل
    python scripts/extract_entities.py --input-dir data/transcripts/ --output data/nlp/

    # مع قائمة مصطلحات يتعقّبها المحلّل
    python scripts/extract_entities.py --input call.json --watchlist data/watchlist.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.nlp.keywords import Watchlist
from src.nlp.pipeline import NLPPipeline, analyze_transcript
from src.utils.config import PROJECT_ROOT
from src.utils.logging import get_logger

log = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="تحليل NLP — المرحلة 5",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    src_group = parser.add_mutually_exclusive_group(required=True)
    src_group.add_argument("--text", type=str, help="نص خام مباشرة")
    src_group.add_argument("--input", type=Path, help="ملف transcript واحد (JSON)")
    src_group.add_argument("--input-dir", type=Path, help="مجلد ملفات transcripts")

    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="مجلد المخرجات (افتراضياً data/nlp)",
    )
    parser.add_argument(
        "--watchlist",
        type=Path,
        default=None,
        help="ملف قائمة المصطلحات (JSON)",
    )
    parser.add_argument(
        "--top-keywords",
        type=int,
        default=20,
        help="عدد الكلمات المفتاحية المرجَعة",
    )
    parser.add_argument(
        "--use-spacy",
        action="store_true",
        help="استخدام spaCy إن مثبَّت",
    )
    return parser.parse_args()


def print_summary(result_dict: dict, log_) -> None:
    """طباعة ملخص النتيجة."""
    if "nlp" in result_dict:
        # نتيجة transcript
        meta = result_dict["nlp"].get("full_text_analysis", {}).get("metadata", {})
    else:
        meta = result_dict.get("metadata", {})

    log_.info("─" * 60)
    log_.info("📊 ملخص التحليل")
    log_.info("─" * 60)
    log_.info(f"  كيانات: {meta.get('n_entities', 0)}")
    log_.info(f"  كيانات فريدة: {meta.get('n_unique_entities', 0)}")
    log_.info(f"  كلمات مفتاحية: {meta.get('n_keywords', 0)}")
    log_.info(f"  تطابقات watchlist: {meta.get('n_watchlist_matches', 0)}")
    log_.info(f"  أحداث: {meta.get('n_events', 0)}")
    log_.info(f"  KG triples: {meta.get('n_kg_triples', 0)}")


def process_text(text: str, watchlist: Watchlist | None, args) -> dict:
    """تحليل نص خام."""
    pipeline = NLPPipeline(
        watchlist=watchlist,
        use_spacy=args.use_spacy,
        top_keywords=args.top_keywords,
    )
    result = pipeline.analyze(text)
    return result.to_dict()


def process_file(path: Path, watchlist: Watchlist | None) -> dict:
    """تحليل ملف transcript."""
    return analyze_transcript(path, watchlist=watchlist)


def main() -> int:
    args = parse_args()

    output_dir = args.output or (PROJECT_ROOT / "data" / "nlp")
    output_dir.mkdir(parents=True, exist_ok=True)

    # تحميل watchlist إن وُجد
    watchlist = None
    if args.watchlist:
        if not args.watchlist.exists():
            log.error(f"watchlist غير موجود: {args.watchlist}")
            return 1
        watchlist = Watchlist.load(args.watchlist)
        log.info(f"حُمِّلت قائمة مصطلحات بـ {len(watchlist)} مصطلحاً")

    # تشغيل حسب نوع المدخل
    if args.text:
        log.info("تحليل نص خام...")
        result = process_text(args.text, watchlist, args)
        out_path = output_dir / "text_analysis.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        log.info(f"📄 النتيجة: {out_path}")
        print_summary(result, log)

        # طباعة بعض الكيانات للمستخدم
        log.info("\n🔍 الكيانات المستخرجة:")
        for e in result["entities"][:10]:
            log.info(
                f"  • [{e['type']}] {e['text']} "
                f"(thread={e['confidence']:.2f})"
            )
        if len(result["entities"]) > 10:
            log.info(f"  ... و{len(result['entities']) - 10} أخرى")

        return 0

    elif args.input:
        if not args.input.exists():
            log.error(f"الملف غير موجود: {args.input}")
            return 1
        log.info(f"تحليل {args.input.name}...")
        result = process_file(args.input, watchlist)
        out_path = output_dir / f"{args.input.stem}.nlp.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        log.info(f"📄 النتيجة: {out_path}")
        print_summary(result, log)
        return 0

    else:
        if not args.input_dir.exists():
            log.error(f"المجلد غير موجود: {args.input_dir}")
            return 1
        files = sorted(args.input_dir.glob("*.json"))
        if not files:
            log.warning(f"لا ملفات JSON في {args.input_dir}")
            return 1

        log.info(f"معالجة {len(files)} ملف")
        all_results = []
        for f in files:
            try:
                log.info(f"  ⏳ {f.name}")
                result = process_file(f, watchlist)
                out_path = output_dir / f"{f.stem}.nlp.json"
                with open(out_path, "w", encoding="utf-8") as fh:
                    json.dump(result, fh, ensure_ascii=False, indent=2)
                all_results.append({"file": f.name, "output": str(out_path)})
                meta = result.get("nlp", {}).get("full_text_analysis", {}).get("metadata", {})
                log.info(
                    f"  ✅ {f.name}: {meta.get('n_entities', 0)} كيان، "
                    f"{meta.get('n_events', 0)} حدث"
                )
            except Exception as e:
                log.error(f"  ❌ {f.name}: {e}")
                all_results.append({"file": f.name, "error": str(e)})

        # ملخص شامل
        summary_path = output_dir / "nlp_summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(
                {"n_files": len(files), "results": all_results},
                f,
                ensure_ascii=False,
                indent=2,
            )
        log.info(f"\n✅ اكتمل: {len(files)} ملف")
        log.info(f"📄 الملخّص: {summary_path}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
