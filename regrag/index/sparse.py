"""BM25 sparse index over the same chunks, addressed by the same ids.

BM25 is a bag-of-terms model: it never sees meaning, only tokens. The
tokenizer is therefore the model's entire interface to the corpus, and for
regulatory text its critical job is keeping identifiers whole ("2.1.2",
"21.04.158", "2025-05-08"). Splitting on dots would turn a section number
into tokens that appear on every page and discriminate nothing.
"""
from __future__ import annotations

import re

from rank_bm25 import BM25Okapi

from regrag.index.corpus import load_chunks

TOKEN_RE = re.compile(r"[a-z0-9]+(?:[.\-/][a-z0-9]+)*")


def tokenize(text: str) -> list[str]:
    """Lowercase word tokens; dotted/slashed/dashed identifiers stay whole."""
    return TOKEN_RE.findall(text.lower())


class SparseIndex:
    """In-memory BM25 over the same chunk list (and order) as the dense index."""

    def __init__(self, chunks: list[dict] | None = None):
        self.chunks = chunks if chunks is not None else load_chunks()
        self.ids = [c["chunk_id"] for c in self.chunks]
        self._bm25 = BM25Okapi([tokenize(c["text"]) for c in self.chunks])

    def search(self, query: str, k: int = 30) -> list[dict]:
        """Top-k as [{chunk_id, score}], best first; ties keep corpus order."""
        scores = self._bm25.get_scores(tokenize(query))
        order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        return [{"chunk_id": self.ids[i], "score": float(scores[i])} for i in order]