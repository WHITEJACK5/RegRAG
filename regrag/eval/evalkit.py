
"""Retrieval metrics: Recall@k, MRR, nDCG@k, bootstrap CI.

Why these four:
- Recall@k: did the evidence reach the top-k we show the generator?
  k=6 matches the prompt budget (spec: rerank top-30 -> top-6).
- MRR: how early the FIRST correct chunk appears.
- nDCG@k: rank-weighted credit; rank 1 beats rank 5 inside the same top-k.
  Binary relevance here - a chunk either is gold or is not.
- Bootstrap CI: with 40 questions a few points are noise; resampling gives
  an interval without assuming a distribution.

Unanswerables have empty gold_chunks by design and are scored by refusal
behaviour, not recall - so every metric raises on empty gold instead of
returning 0, which would silently poison an average.
"""
from __future__ import annotations

import math
from typing import Sequence

import numpy as np


def recall_at_k(retrieved: Sequence[str], gold: Sequence[str], k: int = 6) -> float:
    """Fraction of gold chunks present in the top-k."""
    if not gold:
        raise ValueError("recall needs non-empty gold; exclude unanswerables")
    top = set(retrieved[:k])
    return sum(1 for g in gold if g in top) / len(gold)


def mrr(retrieved: Sequence[str], gold: Sequence[str]) -> float:
    """Reciprocal rank of the first gold hit; 0.0 if none."""
    if not gold:
        raise ValueError("mrr needs non-empty gold; exclude unanswerables")
    gold_set = set(gold)
    for rank, cid in enumerate(retrieved, start=1):
        if cid in gold_set:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(retrieved: Sequence[str], gold: Sequence[str], k: int = 6) -> float:
    """Binary-relevance nDCG@k, normalised by the ideal ordering."""
    if not gold:
        raise ValueError("ndcg needs non-empty gold; exclude unanswerables")
    gold_set = set(gold)
    dcg = sum(1.0 / math.log2(rank + 1)
              for rank, cid in enumerate(retrieved[:k], start=1) if cid in gold_set)
    ideal = sum(1.0 / math.log2(rank + 1)
                for rank in range(1, min(len(gold), k) + 1))
    return dcg / ideal


def bootstrap_ci(values: Sequence[float], n_boot: int = 1000,
                 alpha: float = 0.05, seed: int = 0) -> tuple[float, float]:
    """Percentile bootstrap CI for the mean; deterministic for a given seed."""
    arr = np.asarray(list(values), dtype=float)
    if arr.size == 0:
        raise ValueError("bootstrap needs at least one value")
    rng = np.random.default_rng(seed)
    means = np.array([rng.choice(arr, size=arr.size, replace=True).mean()
                      for _ in range(n_boot)])
    lo, hi = np.quantile(means, [alpha / 2, 1 - alpha / 2])
    return float(lo), float(hi)

def paired_bootstrap_diff(
    a: Sequence[float],
    b: Sequence[float],
    n_boot: int = 1000,
    alpha: float = 0.05,
    seed: int = 0,
) -> tuple[float, float]:
    """Percentile CI for mean(a - b), resampling question indices in lockstep.

    Separate intervals can overlap while the paired difference is real. The
    same resampled indices are applied to both systems, which removes the
    between-question variance that makes unpaired intervals so wide.
    """
    a_arr = np.asarray(list(a), dtype=float)
    b_arr = np.asarray(list(b), dtype=float)
    if a_arr.size != b_arr.size:
        raise ValueError("paired bootstrap needs equal-length samples")
    if a_arr.size == 0:
        raise ValueError("paired bootstrap needs at least one pair")
    diff = a_arr - b_arr
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, diff.size, size=(n_boot, diff.size))
    means = diff[idx].mean(axis=1)
    lo, hi = np.quantile(means, [alpha / 2, 1 - alpha / 2])
    return float(lo), float(hi)