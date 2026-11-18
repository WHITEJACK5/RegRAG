"""Dense retrieval index: BGE-M3 embeddings + exact FAISS search.

Why the pieces are shaped this way:
- One embedding per chunk, L2-normalised. With normalised vectors an inner
  product EQUALS cosine similarity, so IndexFlatIP needs no metric
  bookkeeping and no score rescaling anywhere downstream.
- FAISS returns integer row numbers, not chunk ids. The row -> chunk_id
  mapping is persisted beside the index (dense_ids.json); losing it would
  lose the corpus.
- IndexFlat (exact search) on purpose: 236 vectors is tiny. Approximate
  indexes trade recall for speed we do not need - and a silent recall loss
  would poison every ablation number we produce in D10.
- The model is injectable (build_index(model=...)) so tests can run the
  whole pipeline against a deterministic fake encoder without downloading
  2 GB of weights.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parents[2]
CHUNK_DIR = ROOT / "data" / "chunks"
INDEX_DIR = ROOT / "data" / "index"
MODEL_NAME = "BAAI/bge-m3"

INDEX_FILE = INDEX_DIR / "dense.faiss"
IDS_FILE = INDEX_DIR / "dense_ids.json"
META_FILE = INDEX_DIR / "dense_meta.json"


def load_chunks() -> list[dict]:
    """All chunks across the corpus, in stable (doc_id, chunk_id) order."""
    chunks: list[dict] = []
    for path in sorted(CHUNK_DIR.glob("*_chunks.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                chunks.append(json.loads(line))
    chunks.sort(key=lambda c: (c["doc_id"], c["chunk_id"]))
    return chunks


def build_index(model: SentenceTransformer | None = None) -> dict:
    """Embed every chunk, build the FAISS index, persist index + ids + meta.

    Pass model=None (scripts) to load the real BGE-M3; tests pass a fake.
    Returns the timing/metadata dict that is also written to dense_meta.json.
    """
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    chunks = load_chunks()
    texts = [c["text"] for c in chunks]

    if model is None:
        t0 = time.perf_counter()
        model = SentenceTransformer(MODEL_NAME)
        t_load = time.perf_counter() - t0
        model_label = MODEL_NAME
    else:
        t_load = 0.0
        model_label = getattr(model, "name_or_path", "injected-model")
    t0 = time.perf_counter()
    vectors = model.encode(
        texts,
        batch_size=16,
        normalize_embeddings=True,
        show_progress_bar=True,
        convert_to_numpy=True,
    )
    t_embed = time.perf_counter() - t0

    vectors = np.ascontiguousarray(vectors.astype("float32"))
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)
    faiss.write_index(index, str(INDEX_FILE))

    ids = [c["chunk_id"] for c in chunks]
    IDS_FILE.write_text(json.dumps(ids), encoding="utf-8")
    meta = {
        "model": model_label,
        "dim": int(vectors.shape[1]),
        "num_chunks": len(chunks),
        "model_load_seconds": round(t_load, 2),
        "embed_seconds": round(t_embed, 2),
        "embed_chunks_per_second": round(len(chunks) / t_embed, 2),
    }
    META_FILE.write_text(json.dumps(meta, indent=1), encoding="utf-8")
    return meta


def load_index() -> tuple[faiss.Index, list[str]]:
    """Load the persisted index and its row -> chunk_id mapping."""
    index = faiss.read_index(str(INDEX_FILE))
    ids = json.loads(IDS_FILE.read_text(encoding="utf-8"))
    if index.ntotal != len(ids):
        raise ValueError(f"index has {index.ntotal} rows but {len(ids)} ids")
    return index, ids


def search(
    index: faiss.Index,
    ids: list[str],
    model: SentenceTransformer,
    query: str,
    k: int = 6,
) -> list[dict]:
    """Top-k as [{chunk_id, score}]; scores are cosine because vectors are normalised."""
    q = model.encode([query], normalize_embeddings=True, convert_to_numpy=True)
    q = np.ascontiguousarray(q.astype("float32"))
    scores, rows = index.search(q, k)
    return [
        {"chunk_id": ids[row], "score": float(score)}
        for score, row in zip(scores[0], rows[0])
        if row != -1
    ]