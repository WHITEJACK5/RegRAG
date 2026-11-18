"""Reciprocal Rank Fusion: combine dense and BM25 rankings without scales.

RRF uses only ranks: score(d) = sum over lists of 1/(k + rank). Dense cosine
scores and BM25 scores are not comparable (different units, different
distributions), so fusing ranks sidesteps calibration entirely. k=60 is the
Cormack et al. 2009 convention: it caps how much a single first place can
dominate and rewards agreement between lists.
"""
from __future__ import annotations

RRF_K = 60


def rrf_fuse(rankings: list[list[dict]], k: int = RRF_K, top_n: int = 6) -> list[dict]:
    """Fuse ranked lists of {chunk_id, score} into one best-first list."""
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, item in enumerate(ranking, start=1):
            cid = item["chunk_id"]
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank)
    fused = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    return [{"chunk_id": cid, "score": s} for cid, s in fused[:top_n]]