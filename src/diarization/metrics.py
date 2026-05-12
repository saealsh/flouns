"""قياس جودة فصل المتحدثين عبر DER (Diarization Error Rate).

DER هو المقياس القياسي في الأدبيات، صيغته:

    DER = (FA + Miss + Confusion) / TotalReferenceTime

حيث:
- FA (False Alarm): وقت أُعلِن كلاماً والمرجع صمت.
- Miss: وقت كلام مرجعي لم يُكشف.
- Confusion: وقت كلام صحيح لكن أُسند لمتحدث خاطئ.

نوفّر كذلك JER (Jaccard Error Rate) كمقياس أبسط أحياناً.

استخدام:
    from src.diarization.metrics import diarization_error_rate

    hypothesis = [(0.0, 1.5, "spk1"), (1.5, 3.0, "spk2")]
    reference  = [(0.0, 1.4, "alice"), (1.4, 3.0, "bob")]

    der = diarization_error_rate(hypothesis, reference)
    print(f"DER = {der['der']:.2%}")
"""
from __future__ import annotations

from typing import NamedTuple

import numpy as np


class Segment(NamedTuple):
    start: float
    end: float
    label: str

    @property
    def duration(self) -> float:
        return self.end - self.start


def _to_segments(items: list) -> list[Segment]:
    """تحويل قائمة من tuples/dicts إلى قائمة Segment."""
    result = []
    for item in items:
        if isinstance(item, Segment):
            result.append(item)
        elif isinstance(item, dict):
            result.append(Segment(
                start=float(item["start"]),
                end=float(item["end"]),
                label=str(item.get("label") or item.get("speaker", "")),
            ))
        elif isinstance(item, (tuple, list)) and len(item) >= 3:
            result.append(Segment(start=float(item[0]), end=float(item[1]), label=str(item[2])))
        else:
            raise ValueError(f"تنسيق غير مدعوم: {item!r}")
    return result


def _frame_labels(
    segments: list[Segment],
    duration: float,
    frame_ms: int = 10,
) -> np.ndarray:
    """تحويل قائمة segments إلى تسلسل تسميات على شبكة إطارات.

    لكل إطار (10ms افتراضياً)، نسجّل التسمية المسيطرة (أو "" للصمت).
    التداخلات تُحلّ بأخذ آخر segment متداخل (المرجع متّبع في py-diarization).
    """
    n_frames = int(np.ceil(duration * 1000 / frame_ms))
    labels = np.array([""] * n_frames, dtype=object)
    frame_dur = frame_ms / 1000.0

    for seg in segments:
        start_idx = max(0, int(seg.start / frame_dur))
        end_idx = min(n_frames, int(np.ceil(seg.end / frame_dur)))
        labels[start_idx:end_idx] = seg.label

    return labels


def _optimal_label_mapping(
    hyp_labels: np.ndarray,
    ref_labels: np.ndarray,
) -> dict[str, str]:
    """إيجاد أفضل تطابق بين تسميات الـ hypothesis والـ reference.

    نستخدم Hungarian algorithm (تكلفة = -وقت تداخل).
    هذا يحلّ مشكلة: مجموعتنا «0» قد تطابق المتحدث «alice»، ليس بالضرورة بنفس الاسم.
    """
    hyp_set = sorted({l for l in hyp_labels if l})
    ref_set = sorted({l for l in ref_labels if l})

    if not hyp_set or not ref_set:
        return {}

    # مصفوفة الـ co-occurrence
    cooc = np.zeros((len(hyp_set), len(ref_set)), dtype=np.float64)
    hyp_idx = {l: i for i, l in enumerate(hyp_set)}
    ref_idx = {l: i for i, l in enumerate(ref_set)}

    for h, r in zip(hyp_labels, ref_labels, strict=True):
        if h and r:
            cooc[hyp_idx[h], ref_idx[r]] += 1

    # Hungarian للحد الأقصى → ننفي العلامة
    try:
        from scipy.optimize import linear_sum_assignment
        rows, cols = linear_sum_assignment(-cooc)
        return {hyp_set[r]: ref_set[c] for r, c in zip(rows, cols)}
    except ImportError:
        # fallback: greedy
        mapping = {}
        used_refs = set()
        order = np.argsort(-cooc.flatten())
        for flat in order:
            h = flat // len(ref_set)
            r = flat % len(ref_set)
            if hyp_set[h] not in mapping and ref_set[r] not in used_refs:
                mapping[hyp_set[h]] = ref_set[r]
                used_refs.add(ref_set[r])
        return mapping


