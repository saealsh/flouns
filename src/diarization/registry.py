"""قاعدة بصمات المتحدثين المعروفين (Voiceprint Registry).

تربط متحدثاً مفترضاً (cluster بدون اسم) ببصمة معروفة (اسم محقّق).
تطابق حالات الديمو في صفحة speakers.html:

- stable: بصمة محسوبة من 3+ تسجيلات، تطابق ≥ 0.75.
- new: بصمة من تسجيل واحد، تحتاج تأكيد بشري.
- unstable: التطابق منخفض، الإشارة الصوتية غير كافية.
- unknown: لا تطابق مع أي بصمة (sim < 0.55).

استخدام:
    from src.diarization.registry import VoiceprintRegistry

    reg = VoiceprintRegistry()
    reg.register("أحمد", embedding_arr, source_clip="C-001")
    match = reg.identify(new_embedding)
    # match: {speaker_id, name, similarity, status}
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

import numpy as np

from src.utils.logging import get_logger

log = get_logger(__name__)

VoiceprintStatus = Literal["stable", "new", "unstable", "unknown"]


@dataclass
class Voiceprint:
    """بصمة متحدث: متجه + ميتاداتا."""

    speaker_id: str
    name: str
    centroid: np.ndarray = field(repr=False)  # المتوسط L2-normalized لكل العينات
    samples: list[np.ndarray] = field(default_factory=list, repr=False)
    source_clips: list[str] = field(default_factory=list)
    status: VoiceprintStatus = "new"

    @property
    def n_samples(self) -> int:
        return len(self.samples)

    def add_sample(self, embedding: np.ndarray, source_clip: str | None = None) -> None:
        """إضافة عينة جديدة وإعادة حساب المركز."""
        self.samples.append(embedding.copy())
        if source_clip and source_clip not in self.source_clips:
            self.source_clips.append(source_clip)
        self._recompute_centroid()
        self._update_status()

    def _recompute_centroid(self) -> None:
        if not self.samples:
            return
        stacked = np.stack(self.samples)
        mean = stacked.mean(axis=0)
        norm = np.linalg.norm(mean)
        self.centroid = (mean / norm).astype(np.float32) if norm > 1e-8 else mean.astype(np.float32)

    def _update_status(self) -> None:
        """تحديث الحالة بناءً على عدد العينات وتشتّتها."""
        if not self.samples:
            self.status = "unknown"
            return

        if len(self.samples) < 3:
            self.status = "new"
            return

        # حساب تشابه كل عينة مع المركز — إن كان التشتت كبيراً فالبصمة غير مستقرة
        sims = [float(np.dot(s, self.centroid)) for s in self.samples]
        mean_sim = float(np.mean(sims))

        if mean_sim >= 0.92:
            self.status = "stable"
        elif mean_sim >= 0.85:
            self.status = "new"
        else:
            self.status = "unstable"


@dataclass
class IdentificationResult:
    """نتيجة محاولة التعرّف على متحدث."""

    speaker_id: str | None
    name: str
    similarity: float
    status: VoiceprintStatus
    candidates: list[tuple[str, str, float]] = field(default_factory=list)
    """أعلى 3 مرشّحين (id, name, similarity) للتدقيق البشري."""


class VoiceprintRegistry:
    """قاعدة بيانات لبصمات المتحدثين المعروفين."""

    def __init__(
        self,
        *,
        match_threshold: float = 0.85,
        confident_threshold: float = 0.92,
    ):
        """
        Args:
            match_threshold: أقل تشابه يُعتبر تطابقاً (وإلا = unknown).
                المعايرة الافتراضية تناسب MFCC (78-d). للنماذج العميقة
                (ECAPA-TDNN, pyannote)، عادة 0.55-0.70.
            confident_threshold: أعلى تشابه يُعتبر «مؤكَّداً» (لتحديث الحالة).
        """
        self.voiceprints: dict[str, Voiceprint] = {}
        self.match_threshold = match_threshold
        self.confident_threshold = confident_threshold

    def __len__(self) -> int:
        return len(self.voiceprints)

    def register(
        self,
        name: str,
        embedding: np.ndarray,
        *,
        speaker_id: str | None = None,
        source_clip: str | None = None,
    ) -> str:
        """تسجيل متحدث جديد أو إضافة عيّنة لمتحدث موجود.

        Args:
            name: اسم المتحدث.
            embedding: متجه البصمة.
            speaker_id: إن حُدِّد ووُجد، نضيف العيّنة. إن None نولّد جديداً.
            source_clip: معرّف المكالمة مصدر العيّنة.

        Returns:
            speaker_id الفعلي.
        """
        if speaker_id and speaker_id in self.voiceprints:
            self.voiceprints[speaker_id].add_sample(embedding, source_clip)
            return speaker_id

        if speaker_id is None:
            speaker_id = self._next_speaker_id()

        # طبَّع البصمة إن لم تكن مطبَّعة
        norm = np.linalg.norm(embedding)
        if norm > 1e-8:
            embedding = embedding / norm

        vp = Voiceprint(
            speaker_id=speaker_id,
            name=name,
            centroid=embedding.astype(np.float32).copy(),
            samples=[embedding.astype(np.float32).copy()],
            source_clips=[source_clip] if source_clip else [],
            status="new",
        )
        self.voiceprints[speaker_id] = vp
        log.debug(f"سُجِّل متحدث جديد: {speaker_id} = {name}")
        return speaker_id

    def identify(self, embedding: np.ndarray, top_k: int = 3) -> IdentificationResult:
        """البحث عن أقرب متحدث للبصمة المعطاة.

        Args:
            embedding: متجه البصمة المراد التعرّف عليه.
            top_k: عدد أعلى المرشّحين للإرجاع.

        Returns:
            IdentificationResult فيه التطابق + المرشّحون.
        """
        if not self.voiceprints:
            return IdentificationResult(
                speaker_id=None, name="غير معروف", similarity=0.0, status="unknown"
            )

        # طبَّع المدخل
        norm = np.linalg.norm(embedding)
        if norm > 1e-8:
            embedding = embedding / norm

        # حساب التشابه مع كل البصمات
        sims = [
            (vp.speaker_id, vp.name, float(np.dot(embedding, vp.centroid)), vp.status)
            for vp in self.voiceprints.values()
        ]
        sims.sort(key=lambda x: x[2], reverse=True)

        best_id, best_name, best_sim, best_status = sims[0]
        candidates = [(sid, name, sim) for sid, name, sim, _ in sims[:top_k]]

        if best_sim < self.match_threshold:
            return IdentificationResult(
                speaker_id=None,
                name="غير معروف",
                similarity=best_sim,
                status="unknown",
                candidates=candidates,
            )

        return IdentificationResult(
            speaker_id=best_id,
            name=best_name,
            similarity=best_sim,
            status=best_status,
            candidates=candidates,
        )

    def assign_clusters(
        self,
        embeddings: np.ndarray,
        labels: np.ndarray,
        *,
        source_clip: str | None = None,
        auto_register_unknown: bool = False,
        intra_file_threshold: float = 0.95,
    ) -> list[IdentificationResult]:
        """ربط كل cluster من diarization بمتحدث في القاعدة.

        مبدأ مهم: clusters داخل ملف واحد فُصِلت بالـ clustering لأنها متحدثون
        مختلفون. لذا لا نسمح بأن يُطابَق clusterان مختلفان داخل نفس الملف
        بنفس المتحدث في القاعدة، إلا عند تشابه عالٍ جداً (intra_file_threshold).

        Args:
            embeddings: شكل (N, D).
            labels: شكل (N,) — معرّفات cluster لكل قطعة.
            source_clip: معرّف المكالمة.
            auto_register_unknown: تسجيل تلقائي للـ unknowns كمتحدثين جدد.
            intra_file_threshold: تشابه لازم لاعتبار clusterين داخل نفس الملف
                نفس المتحدث.

        Returns:
            قائمة بطول عدد clusters الفريدة، كل عنصر = نتيجة تعرّف.
        """
        unique_clusters = sorted(set(labels.tolist()))
        results = []
        used_speaker_ids: set[str] = set()

        for c in unique_clusters:
            mask = labels == c
            cluster_embs = embeddings[mask]
            centroid = cluster_embs.mean(axis=0)
            norm = np.linalg.norm(centroid)
            if norm > 1e-8:
                centroid = centroid / norm

            result = self.identify(centroid)

            # حماية ضد التطابق المزدوج داخل نفس الملف:
            # cluster مختلف داخل ملف واحد لا يجب أن يحمل نفس speaker_id إلا
            # عند تشابه عالٍ جداً (نفس المتحدث فعلاً، مثل تكرار في clustering).
            if (
                result.speaker_id is not None
                and result.speaker_id in used_speaker_ids
                and result.similarity < intra_file_threshold
            ):
                # ابحث عن مرشّح بديل بين الـ candidates
                alt = None
                for cand_id, cand_name, cand_sim in result.candidates[1:]:
                    if cand_id not in used_speaker_ids and cand_sim >= self.match_threshold:
                        alt = (cand_id, cand_name, cand_sim)
                        break
                if alt:
                    result = IdentificationResult(
                        speaker_id=alt[0],
                        name=alt[1],
                        similarity=alt[2],
                        status=self.voiceprints[alt[0]].status,
                        candidates=result.candidates,
                    )
                else:
                    # لا بديل → نعدّه جديداً
                    result = IdentificationResult(
                        speaker_id=None,
                        name="غير معروف",
                        similarity=result.similarity,
                        status="unknown",
                        candidates=result.candidates,
                    )

            if result.speaker_id is None and auto_register_unknown:
                new_id = self._next_speaker_id()
                self.register(
                    new_id,
                    centroid,
                    speaker_id=new_id,
                    source_clip=source_clip,
                )
                result = IdentificationResult(
                    speaker_id=new_id,
                    name=new_id,
                    similarity=1.0,
                    status="new",
                )
            elif result.speaker_id is not None and source_clip:
                self.voiceprints[result.speaker_id].add_sample(centroid, source_clip)

            if result.speaker_id is not None:
                used_speaker_ids.add(result.speaker_id)
            results.append(result)

        return results

    def _next_speaker_id(self) -> str:
        """توليد معرّف فريد بصيغة SPK_NN."""
        nums = []
        for sid in self.voiceprints:
            if sid.startswith("SPK_"):
                try:
                    nums.append(int(sid[4:]))
                except ValueError:
                    pass
        next_num = max(nums) + 1 if nums else 1
        return f"SPK_{next_num:02d}"

    def save(self, path: Path | str) -> None:
        """حفظ القاعدة لملف JSON + ملف npz للمتجهات.

        Args:
            path: مسار الـ JSON (المتجهات تُحفظ بنفس الجذر بـ .npz).
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        npz_path = path.with_suffix(".npz")

        # 1. حفظ المتجهات في npz (كفء)
        centroids = {sid: vp.centroid for sid, vp in self.voiceprints.items()}
        samples = {
            f"{sid}__samples": np.stack(vp.samples) if vp.samples else np.empty((0, 0))
            for sid, vp in self.voiceprints.items()
        }
        np.savez(npz_path, **centroids, **samples)

        # 2. حفظ الميتاداتا في JSON
        meta = {
            "match_threshold": self.match_threshold,
            "confident_threshold": self.confident_threshold,
            "voiceprints": [
                {
                    "speaker_id": vp.speaker_id,
                    "name": vp.name,
                    "n_samples": vp.n_samples,
                    "source_clips": vp.source_clips,
                    "status": vp.status,
                }
                for vp in self.voiceprints.values()
            ],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        log.info(f"حُفظت قاعدة البصمات: {len(self)} متحدث في {path}")

    @classmethod
    def load(cls, path: Path | str) -> "VoiceprintRegistry":
        """قراءة القاعدة من ملفات JSON + npz."""
        path = Path(path)
        npz_path = path.with_suffix(".npz")

        if not path.exists():
            raise FileNotFoundError(f"الميتاداتا غير موجودة: {path}")
        if not npz_path.exists():
            raise FileNotFoundError(f"المتجهات غير موجودة: {npz_path}")

        with open(path, encoding="utf-8") as f:
            meta = json.load(f)

        npz = np.load(npz_path)
        reg = cls(
            match_threshold=meta.get("match_threshold", 0.55),
            confident_threshold=meta.get("confident_threshold", 0.75),
        )

        for vp_meta in meta["voiceprints"]:
            sid = vp_meta["speaker_id"]
            samples_key = f"{sid}__samples"
            samples = list(npz[samples_key]) if samples_key in npz.files else []
            centroid = npz[sid] if sid in npz.files else np.zeros(0)

            vp = Voiceprint(
                speaker_id=sid,
                name=vp_meta["name"],
                centroid=centroid.astype(np.float32),
                samples=[s.astype(np.float32) for s in samples],
                source_clips=vp_meta.get("source_clips", []),
                status=vp_meta.get("status", "new"),
            )
            reg.voiceprints[sid] = vp

        log.info(f"حُمِّلت قاعدة البصمات: {len(reg)} متحدث")
        return reg

    def summary(self) -> list[dict]:
        """ملخّص جدولي لكل البصمات (للعرض في التقارير)."""
        return [
            {
                "speaker_id": vp.speaker_id,
                "name": vp.name,
                "status": vp.status,
                "n_samples": vp.n_samples,
                "n_clips": len(vp.source_clips),
            }
            for vp in self.voiceprints.values()
        ]
