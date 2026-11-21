"""Aggregate per-question retrieval metrics into ablation rows.

The scorer computes rankings; this module turns them into numbers that can
be compared. It deliberately imports no FAISS and no sentence-transformers:
the aggregation rules must be testable without loading a 2 GB model.
"""
from __future__ import annotations

from typing import Mapping, Sequence

from regrag.eval.evalkit import bootstrap_ci, mrr, ndcg_at_k, recall_at_k

TYPES = ("lookup", "multihop", "numeric")


def mean_ci(values: Sequence[float], n_boot: int = 1000, seed: int = 0) -> dict:
    """Mean plus percentile bootstrap interval for one metric."""
    values = list(values)
    lo, hi = bootstrap_ci(values, n_boot=n_boot, seed=seed)
    return {"mean": sum(values) / len(values), "lo": lo, "hi": hi}


def score_rows(
    rows: Sequence[Mapping],
    rankings: Mapping[str, Mapping[str, Sequence[str]]],
    system: str,
    k: int = 6,
) -> dict:
    """Overall and per-type metrics for one system."""
    slices = {"overall": list(rows)}
    for t in TYPES:
        slices[t] = [r for r in rows if r["type"] == t]
    out = {}
    for name, sub in slices.items():
        if not sub:
            continue
        out[name] = {
            "n": len(sub),
            "recall": mean_ci([
                recall_at_k(rankings[r["q_id"]][system], r["gold_chunks"], k)
                for r in sub
            ]),
            "mrr": mean_ci([
                mrr(rankings[r["q_id"]][system], r["gold_chunks"])
                for r in sub
            ]),
            "ndcg": mean_ci([
                ndcg_at_k(rankings[r["q_id"]][system], r["gold_chunks"], k)
                for r in sub
            ]),
        }
    return out


def summarize(
    rows: Sequence[Mapping],
    rankings: Mapping[str, Mapping[str, Sequence[str]]],
    systems: Sequence[str],
    k: int = 6,
) -> dict:
    """One results dict per system, keyed by slice."""


    return {s: score_rows(rows, rankings, s, k) for s in systems}


def pool_ceiling(
    rows: Sequence[Mapping],
    pools: Mapping[str, Sequence[str]],
    depth: int = 30,
) -> dict:
    """Mean fraction of gold chunks present in the candidate pool.

    This is the upper bound on any reranker's Recall@k: it can only reorder
    what retrieval already supplied. If the ceiling is 1.0, reranking can
    improve MRR and nDCG but cannot improve recall.
    """
    values = [
        recall_at_k(pools[r["q_id"]], r["gold_chunks"], depth)
        for r in rows
    ]
    return {"mean": sum(values) / len(values), "n": len(values)}


def _cell(metric: dict) -> str:
    return f"{metric['mean']:.3f} [{metric['lo']:.3f}, {metric['hi']:.3f}]"


def markdown(results: Mapping[str, Mapping[str, dict]], k: int = 6) -> str:


    
    """A table whose rows are (slice, system) pairs - readable in a PR."""
    lines = [
        f"| slice | system | n | Recall@{k} | MRR | nDCG@{k} |",
        "|---|---|---|---|---|---|",
    ]
    for name in ("overall", *TYPES):
        for system, by_type in results.items():
            if name not in by_type:
                continue
            b = by_type[name]
            lines.append(
                f"| {name} | {system} | {b['n']} | {_cell(b['recall'])} | "
                f"{_cell(b['mrr'])} | {_cell(b['ndcg'])} |"
            )
    return "\n".join(lines)