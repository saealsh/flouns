"""تقسيم البيانات إلى train/val/test مع ضمان عدم تسرّب المتحدثين بين التقسيمات.

نقطة محورية: تقسيم بسيط 70/15/15 على المقاطع يسمح لنفس المتحدث بالظهور في
train و test معاً، مما يجعل التقييم مفرط التفاؤل. الحل: تقسيم على مستوى
المتحدث، ثم توزيع كل مقاطع المتحدث للتقسيم الذي وقع فيه.

التشغيل:
    python scripts/prepare_dataset.py
    python scripts/prepare_dataset.py --strategy random  # غير موصى به
"""
from __future__ import annotations

import argparse
import random
import shutil
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ingestion.manifest import load_manifest, save_manifest
from src.utils.config import PROJECT_ROOT, load_config
from src.utils.logging import get_logger

log = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="تقسيم البيانات 70/15/15")
    parser.add_argument(
        "--source",
        type=Path,
        default=None,
        help="مسار manifest المصدر (افتراضياً data/raw/common_voice/manifest.json)",
    )
    parser.add_argument(
        "--strategy",
        choices=["speaker", "random"],
        default="speaker",
        help="speaker = منع تسرّب المتحدثين (موصى به). random = تقسيم عشوائي بسيط.",
    )
    parser.add_argument(
        "--copy-files",
        action="store_true",
        help="نسخ الملفات الصوتية لمجلدات التقسيم (افتراضياً نحفظ مسارات فقط)",
    )
    return parser.parse_args()


def split_by_speaker(
    clips: list[dict],
    train_ratio: float,
    val_ratio: float,
    seed: int,
) -> dict[str, list[dict]]:
    """تقسيم على مستوى المتحدث: لا يوجد متحدث في تقسيمين معاً.

    الخوارزمية:
    1. تجميع المقاطع حسب speaker_id.
    2. خلط قائمة المتحدثين عشوائياً.
    3. توزيع المتحدثين على التقسيمات حتى تمتلئ الحصص.
    """
    rng = random.Random(seed)

    # تجميع حسب المتحدث
    by_speaker: dict[str, list[dict]] = defaultdict(list)
    unknown_clips: list[dict] = []

    for clip in clips:
        spk = clip.get("speaker_id")
        if spk:
            by_speaker[spk].append(clip)
        else:
            unknown_clips.append(clip)

    speakers = list(by_speaker.keys())
    rng.shuffle(speakers)

    log.info(f"عدد المتحدثين الفريدين: {len(speakers)}")
    log.info(f"مقاطع بدون speaker_id: {len(unknown_clips)}")

    total = len(clips)
    target_train = int(total * train_ratio)
    target_val = int(total * val_ratio)

    splits: dict[str, list[dict]] = {"train": [], "val": [], "test": []}

    for spk in speakers:
        spk_clips = by_speaker[spk]
        if len(splits["train"]) + len(spk_clips) <= target_train:
            target = "train"
        elif len(splits["val"]) + len(spk_clips) <= target_val:
            target = "val"
        else:
            target = "test"

        for clip in spk_clips:
            clip = {**clip, "split": target}
            splits[target].append(clip)

    # توزيع المقاطع المجهولة المتحدث على التقسيمات الأقل حجماً
    for clip in unknown_clips:
        smallest = min(splits, key=lambda k: len(splits[k]))
        clip = {**clip, "split": smallest}
        splits[smallest].append(clip)

    return splits


def split_random(
    clips: list[dict],
    train_ratio: float,
    val_ratio: float,
    seed: int,
) -> dict[str, list[dict]]:
    """تقسيم عشوائي بسيط على مستوى المقطع.

    تحذير: قد يُسرّب نفس المتحدث بين التقسيمات. استخدم split_by_speaker بدلاً عنه.
    """
    rng = random.Random(seed)
    shuffled = clips[:]
    rng.shuffle(shuffled)

    n = len(shuffled)
    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)

    return {
        "train": [{**c, "split": "train"} for c in shuffled[:n_train]],
        "val": [{**c, "split": "val"} for c in shuffled[n_train : n_train + n_val]],
        "test": [{**c, "split": "test"} for c in shuffled[n_train + n_val :]],
    }


