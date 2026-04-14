"""
test_evaluation.py
Unit tests for retrieval evaluation metrics.
All tests are pure (no I/O, no AWS calls).
"""

import pytest

from evaluation.metrics import (
    precision_at_k,
    recall_at_k,
    mean_reciprocal_rank,
    ndcg_at_k,
    relevance_score,
)


# ── precision@k ─────────────────────────────────────────────────────────────────

def test_precision_perfect():
    assert precision_at_k(["a", "b", "c"], ["a", "b", "c"], k=3) == 1.0


def test_precision_zero():
    assert precision_at_k(["x", "y", "z"], ["a", "b"], k=3) == 0.0


def test_precision_partial():
    result = precision_at_k(["a", "x", "b"], ["a", "b"], k=3)
    assert abs(result - 2 / 3) < 1e-9


def test_precision_k_larger_than_retrieved():
    result = precision_at_k(["a", "b"], ["a", "b", "c"], k=5)
    assert result == 2 / 5


# ── recall@k ────────────────────────────────────────────────────────────────────

def test_recall_perfect():
    assert recall_at_k(["a", "b", "c"], ["a", "b"], k=3) == 1.0


def test_recall_zero():
    assert recall_at_k(["x", "y"], ["a", "b"], k=2) == 0.0


def test_recall_partial():
    result = recall_at_k(["a", "x", "y"], ["a", "b"], k=3)
    assert abs(result - 0.5) < 1e-9


def test_recall_empty_relevant():
    assert recall_at_k(["a", "b"], [], k=2) == 0.0


# ── MRR ─────────────────────────────────────────────────────────────────────────

def test_mrr_first_position():
    assert mean_reciprocal_rank(["a", "b", "c"], ["a"]) == 1.0


def test_mrr_second_position():
    assert mean_reciprocal_rank(["x", "a", "c"], ["a"]) == 0.5


def test_mrr_not_found():
    assert mean_reciprocal_rank(["x", "y", "z"], ["a"]) == 0.0


# ── NDCG@k ──────────────────────────────────────────────────────────────────────

def test_ndcg_perfect():
    assert ndcg_at_k(["a", "b"], ["a", "b"], k=2) == 1.0


def test_ndcg_zero():
    assert ndcg_at_k(["x", "y"], ["a", "b"], k=2) == 0.0


def test_ndcg_between_zero_and_one():
    result = ndcg_at_k(["x", "a", "b"], ["a", "b"], k=3)
    assert 0.0 <= result <= 1.0


# ── relevance_score ──────────────────────────────────────────────────────────────

def test_relevance_identical_vectors():
    v = [1.0, 0.0, 0.0]
    assert abs(relevance_score(v, v) - 1.0) < 1e-6


def test_relevance_orthogonal_vectors():
    assert relevance_score([1.0, 0.0], [0.0, 1.0]) == 0.0


def test_relevance_zero_vector():
    assert relevance_score([0.0, 0.0], [1.0, 2.0]) == 0.0
