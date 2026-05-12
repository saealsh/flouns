"""تجميع بصمات القطع إلى مجموعات (متحدثون).

نوفّر طريقتين:

1. **Agglomerative Clustering** (الأساسي):
   - يبدأ بكل قطعة كمجموعة منفصلة.
   - يدمج المجموعات الأقرب تدريجياً.
   - يتوقف عند عتبة تشابه محددة.
   - يكتشف عدد المتحدثين تلقائياً (إن لم يُحدَّد).

2. **Spectral Clustering** (متقدم):
   - يبني رسماً بيانياً من مصفوفة التشابه.
   - يستخدم القيم الذاتية (eigenvalues) لتحديد عدد المجموعات.
   - أفضل عندما تكون البصمات في فضاء معقد (نماذج عميقة).

استخدام:
    from src.diarization.clustering import cluster_embeddings

    labels = cluster_embeddings(embeddings, method="agglomerative", threshold=0.7)
    # labels[i] = معرّف المتحدث للقطعة i (0, 1, 2, ...)
"""
from __future__ import annotations

from typing import Literal

import numpy as np

from src.utils.logging import get_logger

log = get_logger(__name__)

ClusteringMethod = Literal["agglomerative", "spectral"]


def _validate_embeddings(embeddings: np.ndarray) -> None:
    if embeddings.ndim != 2:
        raise ValueError(f"الـ embeddings يجب أن يكون 2D، أعطيت {embeddings.ndim}D")
    if embeddings.size == 0:
        raise ValueError("لا يمكن التجميع على مصفوفة فارغة")


def agglomerative_cluster(
    embeddings: np.ndarray,
    *,
    n_clusters: int | None = None,
    threshold: float = 0.30,
    min_cluster_size: int = 1,
) -> np.ndarray:
    """التجميع التدرّجي الصاعد على البصمات.

    يستخدم cosine distance = 1 - cosine_similarity.

    Args:
        embeddings: شكل (N, D)، مُطبَّعة L2.
        n_clusters: إن حُدِّد، نستخدمه. إن None نكتشفه عبر العتبة.
        threshold: عتبة المسافة (cosine distance) لإيقاف الدمج.
                   البصمات المتشابهة (cosine_sim > 0.7) → distance < 0.3 → نفس المجموعة.
        min_cluster_size: أصغر مجموعة مقبولة. الأصغر منها تُدمج بأقرب جار.

    Returns:
        مصفوفة معرّفات المتحدث لكل قطعة، شكل (N,)، قيم 0..K-1.
    """
    _validate_embeddings(embeddings)

    try:
        from sklearn.cluster import AgglomerativeClustering
    except ImportError as e:
        raise ImportError("التجميع يحتاج scikit-learn") from e

    n = embeddings.shape[0]
    if n == 0:
        return np.array([], dtype=int)
    if n == 1:
        return np.array([0], dtype=int)

    # cosine distance = 1 - dot product (للبصمات المُطبَّعة)
    dist_matrix = 1.0 - (embeddings @ embeddings.T)
    np.fill_diagonal(dist_matrix, 0.0)
    # تحصين عددي: المسافة لا تكون سالبة
    dist_matrix = np.clip(dist_matrix, 0.0, 2.0)

    if n_clusters is not None:
        if n_clusters > n:
            log.warning(f"n_clusters={n_clusters} > عدد القطع {n}، نستخدم {n}")
            n_clusters = n
        clusterer = AgglomerativeClustering(
            n_clusters=n_clusters,
            metric="precomputed",
            linkage="average",
        )
    else:
        clusterer = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=threshold,
            metric="precomputed",
            linkage="average",
        )

    labels = clusterer.fit_predict(dist_matrix)

    # دمج المجموعات الصغيرة جداً بأقرب جار
    if min_cluster_size > 1:
        labels = _merge_small_clusters(labels, dist_matrix, min_cluster_size)

    # إعادة ترقيم بدءاً من 0 بترتيب الظهور (متطابق مع توقّع المستخدم)
    return _relabel_by_first_occurrence(labels)


