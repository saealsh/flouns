"""قياس جودة المقاطع الصوتية: SNR، RMS، نسبة الصمت، التشبع.

كل مقياس بسيط مفهوم:
- RMS: متوسط طاقة الإشارة. منخفض جداً = صامت، عالٍ جداً = ضوضاء.
- SNR: نسبة الإشارة للضوضاء بـ dB. أعلى = أنظف.
- silence_ratio: نسبة الإطارات الصامتة من المجموع.
- clipping_ratio: نسبة العيّنات المشبعة (تتجاوز ±0.99).

استخدام:
    from src.audio.quality import compute_quality_metrics

    metrics = compute_quality_metrics(audio, sr)
    if metrics["passes"]:
        print("جودة مقبولة")
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np


@dataclass
class QualityMetrics:
    """مؤشرات جودة المقطع الصوتي."""

    duration_sec: float
    rms: float                  # 0..1 — متوسط الطاقة
    rms_db: float               # نفس القيمة بـ dB (-inf..0)
    snr_db: float               # نسبة الإشارة للضوضاء
    silence_ratio: float        # 0..1
    clipping_ratio: float       # 0..1 — نسبة العيّنات المشبعة
    dynamic_range_db: float     # الفرق بين أعلى وأقل قمم
    passes: bool                # هل الملف اجتاز عتبات الجودة؟
    issues: list[str]           # قائمة المشاكل المكتشفة

    def to_dict(self) -> dict:
        return asdict(self)


def _to_db(x: float, eps: float = 1e-10) -> float:
    """تحويل قيمة خطية لـ dB. يحمي من log(0)."""
    return 20.0 * np.log10(max(x, eps))


def compute_rms(audio: np.ndarray) -> tuple[float, float]:
    """حساب RMS (طاقة الإشارة) خطياً وبـ dB.

    Returns:
        (rms_linear, rms_db)
    """
    if audio.size == 0:
        return 0.0, float("-inf")
    rms = float(np.sqrt(np.mean(audio.astype(np.float64) ** 2)))
    return rms, _to_db(rms)


def compute_silence_ratio(
    audio: np.ndarray,
    sr: int,
    frame_ms: int = 30,
    threshold_db: float = -40.0,
) -> float:
    """حساب نسبة الإطارات الصامتة.

    نقسّم الصوت لإطارات صغيرة (30ms عادة)، ونحسب RMS لكل إطار.
    الإطار «صامت» إذا كان RMS أقل من threshold_db (افتراضياً -40 dB).

    Args:
        audio: مصفوفة الصوت.
        sr: تردد العينة.
        frame_ms: طول الإطار بالمللي ثانية.
        threshold_db: عتبة الصمت بـ dB.

    Returns:
        نسبة 0..1 من الإطارات الصامتة.
    """
    if audio.size == 0:
        return 1.0

    frame_size = int(sr * frame_ms / 1000)
    if frame_size == 0 or audio.size < frame_size:
        return 0.0

    n_frames = audio.size // frame_size
    if n_frames == 0:
        return 0.0

    frames = audio[: n_frames * frame_size].reshape(n_frames, frame_size)
    frame_rms = np.sqrt(np.mean(frames.astype(np.float64) ** 2, axis=1))
    frame_db = 20.0 * np.log10(np.maximum(frame_rms, 1e-10))

    silent = (frame_db < threshold_db).sum()
    return float(silent / n_frames)


def compute_snr_db(
    audio: np.ndarray,
    sr: int,
    frame_ms: int = 30,
    silence_threshold_db: float = -40.0,
) -> float:
    """تقدير نسبة الإشارة للضوضاء (SNR) بطريقة الإطارات.

    الفكرة: إطارات الكلام عالية الطاقة، إطارات الصمت تحتوي ضوضاء الخلفية.
    SNR ≈ متوسط طاقة إطارات الكلام - متوسط طاقة إطارات الصمت.

    Returns:
        SNR بـ dB (أعلى = أنظف). يُرجع +∞ إن لم توجد إطارات صمت.
    """
    if audio.size == 0:
        return 0.0

    frame_size = int(sr * frame_ms / 1000)
    if audio.size < frame_size * 2:
        return 0.0

    n_frames = audio.size // frame_size
    frames = audio[: n_frames * frame_size].reshape(n_frames, frame_size)
    frame_rms = np.sqrt(np.mean(frames.astype(np.float64) ** 2, axis=1))
    frame_db = 20.0 * np.log10(np.maximum(frame_rms, 1e-10))

    speech_mask = frame_db >= silence_threshold_db
    silence_mask = ~speech_mask

    if not speech_mask.any():
        return 0.0  # كل شيء صمت
    if not silence_mask.any():
        # لا توجد إطارات صمت — نعتمد على المئوية 10 الأدنى كتقدير لأرضية الضوضاء
        # هذا منطقي: حتى الإشارات الكلامية المتواصلة فيها هدوء بين المقاطع
        floor_rms = np.percentile(frame_rms, 10)
        speech_rms = np.percentile(frame_rms, 75)  # الأعلى = الكلام الفعلي
        if floor_rms < 1e-10 or speech_rms <= floor_rms:
            return 60.0
        return float(20.0 * np.log10(speech_rms / floor_rms))

    speech_rms = frame_rms[speech_mask].mean()
    noise_rms = frame_rms[silence_mask].mean()

    if noise_rms < 1e-10:
        return 60.0

    return float(20.0 * np.log10(speech_rms / noise_rms))


def compute_clipping_ratio(audio: np.ndarray, threshold: float = 0.99) -> float:
    """حساب نسبة العينات المشبعة.

    التشبع (clipping) يحدث عندما يتجاوز السعة ±1.0، وتُقصّ.
    نسبة عالية = تشويه في التسجيل، نص ASR سيكون رديئاً.

    Returns:
        نسبة 0..1.
    """
    if audio.size == 0:
        return 0.0
    clipped = (np.abs(audio) >= threshold).sum()
    return float(clipped / audio.size)


def compute_dynamic_range_db(audio: np.ndarray) -> float:
    """الفرق بين أعلى قمة وأقل قمة غير صامتة.

    نطاق ديناميكي ضيق = إشارة مضغوطة أو ضوضاء.
    """
    if audio.size == 0:
        return 0.0
    abs_audio = np.abs(audio)
    peak = abs_audio.max()
    # نأخذ المئوية العاشرة بدل الحد الأدنى الفعلي (أكثر استقراراً)
    floor = np.percentile(abs_audio, 10)
    return float(_to_db(peak) - _to_db(floor))


def compute_quality_metrics(
    audio: np.ndarray,
    sr: int,
    *,
    min_snr_db: float = 10.0,
    max_silence_ratio: float = 0.5,
    min_rms: float = 0.001,
    max_clipping_ratio: float = 0.01,
) -> QualityMetrics:
    """حساب كل المؤشرات وتقييم ما إذا كان المقطع جيداً.

    Args:
        audio: مصفوفة الصوت (mono، float).
        sr: تردد العينة.
        min_snr_db: حد أدنى مقبول لـ SNR.
        max_silence_ratio: حد أقصى مقبول لنسبة الصمت.
        min_rms: حد أدنى مقبول لـ RMS (لتمييز الملفات الصامتة).
        max_clipping_ratio: حد أقصى مقبول للتشبع.

    Returns:
        QualityMetrics فيه كل المؤشرات + قائمة المشاكل.
    """
    duration = audio.size / sr if sr > 0 else 0.0
    rms_lin, rms_db = compute_rms(audio)
    silence = compute_silence_ratio(audio, sr)
    snr = compute_snr_db(audio, sr)
    clipping = compute_clipping_ratio(audio)
    dyn_range = compute_dynamic_range_db(audio)

    issues: list[str] = []
    if rms_lin < min_rms:
        issues.append(f"RMS منخفض جداً ({rms_db:.1f} dB) — الملف صامت تقريباً")
    if snr < min_snr_db:
        issues.append(f"SNR منخفض ({snr:.1f} dB < {min_snr_db}) — ضوضاء مرتفعة")
    if silence > max_silence_ratio:
        issues.append(
            f"نسبة الصمت {silence:.0%} > {max_silence_ratio:.0%} — معظم الملف صمت"
        )
    if clipping > max_clipping_ratio:
        issues.append(
            f"تشبع مرتفع ({clipping:.2%}) — تشويه في التسجيل"
        )

    return QualityMetrics(
        duration_sec=round(duration, 3),
        rms=round(rms_lin, 6),
        rms_db=round(rms_db, 2),
        snr_db=round(snr, 2),
        silence_ratio=round(silence, 4),
        clipping_ratio=round(clipping, 6),
        dynamic_range_db=round(dyn_range, 2),
        passes=len(issues) == 0,
        issues=issues,
    )
