"""اختبارات وحدة لـ src.diarization.embeddings."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pytest

from src.diarization.embeddings import (
    EmbeddingExtractor,
    MFCCBackend,
    cosine_similarity,
    cosine_similarity_matrix,
)

SR = 16000


def make_speech(duration: float, freq: float = 200, amp: float = 0.4, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    t = np.linspace(0, duration, int(SR * duration), endpoint=False)
    signal = (
        amp * np.sin(2 * np.pi * freq * t)
        + 0.5 * amp * np.sin(2 * np.pi * freq * 2 * t)
        + 0.005 * rng.standard_normal(len(t))
    )
    return signal.astype(np.float32)


class TestMFCCBackend:
    def test_embedding_shape(self):
        backend = MFCCBackend()
        audio = make_speech(1.0)
        emb = backend(audio, SR)
        assert emb.shape == (backend.embedding_dim,)

    def test_embedding_is_normalized(self):
        backend = MFCCBackend()
        audio = make_speech(1.0)
        emb = backend(audio, SR)
        norm = np.linalg.norm(emb)
        assert abs(norm - 1.0) < 0.01

    def test_empty_audio_returns_zero(self):
        backend = MFCCBackend()
        emb = backend(np.array([], dtype=np.float32), SR)
        assert emb.shape == (backend.embedding_dim,)
        assert np.linalg.norm(emb) == 0

    def test_very_short_audio_returns_zero(self):
        backend = MFCCBackend()
        emb = backend(make_speech(0.05), SR)  # 50ms < 100ms
        assert np.linalg.norm(emb) == 0

    def test_similar_speakers_have_similar_embeddings(self):
        """متحدث واحد (نفس التردد) في عينتين مختلفتين → تشابه عالٍ."""
        backend = MFCCBackend()
        emb1 = backend(make_speech(1.5, freq=200, seed=1), SR)
        emb2 = backend(make_speech(1.5, freq=200, seed=2), SR)
        sim = cosine_similarity(emb1, emb2)
        assert sim > 0.9, f"التشابه {sim:.3f} منخفض لمتحدث واحد"

    def test_different_speakers_have_distinct_embeddings(self):
        """تردّدات مختلفة → بصمات مختلفة."""
        backend = MFCCBackend()
        emb_low = backend(make_speech(1.5, freq=120, seed=1), SR)
        emb_high = backend(make_speech(1.5, freq=400, seed=1), SR)
        sim = cosine_similarity(emb_low, emb_high)
        # ليس بالضرورة 0، لكن أقل من نفس المتحدث
        same_emb1 = backend(make_speech(1.5, freq=120, seed=1), SR)
        same_emb2 = backend(make_speech(1.5, freq=120, seed=2), SR)
        same_sim = cosine_similarity(same_emb1, same_emb2)
        assert sim < same_sim, "بصمات مختلفة ليست أقل تشابهاً من نفس المتحدث"


class TestEmbeddingExtractor:
    def test_default_method_is_mfcc(self):
        ex = EmbeddingExtractor()
        assert ex.method == "mfcc"

    def test_unknown_method_raises(self):
        with pytest.raises(ValueError):
            EmbeddingExtractor(method="invented")  # type: ignore

    def test_extract_batch(self):
        ex = EmbeddingExtractor("mfcc")
        audio = make_speech(3.0)
        segments = [(0.0, 1.0), (1.0, 2.0), (2.0, 3.0)]
        embs = ex.extract_batch(audio, SR, segments)
        assert embs.shape == (3, ex.embedding_dim)

    def test_extract_batch_empty(self):
        ex = EmbeddingExtractor("mfcc")
        embs = ex.extract_batch(make_speech(1.0), SR, [])
        assert embs.shape == (0, ex.embedding_dim)


class TestCosineSimilarity:
    def test_identical_vectors(self):
        v = np.array([0.6, 0.8], dtype=np.float32)
        assert abs(cosine_similarity(v, v) - 1.0) < 1e-6

    def test_orthogonal_vectors(self):
        v1 = np.array([1.0, 0.0], dtype=np.float32)
        v2 = np.array([0.0, 1.0], dtype=np.float32)
        assert abs(cosine_similarity(v1, v2)) < 1e-6

    def test_empty_vector(self):
        assert cosine_similarity(np.array([]), np.array([1.0, 2.0])) == 0.0


class TestCosineSimilarityMatrix:
    def test_diagonal_is_one_for_normalized(self):
        rng = np.random.default_rng(42)
        embs = rng.standard_normal((5, 10)).astype(np.float32)
        embs = embs / np.linalg.norm(embs, axis=1, keepdims=True)
        mat = cosine_similarity_matrix(embs)
        np.testing.assert_allclose(np.diag(mat), 1.0, atol=1e-5)

    def test_matrix_is_symmetric(self):
        rng = np.random.default_rng(42)
        embs = rng.standard_normal((4, 8)).astype(np.float32)
        embs = embs / np.linalg.norm(embs, axis=1, keepdims=True)
        mat = cosine_similarity_matrix(embs)
        np.testing.assert_allclose(mat, mat.T, atol=1e-6)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
