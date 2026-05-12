"""تحميل وإعداد بيانات Mozilla Common Voice العربية.

يستخدم HuggingFace Datasets لتحميل النسخة 17.0 من Common Voice (أحدث متاحة 2024).

التشغيل من جذر المشروع:
    python scripts/download_common_voice.py --max-clips 500
    python scripts/download_common_voice.py --max-clips 100 --split test  # للاختبار السريع

ملاحظة مهمة: تحميل Common Voice يحتاج:
1. حساب مجاني على HuggingFace.co
2. قبول شروط Common Voice (مرة واحدة عبر صفحة الـ dataset).
3. تسجيل دخول: huggingface-cli login

البيانات الناتجة في: data/raw/common_voice/
سجل البيانات في: data/raw/common_voice/manifest.json
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# إضافة جذر المشروع لمسار import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import soundfile as sf
from tqdm import tqdm

from src.ingestion.manifest import make_clip_record, save_manifest
from src.utils.arabic_text import clean_text, is_arabic
from src.utils.config import PROJECT_ROOT, load_config
from src.utils.logging import get_logger

log = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="تحميل بيانات Common Voice العربية",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--max-clips",
        type=int,
        default=None,
        help="حد أقصى لعدد المقاطع (افتراضياً من config.yaml)",
    )
    parser.add_argument(
        "--split",
        choices=["train", "validation", "test", "all"],
        default="all",
        help="أي تقسيم من Common Voice نحمّل",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="مجلد الإخراج (افتراضياً data/raw/common_voice)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="عرض ما سيتم دون تحميل فعلي",
    )
    return parser.parse_args()


def download_common_voice(
    max_clips: int,
    splits: list[str],
    output_dir: Path,
    min_duration: float,
    max_duration: float,
    dry_run: bool = False,
) -> list[dict]:
    """تحميل ومعالجة مقاطع Common Voice.

    Returns:
        قائمة بسجلات المقاطع المُحمَّلة.
    """
    try:
        from datasets import load_dataset
    except ImportError:
        log.error(
            "مكتبة datasets غير مثبتة. شغّل:\n  pip install datasets huggingface_hub"
        )
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)
    audio_dir = output_dir / "audio"
    audio_dir.mkdir(exist_ok=True)

    all_records: list[dict] = []
    counter = 0

    for split in splits:
        log.info(f"تحميل تقسيم: {split}")

        if dry_run:
            log.info(f"[DRY RUN] سيتم تحميل من mozilla-foundation/common_voice_17_0 / ar / {split}")
            continue

        try:
            ds = load_dataset(
                "mozilla-foundation/common_voice_17_0",
                "ar",
                split=split,
                streaming=True,  # streaming يوفر مساحة القرص
                trust_remote_code=True,
            )
        except Exception as e:
            log.error(
                f"فشل التحميل: {e}\n"
                "تأكد من:\n"
                "  1. تسجيل الدخول: huggingface-cli login\n"
                "  2. قبول شروط Common Voice على صفحة الـ dataset\n"
                "  3. اتصال إنترنت مستقر"
            )
            return all_records

        pbar = tqdm(ds, desc=f"معالجة {split}", unit="مقطع")
        for item in pbar:
            if counter >= max_clips:
                break

            transcript = item.get("sentence", "").strip()

            # فلترة جودة النص
            if not transcript or not is_arabic(transcript):
                continue
            if len(transcript) < 10:  # نصوص قصيرة جداً
                continue

            audio = item.get("audio")
            if audio is None:
                continue

            duration = len(audio["array"]) / audio["sampling_rate"]
            if duration < min_duration or duration > max_duration:
                continue

            # حفظ الملف الصوتي بصيغة WAV
            clip_id = f"cv_ar_{counter:05d}"
            audio_path = audio_dir / f"{clip_id}.wav"

            try:
                sf.write(
                    audio_path,
                    audio["array"],
                    audio["sampling_rate"],
                    subtype="PCM_16",
                )
            except Exception as e:
                log.warning(f"تعذّر حفظ {clip_id}: {e}")
                continue

            # بناء السجل
            record = make_clip_record(
                clip_id=clip_id,
                source="common_voice_17",
                audio_path=audio_path.relative_to(PROJECT_ROOT),
                transcript=clean_text(transcript),
                duration_sec=duration,
                speaker_id=item.get("client_id"),
                gender=item.get("gender") or "unknown",
                dialect=item.get("variant") or "msa",
                sample_rate=audio["sampling_rate"],
                license="CC0-1.0",
                extra={
                    "age": item.get("age"),
                    "accent": item.get("accent"),
                    "up_votes": item.get("up_votes"),
                    "down_votes": item.get("down_votes"),
                },
            )
            all_records.append(record)
            counter += 1
            pbar.set_postfix({"حُفظ": counter})

        pbar.close()
        if counter >= max_clips:
            log.info(f"وصلنا للحد الأقصى ({max_clips})")
            break

    return all_records


def main() -> int:
    args = parse_args()
    cfg = load_config()
    cv_cfg = cfg["data"]["sources"]["common_voice"]

    if not cv_cfg.get("enabled", True):
        log.warning("Common Voice معطّل في config.yaml")
        return 0

    max_clips = args.max_clips or cv_cfg.get("max_clips", 500)
    splits = cv_cfg["splits"] if args.split == "all" else [args.split]
    output_dir = args.output_dir or (PROJECT_ROOT / "data" / "raw" / "common_voice")

    log.info(f"بدء التحميل: max_clips={max_clips}, splits={splits}")
    log.info(f"مجلد الإخراج: {output_dir}")

    records = download_common_voice(
        max_clips=max_clips,
        splits=splits,
        output_dir=output_dir,
        min_duration=cv_cfg["min_duration_sec"],
        max_duration=cv_cfg["max_duration_sec"],
        dry_run=args.dry_run,
    )

    if not records:
        log.warning("لم يُحمَّل أي مقطع.")
        return 1

    manifest_path = output_dir / "manifest.json"
    save_manifest(records, manifest_path)
    log.info(f"اكتمل: {len(records)} مقطع")
    return 0


if __name__ == "__main__":
    sys.exit(main())