def copy_split_files(splits: dict[str, list[dict]]) -> None:
    """نسخ ملفات الصوت إلى data/{train,val,test}/audio/."""
    cfg = load_config()
    for split_name, clips in splits.items():
        target_dir = PROJECT_ROOT / cfg["data"][f"{split_name}_dir"] / "audio"
        target_dir.mkdir(parents=True, exist_ok=True)

        for clip in clips:
            src = PROJECT_ROOT / clip["audio_path"]
            if not src.exists():
                log.warning(f"الملف غير موجود (تم تخطّيه): {src}")
                continue
            dst = target_dir / src.name
            if not dst.exists():
                shutil.copy2(src, dst)
            # تحديث المسار في السجل
            clip["audio_path"] = str(dst.relative_to(PROJECT_ROOT))

        log.info(f"  {split_name}: نُسخ {len(clips)} ملف")


def report_split_stats(splits: dict[str, list[dict]]) -> None:
    """طباعة تقرير عن التقسيمات."""
    total_clips = sum(len(c) for c in splits.values())
    total_dur = sum(sum(c["duration_sec"] for c in clips) for clips in splits.values())

    log.info("─" * 60)
    log.info("📊 تقرير التقسيم")
    log.info("─" * 60)
    log.info(f"الإجمالي: {total_clips} مقطع، {total_dur / 3600:.2f} ساعة")
    log.info("")

    for name, clips in splits.items():
        if not clips:
            continue
        dur = sum(c["duration_sec"] for c in clips) / 3600
        speakers = {c.get("speaker_id") for c in clips if c.get("speaker_id")}
        genders = {c.get("gender", "unknown") for c in clips}
        dialects = {c.get("dialect", "unknown") for c in clips}

        log.info(f"  {name.upper()}:")
        log.info(f"    مقاطع: {len(clips)} ({len(clips) / total_clips * 100:.1f}%)")
        log.info(f"    مدة: {dur:.2f} ساعة")
        log.info(f"    متحدثون: {len(speakers)}")
        log.info(f"    جنس: {sorted(genders)}")
        log.info(f"    لهجات: {sorted(dialects)}")
        log.info("")


def main() -> int:
    args = parse_args()
    cfg = load_config()

    # تحميل المصدر
    source = args.source or (
        PROJECT_ROOT / "data" / "raw" / "common_voice" / "manifest.json"
    )
    if not source.exists():
        log.error(f"السجل المصدر غير موجود: {source}")
        log.error("شغّل أولاً: python scripts/download_common_voice.py")
        return 1

    manifest = load_manifest(source)
    clips = manifest["clips"]
    log.info(f"تحميل {len(clips)} مقطع من {source}")

    # التقسيم
    train_ratio = cfg["data"]["splits"]["train"]
    val_ratio = cfg["data"]["splits"]["val"]
    seed = cfg["data"]["random_seed"]

    log.info(f"الاستراتيجية: {args.strategy}")
    if args.strategy == "speaker":
        splits = split_by_speaker(clips, train_ratio, val_ratio, seed)
    else:
        splits = split_random(clips, train_ratio, val_ratio, seed)

    # نسخ الملفات أو الإبقاء على المسارات الأصلية
    if args.copy_files:
        log.info("جاري نسخ الملفات...")
        copy_split_files(splits)

    # حفظ سجل لكل تقسيم
    for split_name, clip_list in splits.items():
        out_dir = PROJECT_ROOT / cfg["data"][f"{split_name}_dir"]
        out_dir.mkdir(parents=True, exist_ok=True)
        save_manifest(clip_list, out_dir / "manifest.json")

    report_split_stats(splits)
    log.info("✅ اكتمل التقسيم")
    return 0


if __name__ == "__main__":
    sys.exit(main())
