from typing import List, Tuple

import numpy as np


def kmeans(
    vectors: List[List[float]],
    k: int,
    max_iters: int = 100,
    seed: int = 42,
) -> Tuple[List[int], List[List[float]]]:
    if k <= 0:
        raise ValueError("k must be > 0")
    if not vectors:
        return [], []

    rng = np.random.default_rng(seed)
    data = np.array(vectors, dtype=float)
    n = data.shape[0]
    if k > n:
        k = n

    # Initialize centroids by sampling without replacement
    init_idx = rng.choice(n, size=k, replace=False)
    centroids = data[init_idx]

    for _ in range(max_iters):
        # Assign
        distances = ((data[:, None, :] - centroids[None, :, :]) ** 2).sum(axis=2)
        labels = distances.argmin(axis=1)

        # Recompute
        new_centroids = []
        for i in range(k):
            cluster_points = data[labels == i]
            if len(cluster_points) == 0:
                # Reinitialize an empty cluster to a random point
                new_centroids.append(data[rng.integers(0, n)])
            else:
                new_centroids.append(cluster_points.mean(axis=0))
        new_centroids = np.array(new_centroids, dtype=float)

        if np.allclose(new_centroids, centroids):
            break
        centroids = new_centroids

    centroids_list: List[List[float]] = centroids.tolist()  # type: ignore[assignment]
    return labels.tolist(), centroids_list
