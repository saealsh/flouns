"""تفريغ ملفات صوتية كاملة عبر خط أنابيب المرحلة 4.

أمثلة:
    # ملف واحد (يحتاج faster-whisper مثبت)
    python scripts/transcribe.py --input call.wav --output data/transcripts

    # اختبار بـ mock بدون تنزيل نماذج
    python scripts/transcribe.py --input call.wav --output data/transcripts --backend mock

    # مع تحديد المتحدثين وتمرير prompt للمصطلحات الخاصة
    python scripts/transcribe.py \\
      --input call.wav \\
      --n-speakers 2 \\
      --initial-prompt "أحمد، خالد، الشحنة، المستودع"

    # مجلد كامل مع قاعدة بصمات تراكمية
    python scripts/transcribe.py \\
      --input-dir data/processed \\
      --output data/transcripts \\
      --registry data/diarized/registry.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.asr.pipeline import transcribe_file
from src.diarization.registry import VoiceprintRegistry
from src.utils.config import PROJECT_ROOT
from src.utils.logging import get_logger

log = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="تفريغ تلقائي + فصل المتحدثين — المرحلة 4",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    src_group = parser.add_mutually_exclusive_group(required=True)
    src_group.add_argument("--input", type=Path, help="ملف صوتي واحد")
    src_group.add_argument("--input-dir", type=Path, help="مجلد بملفات صوتية")

    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="مجلد الإخراج (افتراضياً data/transcripts)",
    )
    parser.add_argument(
        "--formats",
        nargs="+",
        choices=["json", "txt", "srt", "vtt", "csv", "demo"],
        default=["json", "txt", "srt", "demo"],
        help="صيغ التصدير",
    )

    # ASR options
    asr_group = parser.add_argument_group("التفريغ (ASR)")
    asr_group.add_argument(
        "--backend",
        choices=["mock", "faster-whisper"],
        default="faster-whisper",
        help="backend الـ ASR",
    )
    asr_group.add_argument(
        "--model",
        default="large-v3",
        help="حجم النموذج (tiny|base|small|medium|large-v3)",
    )
    asr_group.add_argument(
        "--device",
        default="auto",
        choices=["auto", "cuda", "cpu"],
        help="جهاز التنفيذ",
    )
    asr_group.add_argument(
        "--compute-type",
        default="default",
        help="نوع الحساب (default|int8|float16|float32)",
    )
    asr_group.add_argument(
        "--language",
        default="ar",
        help="لغة الصوت (ar للعربية)",
    )
    asr_group.add_argument(
        "--initial-prompt",
        default=None,
        help="prompt اختياري لتوجيه النموذج",
    )

    # Diarization options
    diar_group = parser.add_argument_group("فصل المتحدثين")
    diar_group.add_argument(
        "--n-speakers",
        type=int,
        default=None,
        help="عدد المتحدثين إن كان معلوماً",
    )
    diar_group.add_argument(
        "--registry",
        type=Path,
        default=None,
        help="قاعدة بصمات موجودة",
    )
    diar_group.add_argument(
        "--save-registry",
        type=Path,
        default=None,
        help="حفظ القاعدة بعد المعالجة",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    output_dir = args.output or (PROJECT_ROOT / "data" / "transcripts")
    output_dir.mkdir(parents=True, exist_ok=True)

    # قاعدة البصمات
    if args.registry and args.registry.exists():
        registry = VoiceprintRegistry.load(args.registry)
        log.info(f"حُمِّلت قاعدة بصمات بـ {len(registry)} متحدث")
    else:
        registry = VoiceprintRegistry()

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

    asr_kwargs = {}
    if args.backend == "faster-whisper":
        asr_kwargs = {
            "model_size": args.model,
            "device": args.device,
            "compute_type": args.compute_type,
        }

    summary = []
    for f in files:
        try:
            result = transcribe_file(
                f,
                output_dir=output_dir,
                export_formats=args.formats,
                asr_backend=args.backend,
                asr_kwargs=asr_kwargs,
                registry=registry,
                n_speakers=args.n_speakers,
                language=args.language,
                initial_prompt=args.initial_prompt,
            )
            t = result.aligned_transcript
            log.info(
                f"  ✅ {f.name}: {len(t.segments)} سطر، "
                f"{len(t.speakers)} متحدث، ثقة {t.avg_confidence:.0%}"
            )
            summary.append({
                "file": str(f),
                "call_id": t.call_id,
                "n_segments": len(t.segments),
                "n_speakers": len(t.speakers),
                "avg_confidence": round(t.avg_confidence, 4),
                "duration_sec": round(t.duration_sec, 2),
                "exported": list(result.exported_files.keys()),
            })
        except Exception as e:
            log.error(f"  ❌ {f.name}: {e}")
            summary.append({"file": str(f), "error": str(e)})

    # حفظ القاعدة
    save_path = args.save_registry or (output_dir / "registry.json")
    registry.save(save_path)

    # ملخّص
    summary_path = output_dir / "transcription_summary.json"
    with open(summary_path, "w", encoding="utf-8") as fp:
        json.dump(
            {
                "n_files": len(files),
                "n_speakers_total": len(registry),
                "results": summary,
            },
            fp,
            ensure_ascii=False,
            indent=2,
        )

    log.info("─" * 60)
    log.info(f"✅ اكتمل: {len(files)} ملف، {len(registry)} متحدث في القاعدة")
    log.info(f"📄 الملخّص: {summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
