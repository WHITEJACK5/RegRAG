"""Reranker experiment: hybrid top-30 -> cross-encoder -> top-6.

The quality question and the latency question are answered by the same run.
The decision rule is pre-registered in the payload, so the artifact records
what "keep" meant before the numbers were seen. The reranker scores are raw
logits and are never fused with RRF scores; only rankings are compared.
"""
from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
from sentence_transformers import SentenceTransformer

from regrag.eval.evalkit import mrr, paired_bootstrap_diff
from regrag.eval.report import markdown, pool_ceiling, summarize
from regrag.index.corpus import load_chunks
from regrag.index.dense import MODEL_NAME as DENSE_MODEL, load_index, search as dense_search
from regrag.index.sparse import SparseIndex
from regrag.retrieve.hybrid import rrf_fuse
from regrag.retrieve.rerank import MODEL_NAME as RERANK_MODEL, load_reranker, rerank

GOLDEN = ROOT / "data" / "golden" / "golden_set_v1.jsonl"
OUT = ROOT / "data" / "eval" / "rerank_v1.json"
PARTIAL = ROOT / "data" / "eval" / "rerank_v1.partial.json"

K = 6
POOL = 30
SYSTEMS = ("hybrid", "hybrid_rerank")
MIN_MRR_GAIN = 0.03
MAX_P95_SECONDS = 1.0


def latency_stats(values: list[float]) -> dict:
    arr = np.asarray(values, dtype=float)
    total = float(arr.sum())
    return {
        "total_seconds": round(total, 2),
        "mean_seconds": round(float(arr.mean()), 3),
        "p50_seconds": round(float(np.percentile(arr, 50)), 3),
        "p95_seconds": round(float(np.percentile(arr, 95)), 3),
        "max_seconds": round(float(arr.max()), 3),
        "pairs_per_second": round(POOL * len(values) / total, 2),
    }


def main() -> int:
    lines = GOLDEN.read_text(encoding="utf-8").splitlines()
    rows = [json.loads(line) for line in lines if line.strip()]
    answerable = [r for r in rows if r["type"] != "unanswerable"]
    n = len(answerable)
    texts = {c["chunk_id"]: c["text"] for c in load_chunks()}

    print(f"loading dense model {DENSE_MODEL} ...", flush=True)
    t0 = time.perf_counter()
    dense_model = SentenceTransformer(DENSE_MODEL)
    dense_load = time.perf_counter() - t0
    index, ids = load_index()
    sparse = SparseIndex()

    print(f"loading reranker {RERANK_MODEL} on CPU ...", flush=True)
    t0 = time.perf_counter()
    reranker = load_reranker()
    rerank_load = time.perf_counter() - t0

    rankings: dict[str, dict[str, list[str]]] = {}
    pools: dict[str, list[str]] = {}
    latencies: list[float] = []
    t_start = time.perf_counter()
    print(
        f"reranking {n} queries x {POOL} pairs "
        f"(probe speed suggests ~{n * 44 / 60:.0f} min)",
        flush=True,
    )

    for i, r in enumerate(answerable, start=1):
        dense = dense_search(index, ids, dense_model, r["question"], k=POOL)
        bm25 = sparse.search(r["question"], k=POOL)
        fused = rrf_fuse([dense, bm25], top_n=POOL)
        pools[r["q_id"]] = [x["chunk_id"] for x in fused]

        t0 = time.perf_counter()
        reranked = rerank(r["question"], fused, texts, reranker, top_n=K)
        dt = time.perf_counter() - t0
        latencies.append(dt)

        rankings[r["q_id"]] = {
            "hybrid": [x["chunk_id"] for x in fused][:K],
            "hybrid_rerank": [x["chunk_id"] for x in reranked],
        }

        if i % 2 == 0 or i == n:
            elapsed = time.perf_counter() - t_start
            eta = elapsed / i * (n - i)
            print(
                f"  {i}/{n} | last {dt:.1f}s | "
                f"elapsed {elapsed / 60:.1f}m | eta {eta / 60:.1f}m",
                flush=True,
            )
        if i % 8 == 0:
            PARTIAL.write_text(
                json.dumps({"rankings": rankings, "latencies": latencies}, indent=1),
                encoding="utf-8",
            )

    results = summarize(answerable, rankings, SYSTEMS, k=K)
    ceiling = pool_ceiling(answerable, pools, depth=POOL)

    mrr_hybrid = [mrr(rankings[r["q_id"]]["hybrid"], r["gold_chunks"]) for r in answerable]
    mrr_rerank = [mrr(rankings[r["q_id"]]["hybrid_rerank"], r["gold_chunks"]) for r in answerable]
    gain = statistics.fmean(mrr_rerank) - statistics.fmean(mrr_hybrid)
    lo, hi = paired_bootstrap_diff(mrr_rerank, mrr_hybrid, n_boot=1000, seed=0)
    stats = latency_stats(latencies)
    ci_excludes_zero = lo > 0 or hi < 0
    keep = (
        gain >= MIN_MRR_GAIN
        and ci_excludes_zero
        and stats["p95_seconds"] <= MAX_P95_SECONDS
    )

    payload = {
        "k": K,
        "pool": POOL,
        "dense_model": DENSE_MODEL,
        "rerank_model": RERANK_MODEL,
        "n_total": len(rows),
        "n_answerable": n,
        "n_unanswerable": len(rows) - n,
        "pool_ceiling": ceiling,
        "dense_load_seconds": round(dense_load, 2),
        "rerank_load_seconds": round(rerank_load, 2),
        "latency": stats,
        "mrr_gain_rerank_minus_hybrid": {
            "mean": round(gain, 4),
            "lo": round(lo, 4),
            "hi": round(hi, 4),
            "n_boot": 1000,
            "seed": 0,
        },
        "decision_rule": {
            "min_mrr_gain": MIN_MRR_GAIN,
            "max_p95_seconds": MAX_P95_SECONDS,
            "ci_excludes_zero": ci_excludes_zero,
            "keep": keep,
        },
        "rip": "reranker scores are logits, not RRF scores; rankings only",
        "latency_seconds": [round(x, 3) for x in latencies],
        "rankings": rankings,
        "results": results,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    PARTIAL.unlink(missing_ok=True)

    print()
    print(markdown(results, k=K))
    print()
    print(f"pool ceiling @{POOL}: {ceiling['mean']:.3f} (n={ceiling['n']})")
    print(f"load: dense {dense_load:.1f}s | reranker {rerank_load:.1f}s")
    print(
        f"rerank: total {stats['total_seconds']:.1f}s | "
        f"mean {stats['mean_seconds']:.1f}s | p50 {stats['p50_seconds']:.1f}s | "
        f"p95 {stats['p95_seconds']:.1f}s | {stats['pairs_per_second']} pairs/s"
    )
    print(
        f"MRR gain (rerank - hybrid): {gain:+.3f} [{lo:+.3f}, {hi:+.3f}] | "
        f"p95 {stats['p95_seconds']:.1f}s | keep={keep}"
    )
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())