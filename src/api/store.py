"""مخزن بيانات موحَّد للـ API.

يربط نتائج كل المراحل (1-6) ويوفرها للواجهة بصيغة موحَّدة.

التصميم:
- في الإصدار الحالي: JSON files على القرص (بسيط، يكفي للديمو والتطوير).
- لاحقاً: يمكن استبداله بـ PostgreSQL أو MongoDB دون تغيير الواجهة.

كل مكالمة لها بنية ملفات:
    data/
    ├── transcripts/<call_id>.json    # مخرج ASR (المرحلة 4)
    ├── diarized/<call_id>.diarization.json  # مخرج Diarization (المرحلة 3)
    ├── nlp/<call_id>.nlp.json        # مخرج NLP (المرحلة 5)
    ├── kg/graph.json                  # رسم المعرفة الجامع (المرحلة 6)
    ├── uploads/<call_id>.<ext>        # الملف الصوتي الأصلي
    ├── reviews/<call_id>.json         # حالة التدقيق البشري
    └── jobs/<job_id>.json             # حالة المعالجة
"""
from __future__ import annotations

import hashlib
import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from src.api.models import ProcessingStatus, ReviewStatus
from src.utils.logging import get_logger

log = get_logger(__name__)

# قفل عمليات الكتابة لتجنب race conditions
_lock = threading.Lock()


