"""Metric definitions pinned by hand-computed cases."""
import math

import pytest

from regrag.eval import evalkit


def test_recall_full_partial_none():
    assert evalkit.recall_at_k(["a", "b", "c"], ["a"], k=2) == 1.0
    assert evalkit.recall_at_k(["x", "a"], ["a", "b"], k=2) == 0.5
    assert evalkit.recall_at_k(["x", "y"], ["a"], k=6) == 0.0


def test_recall_respects_k_cutoff():
    assert evalkit.recall_at_k(["x", "y", "a"], ["a"], k=2) == 0.0


def test_recall_rejects_empty_gold():
    with pytest.raises(ValueError):
        evalkit.recall_at_k(["a"], [])


def test_mrr_first_hit_positions():
    assert evalkit.mrr(["a", "b"], ["a"]) == 1.0
    assert evalkit.mrr(["x", "y", "a"], ["a"]) == pytest.approx(1 / 3)
    assert evalkit.mrr(["x"], ["a"]) == 0.0


def test_ndcg_perfect_and_rank_penalty():
    assert evalkit.ndcg_at_k(["a", "b"], ["a", "b"], k=6) == pytest.approx(1.0)
    assert evalkit.ndcg_at_k(["b", "a"], ["a"], k=6) == pytest.approx(1 / math.log2(3))


def test_ndcg_rejects_empty_gold():
    with pytest.raises(ValueError):
        evalkit.ndcg_at_k(["a"], [])


def test_bootstrap_ci_brackets_mean_and_is_deterministic():
    vals = [0.0, 0.5, 1.0, 1.0, 0.5]
    lo, hi = evalkit.bootstrap_ci(vals, n_boot=500, seed=7)
    assert lo <= sum(vals) / len(vals) <= hi
    assert (lo, hi) == evalkit.bootstrap_ci(vals, n_boot=500, seed=7)


def test_bootstrap_single_value():
    assert evalkit.bootstrap_ci([0.42], n_boot=50) == (0.42, 0.42)


def test_bootstrap_rejects_empty():
    with pytest.raises(ValueError):
        evalkit.bootstrap_ci([])


def test_paired_bootstrap_detects_a_consistent_gain():
    lo, hi = evalkit.paired_bootstrap_diff([1.0] * 10, [0.0] * 10, n_boot=500, seed=7)
    assert (lo, hi) == (1.0, 1.0)
    assert (lo, hi) == evalkit.paired_bootstrap_diff(
        [1.0] * 10, [0.0] * 10, n_boot=500, seed=7
    )


def test_paired_bootstrap_null_includes_zero():
    a = [1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0]
    b = [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0]
    lo, hi = evalkit.paired_bootstrap_diff(a, b, n_boot=1000, seed=0)
    assert lo <= 0.0 <= hi


def test_paired_bootstrap_rejects_mismatch_and_empty():
    with pytest.raises(ValueError):
        evalkit.paired_bootstrap_diff([1.0], [1.0, 0.0])
    with pytest.raises(ValueError):
        evalkit.paired_bootstrap_diff([], [])