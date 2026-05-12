"""التحقق من اكتمال وجودة وتنوّع مجموعة البيانات.

يُنفّذ معايير القبول للمرحلة 1 من خطة المشروع:
- المجموع ≥ 10 ساعات
- ≥ 4 متحدثين رئيسيين
- ≥ 2 لهجة
- ≥ 3 مستويات ضوضاء (لاحقاً، يحتاج تحليل صوتي)
- لا تسرّب متحدثين بين train/val/test
- كل ملف صوتي موجود فعلياً وقابل للقراءة

التشغيل:
    python scripts/validate_dataset.py
    python scripts/validate_dataset.py --strict   # فشل عند أي تحذير
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ingestion.manifest import load_manifest
from src.utils.config import PROJECT_ROOT, load_config
from src.utils.logging import get_logger

log = get_logger(__name__)


class ValidationResult:
    """جامع نتائج التحقق."""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.info: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)
        log.error(f"❌ {msg}")

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)
        log.warning(f"⚠️  {msg}")

    def ok(self, msg: str) -> None:
        self.info.append(msg)
        log.info(f"✅ {msg}")

    @property
    def passed(self) -> bool:
        return not self.errors

    def summary(self) -> str:
        return (
            f"الأخطاء: {len(self.errors)} | "
            f"التحذيرات: {len(self.warnings)} | "
            f"النجاحات: {len(self.info)}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="التحقق من جودة مجموعة البيانات")
    parser.add_argument(
        "--strict", action="store_true", help="اعتبر التحذيرات أخطاء وافشل عند أيٍّ منها"
    )
    parser.add_argument(
        "--check-files",
        action="store_true",
        help="التحقق من وجود كل ملف صوتي فعلياً (بطيء على البيانات الكبيرة)",
    )
    return parser.parse_args()


def check_existence(result: ValidationResult) -> dict[str, dict] | None:
    """تحقق من وجود كل سجلات التقسيمات."""
    cfg = load_config()
    manifests = {}

    for split in ["train", "val", "test"]:
        manifest_path = PROJECT_ROOT / cfg["data"][f"{split}_dir"] / "manifest.json"
        if not manifest_path.exists():
            result.error(f"سجل {split} غير موجود: {manifest_path}")
            return None
        manifests[split] = load_manifest(manifest_path)
        result.ok(f"سجل {split}: {manifests[split]['total_clips']} مقطع")

    return manifests


def check_total_duration(manifests: dict[str, dict], result: ValidationResult) -> None:
    """تحقق من المدة الإجمالية ≥ 10 ساعات."""
    cfg = load_config()
    min_hours = cfg["data"]["min_total_hours"]

    total_hours = sum(m["total_duration_hours"] for m in manifests.values())
    if total_hours >= min_hours:
        result.ok(f"المدة الإجمالية {total_hours:.2f} ساعة (≥ {min_hours} مطلوب)")
    else:
        result.warn(
            f"المدة الإجمالية {total_hours:.2f} ساعة < {min_hours} المطلوب. "
            f"يلزم تحميل المزيد من Common Voice."
        )


def check_speaker_count(manifests: dict[str, dict], result: ValidationResult) -> None:
    """تحقق من عدد المتحدثين الفريدين."""
    cfg = load_config()
    min_speakers = cfg["data"]["min_speakers"]

    all_speakers = set()
    for m in manifests.values():
        for clip in m["clips"]:
            spk = clip.get("speaker_id")
            if spk:
                all_speakers.add(spk)

    if len(all_speakers) >= min_speakers:
        result.ok(f"عدد المتحدثين الفريدين: {len(all_speakers)} (≥ {min_speakers})")
    else:
        result.warn(f"عدد المتحدثين {len(all_speakers)} < {min_speakers} المطلوب")


def check_speaker_leakage(manifests: dict[str, dict], result: ValidationResult) -> None:
    """تحقق حرج: لا متحدث في تقسيمين معاً.

    تسرّب المتحدثين هو السبب الأول لتقييم متفائل خادع.
    """
    speakers_per_split = {
        split: {c.get("speaker_id") for c in m["clips"] if c.get("speaker_id")}
        for split, m in manifests.items()
    }

    train_val = speakers_per_split["train"] & speakers_per_split["val"]
    train_test = speakers_per_split["train"] & speakers_per_split["test"]
    val_test = speakers_per_split["val"] & speakers_per_split["test"]

    leaks = len(train_val) + len(train_test) + len(val_test)

    if leaks == 0:
        result.ok("لا تسرّب متحدثين بين التقسيمات")
    else:
        result.error(
            f"تسرّب متحدثين! "
            f"train↔val: {len(train_val)}, train↔test: {len(train_test)}, val↔test: {len(val_test)}"
        )


def check_dialect_diversity(manifests: dict[str, dict], result: ValidationResult) -> None:
    """تحقق من تنوّع اللهجات."""
    cfg = load_config()
    min_dialects = cfg["data"]["min_dialects"]

    all_dialects = set()
    for m in manifests.values():
        for clip in m["clips"]:
            d = clip.get("dialect", "unknown")
            if d and d != "unknown":
                all_dialects.add(d)

    if len(all_dialects) >= min_dialects:
        result.ok(f"اللهجات: {sorted(all_dialects)} (≥ {min_dialects} مطلوب)")
    else:
        result.warn(
            f"تنوّع اللهجات ضعيف: {sorted(all_dialects) or '{}'} "
            f"(يلزم ≥ {min_dialects})"
        )


def check_gender_balance(manifests: dict[str, dict], result: ValidationResult) -> None:
    """تحقق من توازن الجنس بين الأصوات."""
    counts: Counter[str] = Counter()
    for m in manifests.values():
        for clip in m["clips"]:
            counts[clip.get("gender", "unknown")] += 1

    total = sum(counts.values())
    if total == 0:
        result.warn("لا توجد بيانات جنس")
        return

    male_ratio = counts.get("male", 0) / total
    female_ratio = counts.get("female", 0) / total
    unknown_ratio = counts.get("unknown", 0) / total

    log.info(
        f"توزيع الجنس: ذكر {male_ratio:.0%}، أنثى {female_ratio:.0%}، "
        f"غير معروف {unknown_ratio:.0%}"
    )

    if female_ratio < 0.20:
        result.warn(
            f"الأصوات النسائية قليلة ({female_ratio:.0%}). "
            "قد يجعل النموذج متحيّزاً للأصوات الذكورية."
        )
    if male_ratio < 0.20:
        result.warn(f"الأصوات الذكورية قليلة ({male_ratio:.0%})")
    if female_ratio + male_ratio > 0.40:
        result.ok("توزيع الجنس مقبول")


def check_audio_files_exist(manifests: dict[str, dict], result: ValidationResult) -> None:
    """تحقق من وجود كل ملف صوتي على القرص."""
    missing = 0
    total = 0
    for m in manifests.values():
        for clip in m["clips"]:
            total += 1
            audio = PROJECT_ROOT / clip["audio_path"]
            if not audio.exists():
                missing += 1
                if missing <= 5:  # عرض أول خمسة فقط
                    log.warning(f"  مفقود: {audio}")

    if missing == 0:
        result.ok(f"كل {total} ملف صوتي موجود")
    else:
        result.error(f"{missing}/{total} ملف صوتي مفقود")


def check_transcript_quality(manifests: dict[str, dict], result: ValidationResult) -> None:
    """تحقق من جودة التفريغ المرجعي."""
    empty = 0
    too_short = 0
    total = 0

    for m in manifests.values():
        for clip in m["clips"]:
            total += 1
            t = clip.get("transcript", "").strip()
            if not t:
                empty += 1
            elif len(t.split()) < 2:
                too_short += 1

    if empty > 0:
        result.error(f"{empty}/{total} مقطع بدون تفريغ")
    elif too_short > total * 0.05:
        result.warn(f"{too_short}/{total} مقطع بتفريغ قصير جداً (< كلمتين)")
    else:
        result.ok("جودة التفريغ المرجعي جيدة")


def main() -> int:
    args = parse_args()

    log.info("=" * 60)
    log.info("بدء التحقق من مجموعة البيانات")
    log.info("=" * 60)

    result = ValidationResult()

    manifests = check_existence(result)
    if not manifests:
        log.error("فشل التحقق المبدئي")
        return 1

    check_total_duration(manifests, result)
    check_speaker_count(manifests, result)
    check_speaker_leakage(manifests, result)
    check_dialect_diversity(manifests, result)
    check_gender_balance(manifests, result)
    check_transcript_quality(manifests, result)

    if args.check_files:
        log.info("التحقق من وجود الملفات الصوتية...")
        check_audio_files_exist(manifests, result)

    log.info("=" * 60)
    log.info(result.summary())
    log.info("=" * 60)

    if not result.passed:
        log.error("❌ التحقق فشل: راجع الأخطاء أعلاه")
        return 1
    if args.strict and result.warnings:
        log.error("❌ وضع strict: يوجد تحذيرات")
        return 1

    log.info("✅ مرّت كل الفحوص")
    return 0


if __name__ == "__main__":
    sys.exit(main())
