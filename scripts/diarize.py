"""تشغيل diarization على ملف صوتي أو مجلد.

أمثلة:
    # ملف واحد
    python scripts/diarize.py --input data/raw/test_samples/mixed_dialogue.wav

    # مع عدد متحدثين معروف
    python scripts/diarize.py --input call.wav --n-speakers 3

    # مع تحميل قاعدة بصمات موجودة
    python scripts/diarize.py --input call.wav --registry data/registry.json

    # مجلد كامل (يبني قاعدة بصمات تراكمياً)
    python scripts/diarize.py --input-dir data/raw/test_samples --output data/diarized
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.diarization.pipeline import diarize_file
from src.diarization.registry import VoiceprintRegistry
from src.utils.config import PROJECT_ROOT
from src.utils.logging import get_logger

log = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="فصل المتحدثين — المرحلة 3")

    src_group = parser.add_mutually_exclusive_group(required=True)
    src_group.add_argument("--input", type=Path, help="ملف صوتي واحد")
    src_group.add_argument("--input-dir", type=Path, help="مجلد بملفات صوتية")

    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="مجلد المخرجات (افتراضياً data/diarized)",
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=None,
        help="ملف قاعدة بصمات موجودة (JSON). إن لم يوجد يُنشأ.",
    )
    parser.add_argument(
        "--save-registry",
        type=Path,
        default=None,
        help="حفظ القاعدة بعد المعالجة (افتراضياً <output>/registry.json)",
    )
    parser.add_argument("--n-speakers", type=int, default=None, help="عدد المتحدثين إن كان معلوماً")
    parser.add_argument(
        "--method",
        choices=["agglomerative", "spectral"],
        default="agglomerative",
    )
    parser.add_argument(
        "--embedding",
        choices=["mfcc", "speechbrain"],
        default="mfcc",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.30,
        help="عتبة مسافة cosine للتجميع (للـ agglomerative)",
    )
    parser.add_argument(
        "--no-auto-register",
        action="store_true",
        help="لا تسجّل المتحدثين المجهولين تلقائياً",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    output_dir = args.output or (PROJECT_ROOT / "data" / "diarized")
    output_dir.mkdir(parents=True, exist_ok=True)

    # تحميل أو إنشاء قاعدة البصمات
    if args.registry and args.registry.exists():
        registry = VoiceprintRegistry.load(args.registry)
        log.info(f"حُمِّلت قاعدة بصمات بـ {len(registry)} متحدث")
    else:
        registry = VoiceprintRegistry()
        log.info("بدء بقاعدة بصمات فارغة")

    # تجميع الملفات
    files: list[Path] = []
    if args.input:
        if not args.input.exists():
            log.error(f"الملف غير موجود: {args.input}")
            return 1
        files = [args.input]
    else:
        if not args.input_dir.exists():
            log.error(f"المجلد غير موجود: {args.input_dir}")
            return 1
        for ext in (".wav", ".mp3", ".m4a", ".flac", ".ogg"):
            files.extend(args.input_dir.rglob(f"*{ext}"))
        if not files:
            log.warning(f"لا ملفات صوتية في {args.input_dir}")
            return 1

    log.info(f"معالجة {len(files)} ملف")
    all_results = []

    for f in files:
        clip_id = f.stem
        log.info(f"  ⏳ {f.name}")
        try:
            result = diarize_file(
                f,
                registry=registry,
                source_clip=clip_id,
                embedding_method=args.embedding,
                clustering_method=args.method,
                n_speakers=args.n_speakers,
                cluster_threshold=args.threshold,
                auto_register_unknown=not args.no_auto_register,
            )
            log.info(
                f"  ✅ {f.name}: {result.n_speakers_detected} متحدث، "
                f"{len(result.segments)} قطعة"
            )
            # حفظ نتيجة الملف
            result_path = output_dir / f"{clip_id}.diarization.json"
            with open(result_path, "w", encoding="utf-8") as fh:
                json.dump(result.to_dict(), fh, ensure_ascii=False, indent=2)
            all_results.append({"file": str(f), "result": result.to_dict()})
        except Exception as e:
            log.error(f"  ❌ {f.name}: {e}")
            all_results.append({"file": str(f), "error": str(e)})

    # حفظ القاعدة
    save_path = args.save_registry or (output_dir / "registry.json")
    registry.save(save_path)

    # ملخّص
    summary_path = output_dir / "diarization_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "n_files": len(files),
                "n_speakers_total": len(registry),
                "results": all_results,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    log.info("─" * 60)
    log.info(f"✅ اكتمل: {len(files)} ملف، {len(registry)} متحدث في القاعدة")
    log.info(f"📄 الملخّص: {summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