class DataStore:
    """مخزن مركزي لكل بيانات النظام."""

    def __init__(self, root: Path | str):
        """
        Args:
            root: مجلد البيانات الجذر (data/).
        """
        self.root = Path(root)
        self.transcripts_dir = self.root / "transcripts"
        self.diarized_dir = self.root / "diarized"
        self.nlp_dir = self.root / "nlp"
        self.kg_dir = self.root / "kg"
        self.uploads_dir = self.root / "uploads"
        self.reviews_dir = self.root / "reviews"
        self.jobs_dir = self.root / "jobs"

        for d in (
            self.transcripts_dir, self.diarized_dir, self.nlp_dir,
            self.kg_dir, self.uploads_dir, self.reviews_dir, self.jobs_dir,
        ):
            d.mkdir(parents=True, exist_ok=True)

    # ──────────────────────────────────────────────
    # مكالمات
    # ──────────────────────────────────────────────

    def list_call_ids(self) -> list[str]:
        """قائمة معرّفات كل المكالمات المعروفة."""
        ids = set()
        for f in self.transcripts_dir.glob("*.json"):
            ids.add(f.stem)
        for f in self.nlp_dir.glob("*.nlp.json"):
            # call_001.nlp.json → call_001
            ids.add(f.name.replace(".nlp.json", ""))
        for f in self.uploads_dir.iterdir():
            if f.is_file():
                ids.add(f.stem)
        return sorted(ids)

    def get_call_transcript(self, call_id: str) -> Optional[dict]:
        """قراءة transcript للمكالمة."""
        path = self.transcripts_dir / f"{call_id}.json"
        if not path.exists():
            return None
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def get_call_nlp(self, call_id: str) -> Optional[dict]:
        """قراءة نتيجة NLP للمكالمة."""
        path = self.nlp_dir / f"{call_id}.nlp.json"
        if not path.exists():
            return None
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def get_call_summary(self, call_id: str) -> dict:
        """ملخص جامع للمكالمة (للقائمة الرئيسية)."""
        transcript = self.get_call_transcript(call_id) or {}
        nlp = self.get_call_nlp(call_id) or {}

        segments = transcript.get("segments", [])
        speakers = {s.get("speaker_id") for s in segments}

        # عدّ تطابقات watchlist
        watchlist_hits = 0
        if nlp:
            wl = nlp.get("nlp", {}).get("full_text_analysis", {}).get("watchlist_matches", [])
            watchlist_hits = len(wl)

        status = ProcessingStatus.COMPLETED if transcript else ProcessingStatus.PENDING

        return {
            "call_id": call_id,
            "duration_sec": transcript.get("duration_sec", 0.0),
            "n_speakers": len(speakers),
            "n_segments": len(segments),
            "status": status,
            "has_nlp": bool(nlp),
            "has_kg": (self.kg_dir / "graph.json").exists(),
            "watchlist_hits": watchlist_hits,
            "created_at": _file_mtime(self.transcripts_dir / f"{call_id}.json"),
            "processed_at": _file_mtime(self.nlp_dir / f"{call_id}.nlp.json"),
        }

    def save_transcript(self, call_id: str, data: dict) -> None:
        """حفظ transcript جديد (يُستدعى من pipeline)."""
        path = self.transcripts_dir / f"{call_id}.json"
        with _lock, open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def save_nlp(self, call_id: str, data: dict) -> None:
        """حفظ نتيجة NLP."""
        path = self.nlp_dir / f"{call_id}.nlp.json"
        with _lock, open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ──────────────────────────────────────────────
    # متحدثون
    # ──────────────────────────────────────────────

    def get_registry_summary(self) -> list[dict]:
        """ملخص قاعدة بصمات المتحدثين (من المرحلة 3)."""
        registry_path = self.diarized_dir / "registry.json"
        if not registry_path.exists():
            return []

        with open(registry_path, encoding="utf-8") as f:
            data = json.load(f)

        # نُضيف معلومة participated_in من المكالمات
        speaker_calls: dict[str, list[str]] = {}
        for call_id in self.list_call_ids():
            transcript = self.get_call_transcript(call_id)
            if not transcript:
                continue
            for seg in transcript.get("segments", []):
                spk_id = seg.get("speaker_id")
                if spk_id:
                    speaker_calls.setdefault(spk_id, [])
                    if call_id not in speaker_calls[spk_id]:
                        speaker_calls[spk_id].append(call_id)

        result = []
        for vp in data.get("voiceprints", []):
            sid = vp["speaker_id"]
            result.append({
                **vp,
                "n_clips": len(vp.get("source_clips", [])),
                "participated_in": speaker_calls.get(sid, []),
            })
        return result

    # ──────────────────────────────────────────────
    # رسم المعرفة
    # ──────────────────────────────────────────────

    def get_kg_data(self) -> Optional[dict]:
        """قراءة الرسم بصيغة الديمو."""
        path = self.kg_dir / "graph_demo.json"
        if not path.exists():
            # fallback: graph.json العام
            path = self.kg_dir / "graph.json"
            if not path.exists():
                return None
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def save_kg_data(self, data: dict) -> None:
        """حفظ الرسم بصيغة الديمو."""
        path = self.kg_dir / "graph_demo.json"
        with _lock, open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ──────────────────────────────────────────────
    # رفع الملفات
    # ──────────────────────────────────────────────

    def save_upload(self, filename: str, content: bytes) -> tuple[str, Path]:
        """حفظ ملف مرفوع.

        Returns:
            (call_id, file_path)
        """
        # نولّد call_id من hash المحتوى (تكرار = نفس الـ id)
        digest = hashlib.sha256(content).hexdigest()[:12]
        ext = Path(filename).suffix or ".wav"
        call_id = f"C-{digest}"
        path = self.uploads_dir / f"{call_id}{ext}"

        with _lock, open(path, "wb") as f:
            f.write(content)
        return call_id, path

    def get_upload_path(self, call_id: str) -> Optional[Path]:
        """مسار الملف الصوتي المرفوع لمكالمة."""
        for ext in (".wav", ".mp3", ".m4a", ".flac", ".ogg"):
            p = self.uploads_dir / f"{call_id}{ext}"
            if p.exists():
                return p
        return None

    # ──────────────────────────────────────────────
    # تدقيق بشري
    # ──────────────────────────────────────────────

    def get_reviews(self, call_id: str) -> dict[str, Any]:
        """قراءة كل المراجعات لمكالمة معينة.

        Returns:
            قاموس {entity_id: {review_status, reviewed_by, ...}}
        """
        path = self.reviews_dir / f"{call_id}.json"
        if not path.exists():
            return {}
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def save_review(
        self,
        call_id: str,
        entity_id: str,
        review_data: dict,
    ) -> None:
        """حفظ مراجعة لكيان أو حدث."""
        path = self.reviews_dir / f"{call_id}.json"
        with _lock:
            existing = {}
            if path.exists():
                with open(path, encoding="utf-8") as f:
                    existing = json.load(f)

            review_data["reviewed_at"] = datetime.now(timezone.utc).isoformat()
            existing[entity_id] = review_data

            with open(path, "w", encoding="utf-8") as f:
                json.dump(existing, f, ensure_ascii=False, indent=2)

    def get_review_for(self, call_id: str, entity_id: str) -> Optional[dict]:
        """قراءة مراجعة لكيان محدد."""
        reviews = self.get_reviews(call_id)
        return reviews.get(entity_id)

    # ──────────────────────────────────────────────
    # وظائف المعالجة (Background Jobs)
    # ──────────────────────────────────────────────

    def create_job(self, call_id: str) -> str:
        """إنشاء job جديد للمعالجة."""
        job_id = f"job_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{call_id}"
        job = {
            "job_id": job_id,
            "call_id": call_id,
            "status": ProcessingStatus.PENDING.value,
            "stage": "pending",
            "progress": 0.0,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
            "error": None,
        }
        path = self.jobs_dir / f"{job_id}.json"
        with _lock, open(path, "w", encoding="utf-8") as f:
            json.dump(job, f, ensure_ascii=False, indent=2)
        return job_id

    def update_job(self, job_id: str, **updates) -> None:
        """تحديث حالة job."""
        path = self.jobs_dir / f"{job_id}.json"
        if not path.exists():
            log.warning(f"job غير موجود: {job_id}")
            return

        with _lock:
            with open(path, encoding="utf-8") as f:
                job = json.load(f)
            job.update(updates)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(job, f, ensure_ascii=False, indent=2)

    def get_job(self, job_id: str) -> Optional[dict]:
        """قراءة حالة job."""
        path = self.jobs_dir / f"{job_id}.json"
        if not path.exists():
            return None
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def list_recent_jobs(self, limit: int = 20) -> list[dict]:
        """آخر jobs بترتيب زمني تنازلي."""
        files = sorted(
            self.jobs_dir.glob("*.json"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )
        jobs = []
        for f in files[:limit]:
            with open(f, encoding="utf-8") as fh:
                jobs.append(json.load(fh))
        return jobs


def _file_mtime(path: Path) -> Optional[str]:
    """وقت آخر تعديل لملف، أو None إن لم يوجد."""
    if not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime).isoformat()


def make_entity_id(call_id: str, entity: dict) -> str:
    """توليد ID موحَّد لكيان (لاستخدامه في التدقيق)."""
    return f"{call_id}:{entity['type']}:{entity['start']}:{entity['end']}"


def make_event_id(call_id: str, event: dict) -> str:
    """توليد ID موحَّد لحدث."""
    return f"{call_id}:event:{event.get('sentence_start', 0)}:{event.get('action', 'unknown')}"
