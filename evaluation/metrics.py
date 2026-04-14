"""
metrics.py
Retrieval evaluation metrics: precision@k, recall@k, MRR, NDCG, relevance score.
All functions are pure — no I/O or AWS calls.
"""

import math
import numpy as np


def precision_at_k(retrieved_ids: list[str], relevant_ids: list[str], k: int) -> float:
    """
    Fraction of the top-k retrieved items that are relevant.
    precision@k = |retrieved[:k] ∩ relevant| / k
    """
    if k <= 0:
        return 0.0
    top_k = retrieved_ids[:k]
    relevant_set = set(relevant_ids)
    hits = sum(1 for rid in top_k if rid in relevant_set)
    return hits / k


def recall_at_k(retrieved_ids: list[str], relevant_ids: list[str], k: int) -> float:
    """
    Fraction of relevant items found in the top-k retrieved items.
    recall@k = |retrieved[:k] ∩ relevant| / |relevant|
    """
    if not relevant_ids:
        return 0.0
    top_k = retrieved_ids[:k]
    relevant_set = set(relevant_ids)
    hits = sum(1 for rid in top_k if rid in relevant_set)
    return hits / len(relevant_set)


def mean_reciprocal_rank(retrieved_ids: list[str], relevant_ids: list[str]) -> float:
    """
    MRR = 1 / rank_of_first_relevant_item (0.0 if none found).
    """
    relevant_set = set(relevant_ids)
    for rank, rid in enumerate(retrieved_ids, start=1):
        if rid in relevant_set:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(retrieved_ids: list[str], relevant_ids: list[str], k: int) -> float:
    """
    Normalized Discounted Cumulative Gain at k.
    Binary relevance: 1 if in relevant set, 0 otherwise.
    """
    relevant_set = set(relevant_ids)
    top_k = retrieved_ids[:k]

    dcg = sum(
        1.0 / math.log2(rank + 1)
        for rank, rid in enumerate(top_k, start=1)
        if rid in relevant_set
    )

    # Ideal DCG: all relevant docs at the top
    ideal_hits = min(len(relevant_set), k)
    idcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_hits + 1))

    return dcg / idcg if idcg > 0 else 0.0


def relevance_score(query_embedding: list[float], doc_embedding: list[float]) -> float:
    """
    Cosine similarity between a query embedding and a document embedding.
    Returns a float in [0, 1].
    """
    q = np.array(query_embedding)
    d = np.array(doc_embedding)
    denom = np.linalg.norm(q) * np.linalg.norm(d)
    if denom == 0:
        return 0.0
    return float(np.dot(q, d) / denom)
