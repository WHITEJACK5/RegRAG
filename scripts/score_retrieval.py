"""Score dense, BM25 and RRF-hybrid retrieval on the answerable golden set."""
from __future__ import annotations

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sentence_transformers import SentenceTransformer
from regrag.eval.report import markdown, summarize
from regrag.index.dense import MODEL_NAME, load_index, search as dense_search
from regrag.index.sparse import SparseIndex
from regrag.retrieve.hybrid import rrf_fuse

ROOT = Path(__file__).resolve().parent.parent
GOLDEN = ROOT / "data" / "golden" / "golden_set_v1.jsonl"
OUT = ROOT / "data" / "eval" / "retrieval_v1.json"

K = 6
POOL = 30
SYSTEMS = ("dense", "bm25", "hybrid")


def main() -> int:
    lines = GOLDEN.read_text(encoding="utf-8").splitlines()
    rows = [json.loads(l) for l in lines if l.strip()]
    answerable = [r for r in rows if r["type"] != "unanswerable"]

    t0 = time.perf_counter()
    model = SentenceTransformer(MODEL_NAME)
    t_load = time.perf_counter() - t0

    index, ids = load_index()
    sparse = SparseIndex()

    rankings = {}
    t0 = time.perf_counter()
    for r in answerable:
        dense = dense_search(index, ids, model, r["question"], k=POOL)
        bm25 = sparse.search(r["question"], k=POOL)
        rankings[r["q_id"]] = {
            "dense": [x["chunk_id"] for x in dense][:K],
            "bm25": [x["chunk_id"] for x in bm25][:K],
            "hybrid": [x["chunk_id"] for x in rrf_fuse([dense, bm25], top_n=K)],
        }
    t_queries = time.perf_counter() - t0

    results = summarize(answerable, rankings, SYSTEMS, k=K)
    payload = {
        "k": K,
        "pool": POOL,
        "model": MODEL_NAME,
        "n_total": len(rows),
        "n_answerable": len(answerable),
        "n_unanswerable": len(rows) - len(answerable),
        "unanswerables": "scored by refusal, not recall",
        "model_load_seconds": round(t_load, 2),
        "query_seconds": round(t_queries, 2),
        "results": results,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=1), encoding="utf-8")

    print(markdown(results, k=K))
    print()
    print(f"model load {t_load:.1f}s | {len(answerable)} queries {t_queries:.1f}s")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())