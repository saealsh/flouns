"""منسّق Pipeline الذي يربط كل المراحل معاً.

التدفّق:
    upload → audio processing → diarization → ASR → NLP → KG update

كل مرحلة تُحدّث الـ DataStore، ويمكن مراقبة التقدم عبر job_id.

استخدام:
    orch = Orchestrator(store)
    job_id = orch.process_call(audio_path, call_id)
    # المعالجة تجري في الخلفية
    status = store.get_job(job_id)
"""
from __future__ import annotations

import threading
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.api.models import ProcessingStatus
from src.api.store import DataStore
from src.utils.logging import get_logger

log = get_logger(__name__)


class Orchestrator:
    """يدير تشغيل كل المراحل عبر الـ pipeline."""

    def __init__(
        self,
        store: DataStore,
        *,
        watchlist_path: Optional[Path] = None,
        whisper_model: str = "tiny",
        whisper_backend: str = "mock",  # mock | faster-whisper
        n_speakers: Optional[int] = None,
    ):
        self.store = store
        self.watchlist_path = watchlist_path
        self.whisper_model = whisper_model
        self.whisper_backend = whisper_backend
        self.n_speakers = n_speakers

    def process_call(
        self,
        audio_path: Path,
        call_id: str,
        *,
        in_background: bool = True,
    ) -> str:
        """تشغيل pipeline كامل على ملف صوتي.

        Args:
            audio_path: مسار الملف الصوتي.
            call_id: معرّف المكالمة.
            in_background: تشغيل في thread منفصل (الافتراضي).

        Returns:
            job_id لتتبّع التقدم.
        """
        job_id = self.store.create_job(call_id)

        if in_background:
            thread = threading.Thread(
                target=self._run_pipeline,
                args=(audio_path, call_id, job_id),
                daemon=True,
            )
            thread.start()
        else:
            self._run_pipeline(audio_path, call_id, job_id)

        return job_id

    def _run_pipeline(self, audio_path: Path, call_id: str, job_id: str) -> None:
        """تشغيل المراحل تسلسلياً مع تحديث الـ job."""
        try:
            self.store.update_job(
                job_id,
                status=ProcessingStatus.PROCESSING.value,
                stage="diarization",
                progress=0.1,
            )

            # ──────────────────────────────────────────────
            # المرحلة 3: Diarization
            # ──────────────────────────────────────────────
            diarization_result = self._run_diarization(audio_path, call_id)
            self.store.update_job(
                job_id, stage="asr", progress=0.4,
            )

            # ──────────────────────────────────────────────
            # المرحلة 4: ASR
            # ──────────────────────────────────────────────
            transcript = self._run_asr(audio_path, call_id, diarization_result)
            self.store.save_transcript(call_id, transcript)
            self.store.update_job(
                job_id, stage="nlp", progress=0.7,
            )

            # ──────────────────────────────────────────────
            # المرحلة 5: NLP
            # ──────────────────────────────────────────────
            nlp_result = self._run_nlp(call_id, transcript)
            self.store.save_nlp(call_id, nlp_result)
            self.store.update_job(
                job_id, stage="kg", progress=0.9,
            )

            # ──────────────────────────────────────────────
            # المرحلة 6: KG (تحديث الرسم الجامع)
            # ──────────────────────────────────────────────
            self._update_kg(nlp_result)

            self.store.update_job(
                job_id,
                status=ProcessingStatus.COMPLETED.value,
                stage="done",
                progress=1.0,
                completed_at=datetime.now(timezone.utc).isoformat(),
            )
            log.info(f"✅ اكتملت معالجة {call_id} (job={job_id})")

        except Exception as e:
            log.error(f"❌ فشل pipeline لـ {call_id}: {e}")
            log.error(traceback.format_exc())
            self.store.update_job(
                job_id,
                status=ProcessingStatus.FAILED.value,
                error=str(e),
                completed_at=datetime.now(timezone.utc).isoformat(),
            )

    def _run_diarization(self, audio_path: Path, call_id: str) -> dict:
        """تشغيل diarization. يُرجع dict يصلح لـ ASR."""
        try:
            from src.diarization.pipeline import diarize_file
            from src.diarization.registry import VoiceprintRegistry
        except ImportError as e:
            log.warning(f"diarization غير متاح: {e}")
            return {"segments": []}

        # تحميل registry موجود إن وُجد
        registry_path = self.store.diarized_dir / "registry.json"
        if registry_path.exists():
            registry = VoiceprintRegistry.load(registry_path)
        else:
            registry = VoiceprintRegistry()

        try:
            result = diarize_file(
                audio_path,
                registry=registry,
                source_clip=call_id,
                n_speakers=self.n_speakers,
                auto_register_unknown=True,
            )
            # حفظ النتيجة
            out_path = self.store.diarized_dir / f"{call_id}.diarization.json"
            import json
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
            # حفظ registry محدّث
            registry.save(registry_path)
            return result.to_dict()
        except Exception as e:
            log.warning(f"diarization فشلت ({e})، نتابع بدونها")
            return {"segments": []}

    def _run_asr(
        self,
        audio_path: Path,
        call_id: str,
        diarization: dict,
    ) -> dict:
        """تشغيل ASR + alignment مع diarization."""
        try:
            from src.asr.pipeline import transcribe_file
        except ImportError as e:
            log.error(f"ASR غير متاح: {e}")
            # نُعيد transcript فارغاً ليستمر باقي الـ pipeline
            return {
                "call_id": call_id,
                "duration_sec": 0,
                "language": "ar",
                "segments": [],
            }

        try:
            transcript = transcribe_file(
                audio_path,
                diarization=diarization,
                model_name=self.whisper_model,
                backend=self.whisper_backend,
            )
            # ضمان call_id صحيح
            transcript_dict = (
                transcript.to_dict()
                if hasattr(transcript, "to_dict")
                else transcript
            )
            transcript_dict["call_id"] = call_id
            return transcript_dict
        except Exception as e:
            log.error(f"ASR فشلت: {e}")
            raise

    def _run_nlp(self, call_id: str, transcript: dict) -> dict:
        """تشغيل NLP على transcript."""
        from src.nlp.keywords import Watchlist
        from src.nlp.pipeline import NLPPipeline

        watchlist = None
        if self.watchlist_path and Path(self.watchlist_path).exists():
            watchlist = Watchlist.load(self.watchlist_path)

        # نحفظ transcript مؤقتاً ثم نُحلّله
        # (analyze_transcript تستقبل ملفاً لكن يمكن نضع البيانات مباشرة)
        pipeline = NLPPipeline(watchlist=watchlist)

        segments = transcript.get("segments", [])
        if not segments:
            return {**transcript, "nlp": {"full_text_analysis": {}, "per_segment": []}}

        full_text = " ".join(s.get("text", "") for s in segments)
        full_result = pipeline.analyze(full_text)

        per_segment = []
        for seg in segments:
            text = seg.get("text", "")
            seg_result = pipeline.analyze(text) if text else None
            per_segment.append({
                "speaker_name": seg.get("speaker_name"),
                "speaker_id": seg.get("speaker_id"),
                "start": seg.get("start"),
                "end": seg.get("end"),
                "text": text,
                "entities": [e.to_dict() for e in seg_result.entities] if seg_result else [],
                "events": [e.to_dict() for e in seg_result.events] if seg_result else [],
                "watchlist_matches": [
                    m.to_dict() for m in seg_result.watchlist_matches
                ] if seg_result else [],
            })

        # ربط الأحداث بالمتحدثين
        from src.nlp.pipeline import _attribute_events_to_speakers
        enriched_events = _attribute_events_to_speakers(full_result.events, segments)

        return {
            **transcript,
            "nlp": {
                "full_text_analysis": full_result.to_dict(),
                "per_segment": per_segment,
                "enriched_events": enriched_events,
            },
        }

    def _update_kg(self, nlp_result: dict) -> None:
        """تحديث الرسم بإضافة هذه المكالمة."""
        from src.kg.backends import NetworkXBackend
        from src.kg.builder import KGBuilder
        from src.kg.export import export_to_demo_format

        graph_path = self.store.kg_dir / "graph.json"

        if graph_path.exists():
            backend = NetworkXBackend.load(graph_path)
        else:
            backend = NetworkXBackend()

        builder = KGBuilder(backend)
        builder.ingest_call(nlp_result)

        # حفظ الرسم الكامل
        backend.save(graph_path)

        # تصدير لصيغة الديمو
        export_to_demo_format(backend, self.store.kg_dir / "graph_demo.json")
