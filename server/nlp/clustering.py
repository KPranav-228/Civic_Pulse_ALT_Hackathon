"""Clustering and Topic Modeling module for CivicPulse.

Implements:
- KMeans clustering on TF-IDF and dense embeddings
- Latent Dirichlet Allocation (LDA) for unsupervised civic topic discovery
- Silhouette score evaluation
- Topic keyword extraction and coherence scoring
- Deduplication logic grouping reports about the same civic incident
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.metrics import pairwise_distances, silhouette_score

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from server.nlp.features import build_tfidf_vectorizer
from server.nlp.preprocess import default_preprocessor

logger = logging.getLogger(__name__)
RANDOM_SEED = 42


class CivicTopicModeler:
    """Discovers latent topics and recurring civic issues using LDA and KMeans."""

    def __init__(self, n_topics: int = 6):
        self.n_topics = n_topics
        self.vectorizer = None
        self.lda_model = None
        self.kmeans_model = None
        self.feature_names = []

    def fit_lda(self, texts: List[str]) -> Dict[str, Any]:
        """Fit Latent Dirichlet Allocation on text corpus and extract topics."""
        cleaned = [default_preprocessor.preprocess(t) for t in texts]
        self.vectorizer, X = build_tfidf_vectorizer(
            cleaned, max_features=2000, ngram_range=(1, 2)
        )
        self.feature_names = self.vectorizer.get_feature_names_out()

        self.lda_model = LatentDirichletAllocation(
            n_components=self.n_topics,
            random_state=RANDOM_SEED,
            max_iter=30,
            learning_method="batch"
        )
        self.lda_model.fit(X)

        topics = self.extract_lda_topics(top_n=10)
        coherence = self.compute_topic_diversity(topics)

        return {
            "topics": topics,
            "topic_diversity": round(coherence, 4),
            "perplexity": round(self.lda_model.perplexity(X), 2)
        }

    def extract_lda_topics(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """Extract top keywords and weights for each LDA topic."""
        topics = []
        for idx, comp in enumerate(self.lda_model.components_):
            top_indices = comp.argsort()[:-top_n - 1:-1]
            keywords = [self.feature_names[i] for i in top_indices]
            weights = [float(comp[i]) for i in top_indices]
            topics.append({
                "topic_id": idx + 1,
                "keywords": keywords,
                "weights": weights
            })
        return topics

    def fit_kmeans(
        self,
        vectors: np.ndarray,
        n_clusters: int = 6
    ) -> Dict[str, Any]:
        """Fit KMeans clustering on document vectors (TF-IDF or embeddings)."""
        self.kmeans_model = KMeans(
            n_clusters=n_clusters,
            random_state=RANDOM_SEED,
            n_init=10
        )
        labels = self.kmeans_model.fit_predict(vectors)

        # Silhouette score (requires at least 2 clusters and valid distance)
        try:
            sil_score = float(silhouette_score(vectors, labels))
        except Exception:
            sil_score = 0.0

        return {
            "labels": labels.tolist(),
            "silhouette_score": round(sil_score, 4),
            "cluster_centers": self.kmeans_model.cluster_centers_
        }

    def compute_topic_diversity(self, topics: List[Dict[str, Any]]) -> float:
        """Measure topic diversity: proportion of unique words across top keywords."""
        all_words = []
        for t in topics:
            all_words.extend(t["keywords"])
        if not all_words:
            return 0.0
        return len(set(all_words)) / len(all_words)


def find_duplicate_reports(
    texts: List[str],
    similarity_threshold: float = 0.55
) -> List[List[int]]:
    """Group duplicate/near-identical reports using TF-IDF cosine distance."""
    cleaned = [default_preprocessor.preprocess(t) for t in texts]
    if len(cleaned) < 2:
        return []

    _, X = build_tfidf_vectorizer(cleaned, max_features=3000, ngram_range=(1, 1))
    # Cosine distance = 1 - cosine similarity
    dists = pairwise_distances(X, metric="cosine")

    n = len(texts)
    visited = set()
    clusters = []

    for i in range(n):
        if i in visited:
            continue
        group = [i]
        visited.add(i)
        for j in range(i + 1, n):
            if j not in visited and dists[i, j] <= (1.0 - similarity_threshold):
                group.append(j)
                visited.add(j)
        if len(group) > 1:
            clusters.append(group)

    return clusters
