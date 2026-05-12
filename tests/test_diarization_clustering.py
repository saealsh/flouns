"""اختبارات وحدة لـ src.diarization.clustering."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pytest

from src.diarization.clustering import (
    agglomerative_cluster,
    cluster_embeddings,
    spectral_cluster,
)


def make_clustered_embeddings(
    n_clusters: int,
    n_per_cluster: int,
    dim: int = 78,
    noise: float = 0.05,
    seed: int = 42,
) -> tuple[np.ndarray, np.ndarray]:
    """توليد بصمات اصطناعية مع مجموعات واضحة (للاختبار).

    Returns:
        (embeddings, true_labels)
    """
    rng = np.random.default_rng(seed)
    centers = rng.standard_normal((n_clusters, dim))
    centers /= np.linalg.norm(centers, axis=1, keepdims=True)

    all_embs = []
    all_labels = []
    for cluster_idx, center in enumerate(centers):
        for _ in range(n_per_cluster):
            sample = center + noise * rng.standard_normal(dim)
            sample /= np.linalg.norm(sample)
            all_embs.append(sample)
            all_labels.append(cluster_idx)

    return np.array(all_embs, dtype=np.float32), np.array(all_labels, dtype=int)


def cluster_accuracy(predicted: np.ndarray, true: np.ndarray) -> float:
    """دقة التجميع مع إيجاد أفضل تطابق (Hungarian)."""
    try:
        from scipy.optimize import linear_sum_assignment
    except ImportError:
        return 0.0

    n = len(predicted)
    pred_set = sorted(set(predicted.tolist()))
    true_set = sorted(set(true.tolist()))

    cost = np.zeros((len(pred_set), len(true_set)))
    for p, t in zip(predicted, true, strict=True):
        cost[pred_set.index(p), true_set.index(t)] -= 1

    rows, cols = linear_sum_assignment(cost)
    matched = -cost[rows, cols].sum()
    return matched / n


class TestAgglomerativeCluster:
    def test_two_well_separated_clusters(self):
        embs, true_labels = make_clustered_embeddings(2, 10, noise=0.05)
        pred = agglomerative_cluster(embs, threshold=0.5)
        assert len(set(pred)) == 2
        acc = cluster_accuracy(pred, true_labels)
        assert acc > 0.95

    def test_three_clusters_specified(self):
        embs, true_labels = make_clustered_embeddings(3, 8, noise=0.05)
        pred = agglomerative_cluster(embs, n_clusters=3)
        assert len(set(pred)) == 3
        acc = cluster_accuracy(pred, true_labels)
        assert acc > 0.9

    def test_single_embedding(self):
        emb = np.array([[0.5, 0.5, 0.5, 0.5]], dtype=np.float32)
        emb /= np.linalg.norm(emb, axis=1, keepdims=True)
        pred = agglomerative_cluster(emb)
        assert len(pred) == 1
        assert pred[0] == 0

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            agglomerative_cluster(np.empty((0, 10)))

    def test_relabel_by_first_occurrence(self):
        """أول cluster يظهر يجب أن يحمل التسمية 0."""
        embs, _ = make_clustered_embeddings(2, 5, noise=0.02, seed=1)
        pred = agglomerative_cluster(embs, threshold=0.5)
        assert pred[0] == 0  # أول عيّنة → cluster 0

    def test_n_clusters_too_many(self):
        embs, _ = make_clustered_embeddings(2, 5)
        # 100 cluster على 10 نقاط → يُحدّ إلى 10
        pred = agglomerative_cluster(embs, n_clusters=100)
        assert len(set(pred)) <= 10


class TestSpectralCluster:
    def test_two_clusters_specified(self):
        embs, true_labels = make_clustered_embeddings(2, 10, noise=0.05)
        pred = spectral_cluster(embs, n_clusters=2)
        assert len(set(pred)) == 2

    def test_auto_detection_with_eigengap(self):
        """التقدير التلقائي يجب أن يجد العدد الصحيح للمجموعات الواضحة."""
        embs, _ = make_clustered_embeddings(3, 12, noise=0.03, seed=10)
        pred = spectral_cluster(embs, n_clusters=None, max_clusters=8)
        # نسمح بـ ±1 من 3 (التقدير من eigengap ليس مثالياً دائماً)
        assert 2 <= len(set(pred)) <= 4


class TestClusterEmbeddingsDispatcher:
    def test_dispatches_to_agglomerative(self):
        embs, _ = make_clustered_embeddings(2, 5)
        pred = cluster_embeddings(embs, method="agglomerative", n_clusters=2)
        assert len(set(pred)) == 2

    def test_dispatches_to_spectral(self):
        embs, _ = make_clustered_embeddings(2, 5)
        pred = cluster_embeddings(embs, method="spectral", n_clusters=2)
        assert len(set(pred)) == 2

    def test_unknown_method_raises(self):
        embs, _ = make_clustered_embeddings(2, 5)
        with pytest.raises(ValueError):
            cluster_embeddings(embs, method="kmeans")  # type: ignore


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
