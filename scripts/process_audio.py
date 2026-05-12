"""معالجة كل الملفات الصوتية في مجلد عبر خط أنابيب المرحلة 2.

التشغيل:
    python scripts/process_audio.py
    python scripts/process_audio.py --input data/raw/common_voice/audio --output data/processed
    python scripts/process_audio.py --vad silero
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.audio.pipeline import process_directory
from src.utils.config import PROJECT_ROOT, load_config
from src.utils.logging import get_logger

log = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="معالجة الصوت — المرحلة 2")
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="مجلد المدخلات (افتراضياً data/raw)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="مجلد المخرجات (افتراضياً data/processed)",
    )
    parser.add_argument(
        "--vad",
        choices=["energy", "silero"],
        default="energy",
        help="طريقة VAD",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="مسار حفظ تقرير JSON (افتراضياً <output>/processing_report.json)",
    )
    return parser.parse_args()


def print_summary(reports: list, log_) -> None:
    """طباعة ملخص إحصائي."""
    if not reports:
        log_.warning("لا تقارير لعرضها")
        return

    statuses = Counter(r.status for r in reports)
    total_dur = sum(r.duration_sec for r in reports)
    total_speech = sum(r.vad.get("total_speech_sec", 0) for r in reports)

    log_.info("─" * 60)
    log_.info("📊 ملخص المعالجة")
    log_.info("─" * 60)
    log_.info(f"الملفات الكلية: {len(reports)}")
    for status, count in statuses.most_common():
        emoji = {"ok": "✅", "warning": "⚠️", "failed": "❌"}.get(status, "•")
        log_.info(f"  {emoji} {status}: {count}")
    log_.info(f"المدة الكلية: {total_dur / 60:.2f} دقيقة")
    log_.info(f"مدة الكلام (بعد VAD): {total_speech / 60:.2f} دقيقة")
    if total_dur > 0:
        log_.info(f"نسبة الكلام/الكلي: {total_speech / total_dur:.0%}")

    # أكثر التحذيرات شيوعاً
    all_warnings: Counter[str] = Counter()
    for r in reports:
        for w in r.warnings:
            # نأخذ الجزء الأول من التحذير (قبل الأقواس) للتجميع
            key = w.split("(")[0].strip()
            all_warnings[key] += 1

    if all_warnings:
        log_.info("التحذيرات الأكثر شيوعاً:")
        for w, count in all_warnings.most_common(5):
            log_.info(f"  • {w}: {count}")


def main() -> int:
    args = parse_args()
    cfg = load_config()
    audio_cfg = cfg.get("audio", {})

    input_dir = args.input or (PROJECT_ROOT / "data" / "raw")
    output_dir = args.output or (PROJECT_ROOT / "data" / "processed")

    if not input_dir.exists():
        log.error(f"مجلد المدخلات غير موجود: {input_dir}")
        return 1

    log.info(f"معالجة من {input_dir} → {output_dir}")
    log.info(f"طريقة VAD: {args.vad}")

    thresholds = audio_cfg.get("quality_thresholds", {})

    reports = process_directory(
        input_dir,
        output_dir,
        vad_method=args.vad,
        quality_thresholds=thresholds,
    )

    if not reports:
        log.warning("لم تُعالَج أي ملفات")
        return 1

    # حفظ تقرير JSON
    report_path = args.report or (output_dir / "processing_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(
            [r.to_dict() for r in reports],
            f,
            ensure_ascii=False,
            indent=2,
        )
    log.info(f"📄 تقرير محفوظ: {report_path}")

    print_summary(reports, log)

    failed = sum(1 for r in reports if r.status == "failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
