"""بناء وإدارة سجل البيانات (manifest.json).

السجل (manifest) هو المصدر الوحيد لمعرفة:
- ما الملفات الموجودة لدينا
- خصائص كل ملف (مدة، متحدث، لهجة، مصدر، هاش)
- في أي تقسيم (train/val/test) يقع
- نسبة جودته

البنية:
    {
      "version": "1.0",
      "created_at": "2026-05-10T12:00:00Z",
      "total_clips": 500,
      "total_duration_sec": 36000,
      "clips": [
        {
          "clip_id": "cv_ar_00001",
          "source": "common_voice_17",
          "audio_path": "data/raw/common_voice/clip_00001.wav",
          "transcript": "النص المرجعي...",
          "duration_sec": 5.4,
          "speaker_id": "client_id_hash",
          "gender": "female|male|unknown",
          "dialect": "msa|gulf|levantine|...",
          "split": "train|val|test",
          "sample_rate": 48000,
          "language": "ar",
          "license": "CC0-1.0",
          "ingested_at": "2026-05-10T12:00:00Z"
        }
      ]
    }
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.utils.logging import get_logger

log = get_logger(__name__)

MANIFEST_VERSION = "1.0"


def utcnow_iso() -> str:
    """الوقت الحالي بصيغة ISO-8601 UTC."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def file_hash(path: Path, algo: str = "sha256", chunk_size: int = 65536) -> str:
    """حساب هاش لملف بكفاءة (دفعات بدلاً من تحميل كامل)."""
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def make_clip_record(
    clip_id: str,
    source: str,
    audio_path: Path | str,
    transcript: str,
    duration_sec: float,
    *,
    speaker_id: str | None = None,
    gender: str = "unknown",
    dialect: str = "unknown",
    split: str = "unassigned",
    sample_rate: int | None = None,
    license: str = "unknown",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """بناء سجل واحد لمقطع صوتي.

    Args:
        clip_id: معرّف فريد (مثل cv_ar_00001).
        source: مصدر البيانات (common_voice_17, mgb, custom).
        audio_path: مسار الملف الصوتي.
        transcript: النص المرجعي.
        duration_sec: المدة بالثواني.
        speaker_id: معرّف المتحدث (هاش الـ client_id من Common Voice).
        gender: female | male | unknown.
        dialect: msa (فصحى) | gulf | levantine | egyptian | maghrebi | unknown.
        split: train | val | test | unassigned.
        sample_rate: تردد العينة الأصلي.
        license: ترخيص البيانات.
        extra: حقول إضافية اختيارية.

    Returns:
        قاموس بسجل المقطع.
    """
    record = {
        "clip_id": clip_id,
        "source": source,
        "audio_path": str(audio_path),
        "transcript": transcript,
        "duration_sec": round(float(duration_sec), 3),
        "speaker_id": speaker_id,
        "gender": gender,
        "dialect": dialect,
        "split": split,
        "sample_rate": sample_rate,
        "language": "ar",
        "license": license,
        "ingested_at": utcnow_iso(),
    }
    if extra:
        record["extra"] = extra
    return record


def save_manifest(records: list[dict[str, Any]], path: Path | str) -> None:
    """حفظ سجل بيانات إلى JSON.

    Args:
        records: قائمة بسجلات المقاطع.
        path: مسار ملف الـ manifest.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    total_duration = sum(r.get("duration_sec", 0) for r in records)

    manifest = {
        "version": MANIFEST_VERSION,
        "created_at": utcnow_iso(),
        "total_clips": len(records),
        "total_duration_sec": round(total_duration, 2),
        "total_duration_hours": round(total_duration / 3600, 3),
        "clips": records,
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    log.info(
        f"حُفظ السجل: {path.name} ({len(records)} مقطع، "
        f"{manifest['total_duration_hours']:.2f} ساعة)"
    )


def load_manifest(path: Path | str) -> dict[str, Any]:
    """قراءة manifest.json.

    Args:
        path: مسار الملف.

    Returns:
        القاموس الكامل بما فيه الميتاداتا والـ clips.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"السجل غير موجود: {path}")

    with open(path, encoding="utf-8") as f:
        manifest = json.load(f)

    # تحقق توافق الإصدار
    if manifest.get("version") != MANIFEST_VERSION:
        log.warning(
            f"إصدار السجل {manifest.get('version')} مختلف عن المتوقع {MANIFEST_VERSION}"
        )

    return manifest


def merge_manifests(manifests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """دمج عدة سجلات في قائمة سجلات واحدة موحدة.

    يحرس من تكرار clip_id بإسقاط المكررات (يُحتفظ بالأول).
    """
    seen_ids: set[str] = set()
    merged: list[dict[str, Any]] = []

    for m in manifests:
        for clip in m.get("clips", []):
            cid = clip.get("clip_id")
            if cid in seen_ids:
                log.warning(f"تم تجاهل مقطع مكرر: {cid}")
                continue
            seen_ids.add(cid)
            merged.append(clip)

    return merged
