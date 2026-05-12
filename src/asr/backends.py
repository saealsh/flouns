"""تفريغ تلقائي للكلام عبر backends متعددة.

نوفّر ثلاث طبقات:

1. **Mock backend** (مدمج، بدون تبعيات):
   ينتج تفريغاً وهمياً قابلاً للتنبّؤ. مفيد للاختبارات وبناء الـ pipeline
   قبل تنزيل نماذج ضخمة.

2. **faster-whisper backend** (موصى به للإنتاج):
   - يستخدم CTranslate2 لتسريع Whisper بـ 4-5×.
   - يدعم GPU وCPU.
   - أصغر حجماً من openai-whisper الأصلي.
   - pip install faster-whisper

3. **openai-whisper backend** (احتياطي):
   - النسخة الرسمية، أقل سرعة لكن مرجع.
   - pip install openai-whisper

كل backend يُرجع TranscriptionResult بنفس البنية، فالـ pipeline لا يعرف الفرق.

استخدام:
    from src.asr.backends import get_backend

    asr = get_backend("faster-whisper", model_size="large-v3")
    result = asr.transcribe(audio, sr=16000, language="ar")
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal, Protocol

import numpy as np

from src.utils.logging import get_logger

log = get_logger(__name__)

ASRBackendName = Literal["mock", "faster-whisper", "openai-whisper"]


@dataclass
class WordTiming:
    """كلمة واحدة بطابع زمني وثقة."""

    word: str
    start: float
    end: float
    confidence: float = 1.0

    def to_dict(self) -> dict:
        return {
            "word": self.word,
            "start": round(self.start, 3),
            "end": round(self.end, 3),
            "confidence": round(self.confidence, 4),
        }


@dataclass
class TranscriptionSegment:
    """قطعة تفريغ: نص + طابع زمني + كلمات."""

    start: float
    end: float
    text: str
    words: list[WordTiming] = field(default_factory=list)
    avg_confidence: float = 1.0
    language: str = "ar"
    no_speech_prob: float = 0.0

    @property
    def duration(self) -> float:
        return self.end - self.start

    def to_dict(self) -> dict:
        return {
            "start": round(self.start, 3),
            "end": round(self.end, 3),
            "text": self.text,
            "words": [w.to_dict() for w in self.words],
            "avg_confidence": round(self.avg_confidence, 4),
            "language": self.language,
            "no_speech_prob": round(self.no_speech_prob, 4),
        }


@dataclass
class TranscriptionResult:
    """نتيجة تفريغ كاملة لملف صوتي."""

    segments: list[TranscriptionSegment] = field(default_factory=list)
    language: str = "ar"
    language_probability: float = 1.0
    duration_sec: float = 0.0
    model_info: dict = field(default_factory=dict)

    @property
    def full_text(self) -> str:
        return " ".join(s.text for s in self.segments).strip()

    @property
    def avg_confidence(self) -> float:
        if not self.segments:
            return 0.0
        total_dur = sum(s.duration for s in self.segments) or 1.0
        return sum(s.avg_confidence * s.duration for s in self.segments) / total_dur

    def to_dict(self) -> dict:
        return {
            "language": self.language,
            "language_probability": round(self.language_probability, 4),
            "duration_sec": round(self.duration_sec, 3),
            "full_text": self.full_text,
            "avg_confidence": round(self.avg_confidence, 4),
            "n_segments": len(self.segments),
            "segments": [s.to_dict() for s in self.segments],
            "model_info": self.model_info,
        }


class ASRBackend(Protocol):
    """واجهة موحّدة لأي backend تفريغ."""

    def transcribe(
        self,
        audio: np.ndarray,
        sr: int,
        language: str = "ar",
        **kwargs,
    ) -> TranscriptionResult:
        ...


# ═══════════════════════════════════════════════════════════════
# Mock Backend — للاختبارات والـ pipeline قبل تنزيل النماذج
# ═══════════════════════════════════════════════════════════════


class MockASRBackend:
    """backend وهمي ينتج تفريغاً متوقّعاً لاختبار خط الأنابيب.

    يقسّم الصوت لقطع segment_duration ثوانٍ ويُلصق نصاً مختلفاً بكل قطعة.
    يمكن تمرير `texts` لقائمة نصوص مخصّصة (تتكرر دائرياً إن لزم).
    """

    DEFAULT_TEXTS = [
        "هذا هو السطر الأول من التفريغ الاختباري",
        "والآن نختبر السطر الثاني بكلمات مختلفة",
        "السطر الثالث للتأكد من تنوع المخرجات",
        "نتابع بسطر رابع لتغطية مكالمة أطول",
        "وهذا السطر الخامس قبل أن نعود للبداية",
    ]

    def __init__(self, mock_text: str | None = None, texts: list[str] | None = None):
        if texts is not None:
            self.texts = texts
        elif mock_text is not None:
            self.texts = [mock_text]
        else:
            self.texts = list(self.DEFAULT_TEXTS)

    def transcribe(
        self,
        audio: np.ndarray,
        sr: int,
        language: str = "ar",
        segment_duration: float = 3.0,
        **kwargs,
    ) -> TranscriptionResult:
        duration = audio.size / sr if sr > 0 else 0.0
        if duration == 0:
            return TranscriptionResult(language=language, model_info={"backend": "mock"})

        segments = []
        cursor = 0.0
        seg_idx = 0
        while cursor < duration:
            end = min(cursor + segment_duration, duration)
            text = self.texts[seg_idx % len(self.texts)]
            words = self._make_words(text, cursor, end)
            segments.append(
                TranscriptionSegment(
                    start=cursor,
                    end=end,
                    text=text,
                    words=words,
                    avg_confidence=0.85,
                    language=language,
                    no_speech_prob=0.05,
                )
            )
            cursor = end
            seg_idx += 1

        return TranscriptionResult(
            segments=segments,
            language=language,
            language_probability=1.0,
            duration_sec=duration,
            model_info={"backend": "mock", "n_unique_texts": len(self.texts)},
        )

    @staticmethod
    def _make_words(text: str, start: float, end: float) -> list[WordTiming]:
        words = text.split()
        if not words:
            return []
        per_word = (end - start) / len(words)
        return [
            WordTiming(
                word=w,
                start=start + i * per_word,
                end=start + (i + 1) * per_word,
                confidence=0.85,
            )
            for i, w in enumerate(words)
        ]


# ═══════════════════════════════════════════════════════════════
# faster-whisper Backend — الإنتاجي
# ═══════════════════════════════════════════════════════════════


class FasterWhisperBackend:
    """backend مبني على faster-whisper.

    استخدام:
        backend = FasterWhisperBackend(model_size="large-v3", device="cpu")
        result = backend.transcribe(audio, sr=16000, language="ar")

    أحجام النماذج:
        tiny     → 39M معاملات، سريع جداً، دقة منخفضة.
        base     → 74M، توازن جيد للاختبار.
        small    → 244M، دقة معقولة.
        medium   → 769M.
        large-v3 → 1550M، أفضل دقة (موصى به للعربية).
    """

    def __init__(
        self,
        model_size: str = "large-v3",
        device: str = "auto",  # "cuda" | "cpu" | "auto"
        compute_type: str = "default",  # "default" | "int8" | "float16" | "float32"
        download_root: str | None = None,
    ):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.download_root = download_root
        self._model = None

    def _ensure_loaded(self):
        if self._model is not None:
            return

        try:
            from faster_whisper import WhisperModel
        except ImportError as e:
            raise ImportError(
                "faster-whisper غير مثبّت. ثبّت:\n"
                "  pip install faster-whisper"
            ) from e

        log.info(f"تحميل faster-whisper {self.model_size} على {self.device}...")
        self._model = WhisperModel(
            self.model_size,
            device=self.device,
            compute_type=self.compute_type,
            download_root=self.download_root,
        )
        log.info("اكتمل تحميل النموذج")

    def transcribe(
        self,
        audio: np.ndarray,
        sr: int,
        language: str = "ar",
        *,
        beam_size: int = 5,
        word_timestamps: bool = True,
        vad_filter: bool = False,  # نملك VAD منفصلاً، لا نكرّر
        initial_prompt: str | None = None,
        temperature: float = 0.0,
        **kwargs,
    ) -> TranscriptionResult:
        """تفريغ صوت في الذاكرة.

        Args:
            audio: مصفوفة الصوت mono float32.
            sr: تردد العينة (يجب أن يكون 16000).
            language: رمز اللغة ISO 639-1 (ar للعربية).
            beam_size: عرض شعاع البحث (5 توازن جيد).
            word_timestamps: استخراج طابع زمني لكل كلمة.
            vad_filter: تفعيل VAD الداخلي لـ Whisper (نتركه False).
            initial_prompt: prompt اختياري لتوجيه النموذج (أسماء، مصطلحات).
            temperature: 0 = أكثر حتمية. للتنوّع، استخدم 0.2-0.8.
        """
        self._ensure_loaded()

        if sr != 16000:
            log.warning(f"sr={sr} ليس 16000، النتائج قد تتدنّى")

        duration = audio.size / sr if sr > 0 else 0.0
        if duration < 0.1:
            return TranscriptionResult(
                language=language,
                duration_sec=duration,
                model_info={"backend": "faster-whisper", "model": self.model_size},
            )

        try:
            segments_iter, info = self._model.transcribe(  # type: ignore
                audio.astype(np.float32),
                language=language,
                beam_size=beam_size,
                word_timestamps=word_timestamps,
                vad_filter=vad_filter,
                initial_prompt=initial_prompt,
                temperature=temperature,
            )
        except Exception as e:
            log.error(f"فشل التفريغ: {e}")
            raise

        segments = []
        for seg in segments_iter:
            words = []
            if word_timestamps and getattr(seg, "words", None):
                for w in seg.words:
                    words.append(
                        WordTiming(
                            word=w.word.strip(),
                            start=float(w.start),
                            end=float(w.end),
                            confidence=float(getattr(w, "probability", 1.0)),
                        )
                    )

            # confidence على مستوى القطعة من avg_logprob
            avg_logprob = float(getattr(seg, "avg_logprob", 0.0))
            # تحويل logprob إلى احتمالية تقريبية
            avg_conf = float(np.exp(avg_logprob)) if avg_logprob < 0 else 1.0
            avg_conf = max(0.0, min(1.0, avg_conf))

            segments.append(
                TranscriptionSegment(
                    start=float(seg.start),
                    end=float(seg.end),
                    text=seg.text.strip(),
                    words=words,
                    avg_confidence=avg_conf,
                    language=language,
                    no_speech_prob=float(getattr(seg, "no_speech_prob", 0.0)),
                )
            )

        return TranscriptionResult(
            segments=segments,
            language=info.language,
            language_probability=float(info.language_probability),
            duration_sec=float(info.duration),
            model_info={
                "backend": "faster-whisper",
                "model": self.model_size,
                "device": self.device,
                "compute_type": self.compute_type,
            },
        )


# ═══════════════════════════════════════════════════════════════
# Factory
# ═══════════════════════════════════════════════════════════════


def get_backend(name: ASRBackendName = "mock", **kwargs) -> ASRBackend:
    """إنشاء backend بالاسم.

    Args:
        name: "mock" | "faster-whisper" | "openai-whisper".
        **kwargs: تُمرَّر للـ backend.

    Returns:
        backend جاهز.
    """
    if name == "mock":
        return MockASRBackend(**kwargs)
    if name == "faster-whisper":
        return FasterWhisperBackend(**kwargs)
    if name == "openai-whisper":
        # نتركها كملف منفصل لو احتجناها لاحقاً — لا حاجة لمضاعفة الكود
        raise NotImplementedError(
            "استخدم 'faster-whisper' بدلاً من 'openai-whisper' للأداء الأفضل"
        )
    raise ValueError(f"backend غير معروف: {name}")
