"""قياس جودة التفريغ التلقائي.

المقاييس الأساسية:

- **WER** (Word Error Rate): نسبة الأخطاء على مستوى الكلمات.
  WER = (S + D + I) / N
  حيث S = استبدال، D = حذف، I = إضافة، N = كلمات المرجع.

- **CER** (Character Error Rate): مثل WER لكن على الحروف.
  مفيد للعربية لأن WER قاسٍ مع لغات بـ morphology غنية.

- **Speaker Attribution Accuracy**: نسبة الكلمات المُسندة للمتحدث الصحيح.

استخدام:
    from src.asr.metrics import compute_wer, evaluate_transcript

    wer = compute_wer(reference="السلام عليكم", hypothesis="السلام عليكم ورحمة")
    # 0.5 = خطأ واحد (إضافة) / 2 كلمات مرجع
"""
from __future__ import annotations

from dataclasses import dataclass

from src.utils.arabic_text import normalize_for_asr
from src.utils.logging import get_logger

log = get_logger(__name__)


@dataclass
class ErrorRateResult:
    """نتيجة حساب معدل أخطاء."""

    error_rate: float
    substitutions: int
    deletions: int
    insertions: int
    n_reference: int
    n_hypothesis: int

    def to_dict(self) -> dict:
        return {
            "error_rate": round(self.error_rate, 4),
            "substitutions": self.substitutions,
            "deletions": self.deletions,
            "insertions": self.insertions,
            "n_reference": self.n_reference,
            "n_hypothesis": self.n_hypothesis,
            "accuracy": round(1.0 - self.error_rate, 4),
        }


