"""Cross-encoder reranking: judge query and chunk together, not separately.

A bi-encoder embeds the query and each chunk independently; similarity is a
dot product between summaries. A cross-encoder runs the concatenated
(query, chunk) pair through the transformer, so every query token can attend
to every chunk token. It orders better and costs far more: nothing can be
precomputed, so 30 candidates means 30 forward passes per query.

That cost is why this module is an experiment, not an assumption: D11
measures it on CPU and removes it if it cannot earn the latency.
"""
from __future__ import annotations

from typing import Mapping, Sequence

MODEL_NAME = "BAAI/bge-reranker-base"


def load_reranker(model_name: str = MODEL_NAME):
    """Load the cross-encoder on CPU; kept lazy so tests need no weights."""
    from sentence_transformers import CrossEncoder

    return CrossEncoder(model_name, max_length=512, device="cpu")


def rerank(
    query: str,
    candidates: Sequence[Mapping],
    texts: Mapping[str, str],
    model,
    top_n: int = 6,
    batch_size: int = 16,
) -> list[dict]:
    """Score every (query, chunk) pair and return the best `top_n`.

    `candidates` is a ranked list of {chunk_id, score} from retrieval;
    `texts` maps chunk_id to full chunk text. Raises before touching the
    model if any candidate lacks text - a silent skip would hide a broken
    id mapping and quietly shrink the pool.
    """
    if not candidates:
        return []
    missing = [c["chunk_id"] for c in candidates if c["chunk_id"] not in texts]
    if missing:
        raise KeyError(f"no text for chunk ids: {missing}")
    pairs = [(query, texts[c["chunk_id"]]) for c in candidates]
    scores = model.predict(pairs, batch_size=batch_size, show_progress_bar=False)
    ranked = sorted(
        (
            {"chunk_id": c["chunk_id"], "score": float(s)}
            for c, s in zip(candidates, scores)
        ),
        key=lambda x: (-x["score"], x["chunk_id"]),
    )
    return ranked[:top_n]