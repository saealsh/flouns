"""استخلاص البصمات الصوتية (Speaker Embeddings) لكل قطعة كلام.

يوفّر طبقتين:

1. **MFCC-based** (مدمج، بدون torch):
   متجه من 40 بُعد يلتقط MFCC + الإحصاءات (mean, std, delta).
   كفاية للتجميع البسيط، ليس بدقة النماذج العميقة.

2. **SpeechBrain ECAPA-TDNN** (اختياري):
   متجه 192 بُعد، حالة الفن مفتوحة المصدر.
   pip install speechbrain torch

3. **pyannote** (اختياري):
   متجه 256 بُعد، يحتاج HF token لقبول شروط النموذج.
   pip install pyannote.audio

كل البصمات تُطبَّع لـ L2 = 1، فالتشابه = cosine = dot product.

استخدام:
    from src.diarization.embeddings import EmbeddingExtractor

    extractor = EmbeddingExtractor(method="mfcc")
    emb = extractor.extract(audio_segment, sr=16000)  # ndarray (D,)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

import numpy as np

from src.utils.logging import get_logger

log = get_logger(__name__)

EmbeddingMethod = Literal["mfcc", "speechbrain", "pyannote"]


class EmbeddingBackend(Protocol):
    """واجهة موحّدة لأي طريقة استخلاص بصمة."""

    embedding_dim: int

    def __call__(self, audio: np.ndarray, sr: int) -> np.ndarray:
        ...


@dataclass
class MFCCBackend:
    """بصمة مبنية على MFCC + الإحصاءات.

    لكل قطعة:
    1. حساب MFCC لكل إطار (13 معامل افتراضياً).
    2. حساب delta و delta-delta.
    3. تجميع: متوسط + انحراف معياري لكل بُعد.
    4. النتيجة: 13 * 3 * 2 = 78 بُعد.

    سريع جداً، لا يحتاج تدريباً ولا GPU، يلتقط جوهر طيف صوت المتحدث.
    """

    n_mfcc: int = 13
    embedding_dim: int = 78  # 13 * 3 (mfcc+d+dd) * 2 (mean+std)

    def __call__(self, audio: np.ndarray, sr: int) -> np.ndarray:
        try:
            import librosa
        except ImportError as e:
            raise ImportError("MFCC backend يحتاج librosa") from e

        if audio.size == 0 or audio.size < int(sr * 0.1):
            # قطعة أقصر من 100ms → بصمة صفرية (تُتجاهل لاحقاً في التجميع)
            return np.zeros(self.embedding_dim, dtype=np.float32)

        # MFCC الأساسية
        mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=self.n_mfcc)
        # Delta و Delta-Delta
        delta = librosa.feature.delta(mfcc)
        delta2 = librosa.feature.delta(mfcc, order=2)

        # تجميع: mean + std على البُعد الزمني
        feats = np.concatenate([mfcc, delta, delta2], axis=0)  # (39, T)
        mean = feats.mean(axis=1)
        std = feats.std(axis=1)
        emb = np.concatenate([mean, std]).astype(np.float32)  # (78,)

        # L2 normalize
        norm = np.linalg.norm(emb)
        if norm > 1e-8:
            emb = emb / norm
        return emb


@dataclass
class SpeechBrainBackend:
    """بصمة ECAPA-TDNN من SpeechBrain.

    أكثر دقة من MFCC بفارق كبير. النموذج يُحمَّل أول مرة (~80MB).

    التبعيات:
        pip install speechbrain torch torchaudio
    """

    embedding_dim: int = 192
    _model = None

    def _load(self):
        if self._model is not None:
            return
        try:
            from speechbrain.inference.speaker import EncoderClassifier
        except ImportError as e:
            raise ImportError(
                "SpeechBrain غير مثبّت. ثبّت:\n"
                "  pip install speechbrain torch torchaudio"
            ) from e

        log.info("تحميل نموذج SpeechBrain ECAPA-TDNN (أول مرة فقط)...")
        self._model = EncoderClassifier.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb",
            savedir="models/spkrec-ecapa",
        )

    def __call__(self, audio: np.ndarray, sr: int) -> np.ndarray:
        import torch

        self._load()
        if audio.size == 0 or audio.size < int(sr * 0.5):
            return np.zeros(self.embedding_dim, dtype=np.float32)

        if sr != 16000:
            try:
                import librosa
                audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)
            except ImportError as e:
                raise ImportError("إعادة العيّنة تحتاج librosa") from e

        tensor = torch.from_numpy(audio.astype(np.float32)).unsqueeze(0)
        with torch.no_grad():
            emb = self._model.encode_batch(tensor).squeeze().cpu().numpy()  # type: ignore

        norm = np.linalg.norm(emb)
        if norm > 1e-8:
            emb = emb / norm
        return emb.astype(np.float32)


class EmbeddingExtractor:
    """واجهة موحّدة تختار الـ backend المطلوب."""

    BACKENDS: dict[str, type[EmbeddingBackend]] = {
        "mfcc": MFCCBackend,
        "speechbrain": SpeechBrainBackend,
    }

    def __init__(self, method: EmbeddingMethod = "mfcc", **kwargs):
        if method not in self.BACKENDS:
            raise ValueError(
                f"طريقة غير معروفة: {method}. "
                f"المتاح: {list(self.BACKENDS)}"
            )
        self.method = method
        self.backend = self.BACKENDS[method](**kwargs)

    @property
    def embedding_dim(self) -> int:
        return self.backend.embedding_dim

    def extract(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """استخلاص بصمة لقطعة صوتية واحدة.

        Args:
            audio: مصفوفة الصوت mono float.
            sr: تردد العينة.

        Returns:
            متجه البصمة (مُطبَّع L2)، شكله (embedding_dim,).
        """
        return self.backend(audio, sr)

    def extract_batch(
        self,
        audio: np.ndarray,
        sr: int,
        segments: list[tuple[float, float]],
    ) -> np.ndarray:
        """استخلاص بصمات لعدة قطع زمنية من نفس الملف.

        Args:
            audio: الملف الصوتي الكامل.
            sr: تردد العينة.
            segments: قائمة (start_sec, end_sec).

        Returns:
            مصفوفة بشكل (n_segments, embedding_dim).
        """
        if not segments:
            return np.empty((0, self.embedding_dim), dtype=np.float32)

        embeddings = np.zeros((len(segments), self.embedding_dim), dtype=np.float32)
        for i, (start, end) in enumerate(segments):
            start_idx = int(start * sr)
            end_idx = int(end * sr)
            chunk = audio[start_idx:end_idx]
            embeddings[i] = self.extract(chunk, sr)
        return embeddings


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """مسافة cosine بين متجهين (L2-normalized → dot product مباشرة).

    Returns:
        قيمة في [-1, 1]. 1 = متطابقان، 0 = غير مترابطين، -1 = معاكسان.
    """
    if a.size == 0 or b.size == 0:
        return 0.0
    return float(np.dot(a, b))


def cosine_similarity_matrix(embeddings: np.ndarray) -> np.ndarray:
    """مصفوفة تشابه cosine بين كل أزواج البصمات.

    Args:
        embeddings: شكل (N, D).

    Returns:
        مصفوفة (N, N) بقيم [-1, 1].
    """
    if embeddings.size == 0:
        return np.empty((0, 0), dtype=np.float32)
    # بما أن البصمات L2-normalized، الـ dot product = cosine
    return embeddings @ embeddings.T