def _edit_distance(ref: list, hyp: list) -> dict[str, int]:
    """حساب مسافة التحرير بـ DP، يُرجع تفصيل الأخطاء.

    خوارزمية Levenshtein بمصفوفة DP + تتبع للعمليات.
    """
    n, m = len(ref), len(hyp)

    if n == 0:
        return {"substitutions": 0, "deletions": 0, "insertions": m}
    if m == 0:
        return {"substitutions": 0, "deletions": n, "insertions": 0}

    # dp[i][j] = أقل عدد تحريرات لتحويل ref[:i] إلى hyp[:j]
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    op = [[""] * (m + 1) for _ in range(n + 1)]

    for i in range(n + 1):
        dp[i][0] = i
        op[i][0] = "del"
    for j in range(m + 1):
        dp[0][j] = j
        op[0][j] = "ins"
    op[0][0] = ""

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if ref[i - 1] == hyp[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
                op[i][j] = "match"
            else:
                sub = dp[i - 1][j - 1] + 1
                delete = dp[i - 1][j] + 1
                insert = dp[i][j - 1] + 1
                best = min(sub, delete, insert)
                dp[i][j] = best
                if best == sub:
                    op[i][j] = "sub"
                elif best == delete:
                    op[i][j] = "del"
                else:
                    op[i][j] = "ins"

    # تتبع العمليات
    subs = dels = ins = 0
    i, j = n, m
    while i > 0 or j > 0:
        action = op[i][j]
        if action == "match":
            i -= 1
            j -= 1
        elif action == "sub":
            subs += 1
            i -= 1
            j -= 1
        elif action == "del":
            dels += 1
            i -= 1
        elif action == "ins":
            ins += 1
            j -= 1
        else:
            break

    return {"substitutions": subs, "deletions": dels, "insertions": ins}


def compute_wer(
    reference: str,
    hypothesis: str,
    *,
    normalize: bool = True,
) -> ErrorRateResult:
    """حساب WER بين نصين.

    Args:
        reference: النص المرجعي.
        hypothesis: نص التفريغ.
        normalize: تطبيق normalize_for_asr قبل المقارنة (موصى به للعربية).

    Returns:
        ErrorRateResult.
    """
    ref_text = normalize_for_asr(reference) if normalize else reference
    hyp_text = normalize_for_asr(hypothesis) if normalize else hypothesis

    ref_words = ref_text.split()
    hyp_words = hyp_text.split()

    if not ref_words:
        return ErrorRateResult(
            error_rate=1.0 if hyp_words else 0.0,
            substitutions=0,
            deletions=0,
            insertions=len(hyp_words),
            n_reference=0,
            n_hypothesis=len(hyp_words),
        )

    edits = _edit_distance(ref_words, hyp_words)
    total_errors = edits["substitutions"] + edits["deletions"] + edits["insertions"]
    error_rate = total_errors / len(ref_words)

    return ErrorRateResult(
        error_rate=error_rate,
        substitutions=edits["substitutions"],
        deletions=edits["deletions"],
        insertions=edits["insertions"],
        n_reference=len(ref_words),
        n_hypothesis=len(hyp_words),
    )


def compute_cer(
    reference: str,
    hypothesis: str,
    *,
    normalize: bool = True,
) -> ErrorRateResult:
    """حساب CER (على مستوى الحروف).

    Args:
        reference: النص المرجعي.
        hypothesis: نص التفريغ.
        normalize: تطبيق normalize_for_asr قبل المقارنة.
    """
    ref_text = normalize_for_asr(reference) if normalize else reference
    hyp_text = normalize_for_asr(hypothesis) if normalize else hypothesis

    # نتجاهل المسافات في الحساب على مستوى الحروف
    ref_chars = list(ref_text.replace(" ", ""))
    hyp_chars = list(hyp_text.replace(" ", ""))

    if not ref_chars:
        return ErrorRateResult(
            error_rate=1.0 if hyp_chars else 0.0,
            substitutions=0,
            deletions=0,
            insertions=len(hyp_chars),
            n_reference=0,
            n_hypothesis=len(hyp_chars),
        )

    edits = _edit_distance(ref_chars, hyp_chars)
    total_errors = edits["substitutions"] + edits["deletions"] + edits["insertions"]
    error_rate = total_errors / len(ref_chars)

    return ErrorRateResult(
        error_rate=error_rate,
        substitutions=edits["substitutions"],
        deletions=edits["deletions"],
        insertions=edits["insertions"],
        n_reference=len(ref_chars),
        n_hypothesis=len(hyp_chars),
    )


def speaker_attribution_accuracy(
    hypothesis_segments: list[dict],
    reference_segments: list[dict],
    *,
    frame_ms: int = 100,
) -> dict[str, float]:
    """نسبة الإطارات الزمنية التي أُسنِدت للمتحدث الصحيح.

    لكل إطار 100ms من زمن المكالمة:
    - نحدد المتحدث المرجعي.
    - نحدد المتحدث الذي اقترحه النظام.
    - إن تطابقا (بعد تطابق التسميات الأمثل) فالإطار صحيح.

    Args:
        hypothesis_segments: قائمة dict فيها start/end/speaker_id (أو speaker_name).
        reference_segments: قائمة dict مماثلة بالمرجع.
        frame_ms: حجم الإطار للمقارنة.

    Returns:
        قاموس فيه: accuracy, n_correct_frames, n_total_frames, mapping.
    """
    from src.diarization.metrics import _frame_labels, _optimal_label_mapping, _to_segments

    if not reference_segments:
        return {"accuracy": 0.0, "n_correct_frames": 0, "n_total_frames": 0, "mapping": {}}

    # نأخذ تسمية المتحدث من speaker_id إن وُجد، وإلا speaker_name
    def to_seg_tuples(items):
        result = []
        for it in items:
            label = it.get("speaker_id") or it.get("speaker_name") or it.get("speaker", "")
            result.append((float(it["start"]), float(it["end"]), str(label)))
        return result

    hyp = _to_segments(to_seg_tuples(hypothesis_segments))
    ref = _to_segments(to_seg_tuples(reference_segments))

    max_end = max(
        max((s.end for s in hyp), default=0.0),
        max(s.end for s in ref),
    )
    if max_end == 0:
        return {"accuracy": 0.0, "n_correct_frames": 0, "n_total_frames": 0, "mapping": {}}

    hyp_frames = _frame_labels(hyp, max_end, frame_ms)
    ref_frames = _frame_labels(ref, max_end, frame_ms)

    mapping = _optimal_label_mapping(hyp_frames, ref_frames)
    mapped_hyp = [mapping.get(l, l) for l in hyp_frames]

    n_total = sum(1 for r in ref_frames if r)
    n_correct = sum(
        1 for h, r in zip(mapped_hyp, ref_frames)
        if r and h == r
    )
    accuracy = n_correct / n_total if n_total > 0 else 0.0

    return {
        "accuracy": round(accuracy, 4),
        "n_correct_frames": n_correct,
        "n_total_frames": n_total,
        "mapping": mapping,
    }


def evaluate_transcript(
    reference_text: str,
    hypothesis_text: str,
    *,
    reference_segments: list[dict] | None = None,
    hypothesis_segments: list[dict] | None = None,
) -> dict:
    """تقييم كامل: WER + CER + Speaker Attribution.

    Args:
        reference_text: النص المرجعي (كل المكالمة).
        hypothesis_text: نص التفريغ الكامل.
        reference_segments: قطع المرجع مع متحدثيها (للحساب الكامل لـ SAA).
        hypothesis_segments: قطع التفريغ مع المتحدثين المُسندين.

    Returns:
        قاموس فيه: wer, cer, speaker_attribution, summary.
    """
    wer_result = compute_wer(reference_text, hypothesis_text)
    cer_result = compute_cer(reference_text, hypothesis_text)

    saa = None
    if reference_segments and hypothesis_segments:
        saa = speaker_attribution_accuracy(hypothesis_segments, reference_segments)

    return {
        "wer": wer_result.to_dict(),
        "cer": cer_result.to_dict(),
        "speaker_attribution": saa,
        "summary": {
            "wer_percent": round(wer_result.error_rate * 100, 2),
            "cer_percent": round(cer_result.error_rate * 100, 2),
            "saa_percent": round(saa["accuracy"] * 100, 2) if saa else None,
        },
    }