def diarization_error_rate(
    hypothesis: list,
    reference: list,
    *,
    frame_ms: int = 10,
    collar_sec: float = 0.0,
) -> dict[str, float]:
    """حساب DER كاملاً.

    Args:
        hypothesis: قائمة (start, end, label) من النظام.
        reference: قائمة (start, end, label) المرجعية.
        frame_ms: دقة الإطار للحساب.
        collar_sec: هامش تسامح عند حدود segments (شائع: 0.25s).
                    الإطارات داخل ±collar من حدود مرجعية تُتجاهل.

    Returns:
        قاموس فيه: der, false_alarm, miss, confusion, total_ref_sec, mapping.
    """
    hyp = _to_segments(hypothesis)
    ref = _to_segments(reference)

    if not ref:
        return {
            "der": 1.0 if hyp else 0.0,
            "false_alarm": sum(s.duration for s in hyp),
            "miss": 0.0,
            "confusion": 0.0,
            "total_ref_sec": 0.0,
            "mapping": {},
        }

    # مدة الإطار = max(آخر زمن في كليهما)
    max_end = max(
        max((s.end for s in hyp), default=0.0),
        max(s.end for s in ref),
    )
    if max_end == 0:
        return {"der": 0.0, "false_alarm": 0.0, "miss": 0.0, "confusion": 0.0, "total_ref_sec": 0.0, "mapping": {}}

    hyp_frames = _frame_labels(hyp, max_end, frame_ms)
    ref_frames = _frame_labels(ref, max_end, frame_ms)
    frame_dur = frame_ms / 1000.0

    # تطبيق collar: إخفاء الإطارات قرب حدود المرجع
    if collar_sec > 0:
        collar_frames = int(collar_sec / frame_dur)
        mask = np.ones(len(ref_frames), dtype=bool)
        for seg in ref:
            for boundary in [seg.start, seg.end]:
                b_idx = int(boundary / frame_dur)
                lo = max(0, b_idx - collar_frames)
                hi = min(len(mask), b_idx + collar_frames)
                mask[lo:hi] = False
        hyp_frames = hyp_frames[mask]
        ref_frames = ref_frames[mask]

    # إيجاد أفضل تطابق
    mapping = _optimal_label_mapping(hyp_frames, ref_frames)
    # نطبّق التطابق على hyp_frames
    mapped_hyp = np.array([mapping.get(l, l) if l else "" for l in hyp_frames], dtype=object)

    # حساب الأخطاء (بالإطارات)
    is_ref_speech = ref_frames != ""
    is_hyp_speech = mapped_hyp != ""

    false_alarm_frames = (~is_ref_speech & is_hyp_speech).sum()
    miss_frames = (is_ref_speech & ~is_hyp_speech).sum()
    confusion_frames = (is_ref_speech & is_hyp_speech & (mapped_hyp != ref_frames)).sum()

    false_alarm = false_alarm_frames * frame_dur
    miss = miss_frames * frame_dur
    confusion = confusion_frames * frame_dur
    total_ref = is_ref_speech.sum() * frame_dur

    der = (false_alarm + miss + confusion) / total_ref if total_ref > 0 else 0.0

    return {
        "der": round(der, 4),
        "false_alarm": round(false_alarm, 3),
        "miss": round(miss, 3),
        "confusion": round(confusion, 3),
        "total_ref_sec": round(total_ref, 3),
        "mapping": mapping,
    }


def speaker_purity_coverage(
    hypothesis: list,
    reference: list,
    *,
    frame_ms: int = 10,
) -> dict[str, float]:
    """مقياسان مكمّلان لـ DER:

    - **Purity**: كم نقي كل cluster من النظام؟ (لا يخلط بين متحدثين)
    - **Coverage**: كم من كلام كل متحدث مرجعي يُجمَّع معاً؟

    Purity عالية + Coverage عالية = diarization ممتاز.
    Purity عالية + Coverage منخفضة = تجزئة مفرطة (over-splitting).
    Purity منخفضة + Coverage عالية = تجميع مفرط (under-clustering).
    """
    hyp = _to_segments(hypothesis)
    ref = _to_segments(reference)
    if not hyp or not ref:
        return {"purity": 0.0, "coverage": 0.0}

    max_end = max(max(s.end for s in hyp), max(s.end for s in ref))
    hyp_frames = _frame_labels(hyp, max_end, frame_ms)
    ref_frames = _frame_labels(ref, max_end, frame_ms)

    # Purity: لكل cluster من hyp، احسب أكبر تطابق مع cluster من ref
    purity_num = 0
    total_hyp_frames = 0
    for h in set(hyp_frames):
        if not h:
            continue
        mask = hyp_frames == h
        total_hyp_frames += mask.sum()
        # count refs المتزامنة
        ref_subset = ref_frames[mask]
        max_overlap = max(
            (ref_subset == r).sum() for r in set(ref_subset) if r
        ) if any(r for r in ref_subset) else 0
        purity_num += max_overlap

    purity = purity_num / total_hyp_frames if total_hyp_frames > 0 else 0.0

    # Coverage: لكل ref label، احسب أكبر تطابق مع hyp cluster
    coverage_num = 0
    total_ref_frames = 0
    for r in set(ref_frames):
        if not r:
            continue
        mask = ref_frames == r
        total_ref_frames += mask.sum()
        hyp_subset = hyp_frames[mask]
        max_overlap = max(
            (hyp_subset == h).sum() for h in set(hyp_subset) if h
        ) if any(h for h in hyp_subset) else 0
        coverage_num += max_overlap

    coverage = coverage_num / total_ref_frames if total_ref_frames > 0 else 0.0

    return {
        "purity": round(purity, 4),
        "coverage": round(coverage, 4),
    }
