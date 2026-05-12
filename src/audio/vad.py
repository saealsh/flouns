"""كشف نشاط الصوت (Voice Activity Detection — VAD).

نوفّر طريقتين متكاملتين:

1. **Energy-based VAD** (مدمج، بدون تبعيات): يكشف الكلام بناءً على RMS لكل إطار.
   سريع، لكن قد يخطئ في الضوضاء العالية المستقرة.

2. **Silero VAD** (نموذج عميق، اختياري): يحمَّل عند الطلب من PyTorch Hub.
   أدق، يحتاج تنزيل أول مرة (~17MB).

كلتا الطريقتين تُرجعان قائمة من segments بصيغة موحدة:
    [(start_sec, end_sec), ...]

استخدام:
    from src.audio.vad import detect_speech_segments

    segments = detect_speech_segments(audio, sr, method="energy")
    for start, end in segments:
        print(f"كلام من {start:.2f}ث إلى {end:.2f}ث")
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

from src.utils.logging import get_logger

log = get_logger(__name__)

VADMethod = Literal["energy", "silero"]


@dataclass(frozen=True)
class SpeechSegment:
    """قطعة كلام: نطاق زمني واحد متواصل."""

    start_sec: float
    end_sec: float

    @property
    def duration_sec(self) -> float:
        return self.end_sec - self.start_sec

    def to_tuple(self) -> tuple[float, float]:
        return (round(self.start_sec, 3), round(self.end_sec, 3))


def _frames_to_segments(
    is_speech: np.ndarray,
    frame_size: int,
    sr: int,
    min_speech_ms: int = 250,
    min_silence_ms: int = 100,
) -> list[SpeechSegment]:
    """تحويل قناع إطارات منطقي إلى segments زمنية مدمجة.

    منطق الدمج:
    - الإطارات المتجاورة المُعلَّمة كلاماً تُجمع.
    - فجوات الصمت الأقصر من min_silence_ms تُتجاهل (تُدمَج).
    - segments الأقصر من min_speech_ms تُحذف بعد الدمج.

    Args:
        is_speech: مصفوفة منطقية بطول عدد الإطارات.
        frame_size: عدد العينات في الإطار.
        sr: تردد العينة.
        min_speech_ms: أدنى طول مقبول لقطعة كلام.
        min_silence_ms: أقصر فجوة صمت تُعتبر فصلاً حقيقياً.

    Returns:
        قائمة SpeechSegment.
    """
    if not is_speech.any():
        return []

    frame_sec = frame_size / sr
    min_speech_frames = max(1, int(min_speech_ms / 1000 / frame_sec))
    min_silence_frames = max(1, int(min_silence_ms / 1000 / frame_sec))

    # اعثر على نقاط التحوّل
    diff = np.diff(is_speech.astype(int), prepend=0, append=0)
    starts = np.where(diff == 1)[0]
    ends = np.where(diff == -1)[0]

    # ادمج segments الفاصل بينها صمت قصير
    merged: list[tuple[int, int]] = []
    for s, e in zip(starts, ends, strict=True):
        if merged and (s - merged[-1][1]) < min_silence_frames:
            merged[-1] = (merged[-1][0], e)
        else:
            merged.append((s, e))

    # احذف القصيرة جداً
    segments = [
        SpeechSegment(
            start_sec=s * frame_sec,
            end_sec=e * frame_sec,
        )
        for s, e in merged
        if (e - s) >= min_speech_frames
    ]

    return segments


def energy_vad(
    audio: np.ndarray,
    sr: int,
    *,
    frame_ms: int = 30,
    threshold_db: float = -35.0,
    min_speech_ms: int = 250,
    min_silence_ms: int = 200,
    adaptive: bool = True,
) -> list[SpeechSegment]:
    """VAD بسيط مبني على طاقة الإطارات.

    آلية adaptive: إذا فُعِّلت، نضبط threshold_db تلقائياً بناءً على توزيع الطاقة
    الفعلية للملف (نأخذ المئوية 25 + 6dB). أدق على ملفات بأنواع ضوضاء مختلفة.

    Args:
        audio: مصفوفة الصوت mono float.
        sr: تردد العينة.
        frame_ms: طول الإطار بالـ ms.
        threshold_db: عتبة الطاقة بـ dB (إذا adaptive=False).
        min_speech_ms: أدنى طول مقبول لقطعة كلام.
        min_silence_ms: أدنى فاصل صمت يفصل قطعتين.
        adaptive: ضبط العتبة تلقائياً.

    Returns:
        قائمة SpeechSegment.
    """
    if audio.size == 0:
        return []

    frame_size = int(sr * frame_ms / 1000)
    if audio.size < frame_size:
        return []

    n_frames = audio.size // frame_size
    frames = audio[: n_frames * frame_size].reshape(n_frames, frame_size)
    frame_rms = np.sqrt(np.mean(frames.astype(np.float64) ** 2, axis=1))
    frame_db = 20.0 * np.log10(np.maximum(frame_rms, 1e-10))

    if adaptive:
        # العتبة التكيّفية: نتعامل مع حالتين متطرفتين:
        #   (أ) ملف فيه صمت وكلام معاً → percentile 25 ≈ أرضية الضوضاء
        #   (ب) ملف كله كلام (لا صمت) → percentile 25 قريب من قمة الإشارة
        # الحل: نأخذ الأدنى بين «أرضية + 6dB» والعتبة الثابتة threshold_db
        noise_floor = np.percentile(frame_db, 25)
        peak_db = np.percentile(frame_db, 95)
        dynamic_range = peak_db - noise_floor

        if dynamic_range < 10.0:
            # ملف رتيب (كله كلام أو كله صمت) → استخدم العتبة الثابتة
            effective_threshold = threshold_db
        else:
            # عتبة بين أرضية + 6dB والثابت، أيهما أقل
            effective_threshold = min(noise_floor + 6.0, threshold_db)
        log.debug(
            f"VAD adaptive: floor={noise_floor:.1f}, peak={peak_db:.1f}, "
            f"threshold={effective_threshold:.1f} dB"
        )
    else:
        effective_threshold = threshold_db

    is_speech = frame_db >= effective_threshold

    return _frames_to_segments(
        is_speech,
        frame_size,
        sr,
        min_speech_ms=min_speech_ms,
        min_silence_ms=min_silence_ms,
    )


def silero_vad(
    audio: np.ndarray,
    sr: int,
    *,
    threshold: float = 0.5,
    min_speech_ms: int = 250,
    min_silence_ms: int = 200,
) -> list[SpeechSegment]:
    """VAD بنموذج Silero العميق.

    يتطلّب: pip install torch
    التحميل من PyTorch Hub أول مرة (يُخزَّن في ~/.cache).

    Args:
        audio: مصفوفة الصوت (mono، float، 16kHz أو 8kHz).
        sr: 8000 أو 16000.
        threshold: 0..1 — احتمال الكلام لاعتبار الإطار كلاماً.
        min_speech_ms: أدنى طول قطعة.
        min_silence_ms: أدنى فاصل.

    Returns:
        قائمة SpeechSegment.
    """
    try:
        import torch
    except ImportError as e:
        raise ImportError(
            "Silero VAD يحتاج torch. ثبّت: pip install torch"
        ) from e

    if sr not in (8000, 16000):
        raise ValueError(f"Silero VAD يدعم 8kHz أو 16kHz فقط. أعطيت: {sr}")

    log.info("تحميل Silero VAD (يحتاج اتصال أول مرة)...")
    model, utils = torch.hub.load(
        repo_or_dir="snakers4/silero-vad",
        model="silero_vad",
        force_reload=False,
        trust_repo=True,
    )
    get_speech_timestamps = utils[0]

    audio_tensor = torch.from_numpy(audio.astype(np.float32))
    timestamps = get_speech_timestamps(
        audio_tensor,
        model,
        threshold=threshold,
        sampling_rate=sr,
        min_speech_duration_ms=min_speech_ms,
        min_silence_duration_ms=min_silence_ms,
    )

    return [
        SpeechSegment(
            start_sec=t["start"] / sr,
            end_sec=t["end"] / sr,
        )
        for t in timestamps
    ]


def detect_speech_segments(
    audio: np.ndarray,
    sr: int,
    method: VADMethod = "energy",
    **kwargs,
) -> list[SpeechSegment]:
    """واجهة موحّدة لكلتا الطريقتين.

    Args:
        audio: مصفوفة الصوت.
        sr: تردد العينة.
        method: "energy" (بدون تبعيات) أو "silero" (يحتاج torch).
        **kwargs: تُمرَّر للدالة المختارة.

    Returns:
        قائمة SpeechSegment.
    """
    if method == "energy":
        return energy_vad(audio, sr, **kwargs)
    elif method == "silero":
        return silero_vad(audio, sr, **kwargs)
    else:
        raise ValueError(f"طريقة VAD غير معروفة: {method}")


def total_speech_duration(segments: list[SpeechSegment]) -> float:
    """مجموع مدد الكلام (مفيد للإحصائيات)."""
    return sum(s.duration_sec for s in segments)


def extract_speech_audio(
    audio: np.ndarray,
    sr: int,
    segments: list[SpeechSegment],
) -> np.ndarray:
    """تجميع كل قطع الكلام في مصفوفة واحدة (إزالة الصمت).

    مفيد لتقليل حجم الملفات قبل تمريرها لـ ASR.
    """
    if not segments:
        return np.array([], dtype=audio.dtype)

    parts = []
    for seg in segments:
        start_idx = int(seg.start_sec * sr)
        end_idx = int(seg.end_sec * sr)
        parts.append(audio[start_idx:end_idx])
    return np.concatenate(parts)