def spectral_cluster(
    embeddings: np.ndarray,
    *,
    n_clusters: int | None = None,
    max_clusters: int = 10,
) -> np.ndarray:
    """التجميع الطيفي على رسم بياني للتشابه.

    إن لم يُحدَّد n_clusters، نستخدم eigen-gap للتقدير التلقائي.

    Args:
        embeddings: شكل (N, D)، مُطبَّعة L2.
        n_clusters: إن حُدِّد، استخدمه.
        max_clusters: حد أقصى للبحث عن عدد المتحدثين.

    Returns:
        مصفوفة المعرّفات.
    """
    _validate_embeddings(embeddings)

    try:
        from sklearn.cluster import SpectralClustering
    except ImportError as e:
        raise ImportError("Spectral clustering يحتاج scikit-learn") from e

    n = embeddings.shape[0]
    if n == 0:
        return np.array([], dtype=int)
    if n == 1:
        return np.array([0], dtype=int)

    # affinity = (1 + cos_sim) / 2 ∈ [0, 1]
    similarity = (1.0 + embeddings @ embeddings.T) / 2.0
    np.fill_diagonal(similarity, 1.0)
    similarity = np.clip(similarity, 0.0, 1.0)

    if n_clusters is None:
        n_clusters = _estimate_n_clusters_eigengap(similarity, max_clusters=min(max_clusters, n))
        log.debug(f"Spectral: عدد المجموعات المُقدَّر = {n_clusters}")

    if n_clusters > n:
        n_clusters = n
    if n_clusters < 1:
        n_clusters = 1

    if n_clusters == 1:
        return np.zeros(n, dtype=int)

    clusterer = SpectralClustering(
        n_clusters=n_clusters,
        affinity="precomputed",
        assign_labels="kmeans",
        random_state=42,
    )
    labels = clusterer.fit_predict(similarity)
    return _relabel_by_first_occurrence(labels)


def _estimate_n_clusters_eigengap(similarity: np.ndarray, max_clusters: int) -> int:
    """تقدير عدد المجموعات عبر فجوة القيم الذاتية للـ Laplacian.

    اقرأ: Von Luxburg (2007), "A tutorial on spectral clustering".
    """
    n = similarity.shape[0]
    if n < 2:
        return 1

    # Normalized Laplacian
    degrees = similarity.sum(axis=1)
    d_inv_sqrt = np.power(np.maximum(degrees, 1e-10), -0.5)
    d_mat = np.diag(d_inv_sqrt)
    laplacian = np.eye(n) - d_mat @ similarity @ d_mat
    # تحصين تناظر
    laplacian = (laplacian + laplacian.T) / 2.0

    try:
        eigenvalues = np.linalg.eigvalsh(laplacian)
    except np.linalg.LinAlgError:
        log.warning("فشل تحليل eigenvalue، نستخدم 2 مجموعات افتراضياً")
        return 2

    eigenvalues = np.sort(eigenvalues)[: max_clusters + 1]
    if len(eigenvalues) < 2:
        return 1

    # تخطّى القيمة الذاتية الأولى (دائماً ≈ 0 لـ Laplacian)
    # نبحث عن أكبر فجوة بين القيم اللاحقة
    diffs = np.diff(eigenvalues[1:]) if len(eigenvalues) > 2 else np.diff(eigenvalues)
    if len(diffs) == 0:
        return 1

    # k = موقع الفجوة + 1 (لأن k=1 يطابق eigenvalue 0)
    best_k = int(np.argmax(diffs)) + 2  # +1 لتخطّي الأولى، +1 لتحويل الـ index إلى عدد
    return max(1, min(best_k, max_clusters))


def _merge_small_clusters(
    labels: np.ndarray,
    dist_matrix: np.ndarray,
    min_size: int,
) -> np.ndarray:
    """دمج المجموعات الأصغر من min_size بأقرب جار من المجموعات الكبيرة."""
    labels = labels.copy()
    while True:
        unique, counts = np.unique(labels, return_counts=True)
        small = unique[counts < min_size]
        large = unique[counts >= min_size]
        if len(small) == 0 or len(large) == 0:
            break

        for s in small:
            members = np.where(labels == s)[0]
            best_target = None
            best_dist = float("inf")
            for l in large:
                l_members = np.where(labels == l)[0]
                # average linkage
                d = dist_matrix[np.ix_(members, l_members)].mean()
                if d < best_dist:
                    best_dist = d
                    best_target = l
            if best_target is not None:
                labels[members] = best_target
    return labels


def _relabel_by_first_occurrence(labels: np.ndarray) -> np.ndarray:
    """إعادة ترقيم: المجموعة التي تظهر أولاً → 0، الثانية → 1، إلخ.

    هذا يجعل المخرج مستقراً وقابلاً للقراءة بشريّاً.
    """
    seen: dict[int, int] = {}
    new = np.empty_like(labels)
    for i, l in enumerate(labels):
        if l not in seen:
            seen[l] = len(seen)
        new[i] = seen[l]
    return new


def cluster_embeddings(
    embeddings: np.ndarray,
    method: ClusteringMethod = "agglomerative",
    **kwargs,
) -> np.ndarray:
    """واجهة موحّدة للتجميع.

    Args:
        embeddings: شكل (N, D)، مُطبَّعة L2.
        method: "agglomerative" أو "spectral".
        **kwargs: تُمرَّر للدالة المختارة.

    Returns:
        مصفوفة المعرّفات.
    """
    if method == "agglomerative":
        return agglomerative_cluster(embeddings, **kwargs)
    elif method == "spectral":
        return spectral_cluster(embeddings, **kwargs)
    else:
        raise ValueError(f"طريقة تجميع غير معروفة: {method}")
