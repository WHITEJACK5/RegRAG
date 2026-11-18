"""Shared corpus loader: one stable chunk order for every index.

Dense rows are addressed by FAISS row number; BM25 documents by list
position. If the two lists disagree on order, fusion compares different
chunks and every metric downstream is garbage. Both indexes load chunks
through this function only.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHUNK_DIR = ROOT / "data" / "chunks"


def load_chunks() -> list[dict]:
    """All chunks across the corpus, in stable (doc_id, chunk_id) order."""
    chunks: list[dict] = []
    for path in sorted(CHUNK_DIR.glob("*_chunks.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                chunks.append(json.loads(line))
    chunks.sort(key=lambda c: (c["doc_id"], c["chunk_id"]))
    return chunks